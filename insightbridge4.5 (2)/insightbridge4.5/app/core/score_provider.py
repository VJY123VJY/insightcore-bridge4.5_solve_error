"""
Trusted score provider - NEVER trust JWT payload scores.
Supports multiple backends: database, Redis cache, external API.
"""

import hashlib
import httpx
from typing import Optional
from app.persistence.repositories import ScoreRepository


class TrustedScoreProvider:
    """Provides trusted scores from receiver-controlled sources."""
    
    def __init__(self, score_repo: ScoreRepository, settings=None):
        self.settings = settings
        self.score_repo = score_repo
        self.provider_type = settings.score_provider_type if settings else "database"
    
    async def get_score(self, user_id: str) -> int:
        """
        Get trusted score for user.
        Fail-closed: Return 0 (deny) on error.
        """
        try:
            if self.provider_type == "database":
                return await self._get_from_database(user_id)
            elif self.provider_type == "redis":
                return await self._get_from_redis(user_id)
            elif self.provider_type == "external_api":
                return await self._get_from_api(user_id)
            else:
                # Invalid provider type - fail closed
                return 0
        except Exception as e:
            # Fail-closed: Return 0 on any error
            return 0
    
    async def _get_from_database(self, user_id: str) -> int:
        """Fetch score from database."""
        score = await self.score_repo.get_score(user_id)
        return score if score is not None else 0
    
    async def _get_from_redis(self, user_id: str) -> int:
        """Fetch score from Redis cache with DB fallback."""
        # Try cache first
        cached_score = await self.score_repo.get_cached_score(user_id)
        if cached_score is not None:
            return cached_score
        
        # Fallback to database
        score = await self.score_repo.get_score(user_id)
        if score is not None:
            # Update cache
            ttl = self.settings.score_cache_ttl_seconds if self.settings else 300
            await self.score_repo.cache_score(user_id, score, ttl)
            return score
        
        return 0
    
    async def _get_from_api(self, user_id: str) -> int:
        """Fetch score from external API."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{self.settings.score_api_url}/users/{user_id}/score",
                    headers={"Authorization": f"Bearer {self.settings.score_api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("score", 0)
        except Exception:
            # API failure - fail closed
            return 0
    
    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """Hash user ID for telemetry (privacy protection)."""
        return hashlib.sha256(user_id.encode()).hexdigest()