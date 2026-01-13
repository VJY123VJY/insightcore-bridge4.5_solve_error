"""
Pydantic models for requests, responses, and telemetry.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Decision(str, Enum):
    """Enforcement decision types."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    MONITOR = "MONITOR"


class DenyReason(str, Enum):
    """Reasons for denial."""
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    NOT_YET_VALID = "NOT_YET_VALID"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    LOW_SCORE = "LOW_SCORE"
    MALFORMED_TOKEN = "MALFORMED_TOKEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ValidateRequest(BaseModel):
    """Request to validate a JWT."""
    token: str = Field(..., description="JWT token to validate")


class ValidateResponse(BaseModel):
    """Response from validation."""
    decision: Decision
    reason: Optional[DenyReason] = None
    request_id: str
    timestamp: datetime
    score: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TelemetryEvent(BaseModel):
    """Base telemetry event."""
    version: str = Field(default="1.0.0")
    event_type: str
    request_id: str
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DecisionEvent(TelemetryEvent):
    """Decision telemetry event."""
    event_type: str = Field(default="gateway.decision.made")
    decision: Decision
    reason: Optional[DenyReason] = None
    score: Optional[int] = None
    user_id_hash: Optional[str] = None
    latency_ms: int


class ErrorEvent(TelemetryEvent):
    """Error telemetry event."""
    event_type: str = Field(default="gateway.error")
    error_type: str
    error_message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: int
    database_connected: bool
    redis_connected: bool
    replay_cache_size: int
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsResponse(BaseModel):
    """Metrics summary response."""
    total_requests: int
    allow_count: int
    deny_count: int
    monitor_count: int
    avg_latency_ms: float
    rate_limit_hits: int
    replay_detections: int
    active_users: int