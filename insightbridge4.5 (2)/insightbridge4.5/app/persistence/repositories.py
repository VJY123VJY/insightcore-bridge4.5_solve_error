"""
Data access layer - Stub implementations for demo
"""

from typing import Optional


class ScoreRepository:
    """Mock score repository."""
    
    async def get_score(self, user_id: str) -> Optional[int]:
        """Get user score"""
        # Mock scores for testing
        if user_id.startswith("high"):
            return 95
        elif user_id.startswith("med"):
            return 50
        else:
            return 5
    
    async def get_cached_score(self, user_id: str) -> Optional[int]:
        """Get cached score"""
        return None
    
    async def cache_score(self, user_id: str, score: int, ttl: int):
        """Cache score"""
        pass


class RateLimitRepository:
    """Mock rate limit repository."""
    
    async def get_state(self, user_id: str) -> Optional[tuple]:
        """Get rate limit state"""
        return None
    
    async def set_state(self, user_id: str, tokens: float, last_update: float):
        """Set rate limit state"""
        pass


class ReplayRepository:
    """Mock replay repository."""
    
    async def is_seen(self, jti: str) -> bool:
        """Check if JTI seen before"""
        return False
    
    async def mark_seen(self, jti: str, exp: int):
        """Mark JTI as seen"""
        pass
    
    async def get_cache_size(self) -> int:
        """Get cache size"""
        return 0
    
    async def purge_expired(self) -> int:
        """Purge expired entries"""
        return 0
        self.db = db
        self.redis = redis_client
    
    async def get_score(self, user_id: str) -> Optional[int]:
        """Get user score from database."""
        result = await self.db.execute(
            select(UserScoreModel).where(UserScoreModel.user_id == user_id)
        )
        score_model = result.scalar_one_or_none()
        return score_model.score if score_model else None
    
    async def get_cached_score(self, user_id: str) -> Optional[int]:
        """Get user score from Redis cache."""
        if not self.redis:
            return None
        try:
            cached = await self.redis.get(f"score:{user_id}")
            return int(cached) if cached else None
        except Exception:
            return None
    
    async def cache_score(self, user_id: str, score: int, ttl: int):
        """Cache user score in Redis."""
        if not self.redis:
            return
        try:
            await self.redis.setex(f"score:{user_id}", ttl, score)
        except Exception:
            pass  # Cache failure is non-critical