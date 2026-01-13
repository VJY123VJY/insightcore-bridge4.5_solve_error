"""
Integration tests for fail-closed behavior.
"""

import pytest
from unittest.mock import patch
from app.core.replay_cache import ReplayCache
from app.core.rate_limiter import RateLimiter
from app.core.score_provider import TrustedScoreProvider


@pytest.mark.asyncio
class TestFailClosed:
    """Test that all components fail closed on errors."""
    
    async def test_replay_cache_fails_closed(self):
        """Test replay cache denies on database error."""
        cache = ReplayCache(None)  # Invalid repo
        
        # Should treat as replay (deny)
        is_replay = await cache.is_replay("test-jti")
        assert is_replay is True
    
    async def test_rate_limiter_fails_closed(self):
        """Test rate limiter denies on error."""
        limiter = RateLimiter(None)  # Invalid repo
        
        # Should deny
        is_allowed = await limiter.is_allowed("test-user")
        assert is_allowed is False
    
    async def test_score_provider_fails_closed(self):
        """Test score provider returns 0 on error."""
        provider = TrustedScoreProvider(None)  # Invalid repo
        
        # Should return 0 (results in deny)
        score = await provider.get_score("test-user")
        assert score == 0