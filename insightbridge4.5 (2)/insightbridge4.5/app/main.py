"""
InsightBridge v4.5 - Main FastAPI Application
JWT validation gateway with score-based enforcement decisions
"""

import time
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import jwt
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import (
    Decision, DenyReason, ValidateRequest, ValidateResponse, 
    TelemetryEvent, DecisionEvent, ErrorEvent, HealthResponse, MetricsResponse
)
from app.core.decision_engine import DecisionEngine
from app.core.jwt_validator import JWTValidator
from app.core.rate_limiter import RateLimiter
from app.core.replay_cache import ReplayCache
from app.core.score_provider import TrustedScoreProvider
from app.telemetry.logger import TelemetryLogger

# ============================================================================
# Global State
# ============================================================================

settings = get_settings()
jwt_validator = None
decision_engine = None
rate_limiter = None
replay_cache = None
telemetry_logger = None
score_provider = None

# Metrics
metrics = {
    "total_requests": 0,
    "allow_count": 0,
    "deny_count": 0,
    "monitor_count": 0,
    "start_time": time.time(),
    "total_latency_ms": 0,
    "rate_limit_hits": 0,
    "replay_detections": 0,
    "active_users": 0,
}


# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global jwt_validator, decision_engine, rate_limiter, replay_cache, telemetry_logger, score_provider
    
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"   Environment: {settings.environment}")
    print(f"   JWT Algorithm: {settings.jwt_algorithm}")
    
    # Initialize components
    jwt_validator = JWTValidator(settings)
    rate_limiter = RateLimiter(settings.rate_limit_requests_per_minute)
    replay_cache = ReplayCache()
    telemetry_logger = TelemetryLogger(settings)
    
    # Initialize score provider (mock for now)
    class MockScoreRepository:
        async def get_score(self, user_id: str) -> int:
            """Return mock scores for testing"""
            # Scores > 9 should ALLOW, <= 9 should DENY
            if user_id.startswith("high"):
                return 95
            elif user_id.startswith("med"):
                return 50
            else:
                return 5
        
        async def get_cached_score(self, user_id: str) -> Optional[int]:
            return None
        
        async def cache_score(self, user_id: str, score: int, ttl: int):
            pass
    
    score_provider = TrustedScoreProvider(MockScoreRepository(), settings)
    decision_engine = DecisionEngine(score_provider)
    
    print("✅ Components initialized")
    
    yield
    
    print("🛑 Shutting down...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    description="JWT validation gateway with score-based enforcement",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_request_id(request: Request) -> str:
    """Extract or generate request ID."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


# ============================================================================
# Core Endpoints
# ============================================================================

@app.post("/validate", response_model=ValidateResponse)
async def validate_token(
    request: ValidateRequest,
    request_id: str = Depends(get_request_id),
):
    """
    Validate JWT and make enforcement decision.
    
    Score Thresholds:
    - Score >= 70: ALLOW
    - Score 50-69: MONITOR
    - Score < 50: DENY
    """
    metrics["total_requests"] += 1
    timestamp = datetime.utcnow()
    
    try:
        # 1. Rate limiting check
        if not rate_limiter.is_allowed():
            metrics["deny_count"] += 1
            return ValidateResponse(
                decision=Decision.DENY,
                reason=DenyReason.RATE_LIMIT_EXCEEDED,
                request_id=request_id,
                timestamp=timestamp,
                score=None,
            )
        
        # 2. Parse and validate JWT
        decoded = jwt_validator.validate_token(request.token)
        if isinstance(decoded, dict) and "error" in decoded:
            reason_map = {
                "expired": DenyReason.EXPIRED_TOKEN,
                "not_yet_valid": DenyReason.NOT_YET_VALID,
                "invalid_signature": DenyReason.INVALID_SIGNATURE,
                "malformed": DenyReason.MALFORMED_TOKEN,
            }
            reason = reason_map.get(decoded["error"], DenyReason.INTERNAL_ERROR)
            metrics["deny_count"] += 1
            return ValidateResponse(
                decision=Decision.DENY,
                reason=reason,
                request_id=request_id,
                timestamp=timestamp,
                score=None,
            )
        
        user_id = decoded.get("sub")
        jti = decoded.get("jti")
        
        # 3. Replay attack detection
        if replay_cache.is_replayed(jti):
            metrics["deny_count"] += 1
            return ValidateResponse(
                decision=Decision.DENY,
                reason=DenyReason.REPLAY_DETECTED,
                request_id=request_id,
                timestamp=timestamp,
                score=None,
            )
        
        replay_cache.record(jti)
        
        # 4. Get trusted score and make decision
        decision, score = await decision_engine.make_decision(user_id)
        
        # 5. Update metrics
        if decision == Decision.ALLOW:
            metrics["allow_count"] += 1
        elif decision == Decision.DENY:
            metrics["deny_count"] += 1
        else:
            metrics["monitor_count"] += 1
        
        # 6. Log telemetry
        if settings.telemetry_emit_enabled:
            event = DecisionEvent(
                decision=decision,
                reason=DenyReason.LOW_SCORE if decision == Decision.DENY else None,
                score=score,
                user_id_hash=TrustedScoreProvider.hash_user_id(user_id),
                request_id=request_id,
                timestamp=timestamp,
                latency_ms=int((time.time() - timestamp.timestamp()) * 1000),
            )
            await telemetry_logger.emit(event)
        
        return ValidateResponse(
            decision=decision,
            reason=DenyReason.LOW_SCORE if decision == Decision.DENY else None,
            request_id=request_id,
            timestamp=timestamp,
            score=score,
        )
    
    except Exception as e:
        metrics["deny_count"] += 1
        error_event = ErrorEvent(
            error_type=type(e).__name__,
            error_message=str(e),
            request_id=request_id,
            timestamp=timestamp,
        )
        if settings.telemetry_emit_enabled:
            await telemetry_logger.emit(error_event)
        
        return ValidateResponse(
            decision=Decision.DENY,
            reason=DenyReason.INTERNAL_ERROR,
            request_id=request_id,
            timestamp=timestamp,
            score=None,
        )


# ============================================================================
# Health & Monitoring
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        uptime_seconds=int(time.time() - metrics["start_time"]),
        database_connected=True,  # Mock
        redis_connected=True,     # Mock
        replay_cache_size=replay_cache.size() if replay_cache else 0,
        timestamp=datetime.utcnow(),
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get metrics summary."""
    total = metrics["total_requests"] or 1
    return MetricsResponse(
        total_requests=metrics["total_requests"],
        allow_count=metrics["allow_count"],
        deny_count=metrics["deny_count"],
        monitor_count=metrics["monitor_count"],
        avg_latency_ms=metrics.get("total_latency_ms", 0) / total,
        rate_limit_hits=metrics.get("rate_limit_hits", 0),
        replay_detections=metrics.get("replay_detections", 0),
        active_users=metrics.get("active_users", 0),
    )


@app.get("/status")
async def status():
    """Application status."""
    return {
        "status": "running",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": int(time.time() - metrics["start_time"]),
        "metrics": {
            "total_requests": metrics["total_requests"],
            "allow": metrics["allow_count"],
            "deny": metrics["deny_count"],
            "monitor": metrics["monitor_count"],
        }
    }


# ============================================================================
# Root & Info
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "validate": "POST /validate",
            "health": "GET /health",
            "metrics": "GET /metrics",
            "status": "GET /status",
        }
    }


@app.get("/docs/info")
async def api_info():
    """API information and usage guide."""
    return {
        "title": settings.app_name,
        "version": settings.app_version,
        "description": "JWT validation gateway with score-based enforcement decisions",
        "features": [
            "JWT token validation (RS256)",
            "Rate limiting",
            "Replay attack detection",
            "Score-based decision engine",
            "Telemetry and metrics",
        ],
        "endpoints": {
            "POST /validate": {
                "description": "Validate JWT and get enforcement decision",
                "request": {"token": "JWT token string"},
                "response": {
                    "decision": "ALLOW | DENY | MONITOR",
                    "reason": "Optional denial reason",
                    "score": "Trust score (0-100)",
                    "timestamp": "ISO 8601",
                }
            },
            "GET /health": "Health check",
            "GET /metrics": "Metrics summary",
            "GET /status": "Application status",
        },
        "authentication": "JWT token in POST body",
        "score_thresholds": {
            "ALLOW": "score >= 70",
            "MONITOR": "score >= 50 and score < 70",
            "DENY": "score < 50",
        }
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    print(f"❌ Error [{request_id}]: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.is_development(),
    )
