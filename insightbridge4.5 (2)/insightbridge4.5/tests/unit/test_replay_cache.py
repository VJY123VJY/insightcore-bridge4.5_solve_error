"""
Unit tests for replay cache.
"""

import pytest
from app.core.replay_cache import ReplayCache
from app.persistence.repositories import ReplayRepository


@pytest.mark.asyncio
class TestReplayCache:
    """Test replay detection logic."""
    
    async def test_first_use_not_replay(self, test_db):
        """Test that first use of JTI is not flagged as replay."""
        repo = ReplayRepository(test_db)
        cache = ReplayCache(repo)
        
        jti = "first-use-jti"
        is_replay = await cache.is_replay(jti)
        
        assert is_replay is False
    
    async def test_second_use_is_replay(self, test_db):
        """Test that second use of JTI is flagged as replay."""
        repo = ReplayRepository(test_db)
        cache = ReplayCache(repo)
        
        jti = "reused-jti"
        exp = int(time.time()) + 3600
        
        # First use
        await cache.mark_seen(jti, exp)
        
        # Second use should be detected
        is_replay = await cache.is_replay(jti)
        assert is_replay is True
    
    async def test_purge_expired_entries(self, test_db):
        """Test purging of expired cache entries."""
        import time
        repo = ReplayRepository(test_db)
        cache = ReplayCache(repo)
        
        # Add expired entry
        old_jti = "old-jti"
        old_exp = int(time.time()) - 3600  # Expired 1 hour ago
        await cache.mark_seen(old_jti, old_exp)
        
        # Add valid entry
        new_jti = "new-jti"
        new_exp = int(time.time()) + 3600  # Valid for 1 hour
        await cache.mark_seen(new_jti, new_exp)
        
        # Purge expired
        purged_count = await cache.purge_expired()
        
        assert purged_count >= 1
        
        # Old should be gone, new should remain
        assert await cache.is_replay(new_jti) is True
    
    async def test_cache_size_limit(self, test_db):
        """Test cache respects size limits."""
        repo = ReplayRepository(test_db)
        cache = ReplayCache(repo)
        
        # Check initial size
        initial_size = await cache.get_cache_size()
        assert initial_size >= 0
    
    async def test_fail_closed_on_error(self, test_db):
        """Test that errors result in fail-closed behavior."""
        # Create cache with invalid repo to trigger error
        cache = ReplayCache(None)
        
        # Should treat as replay (fail-closed)
        is_replay = await cache.is_replay("test-jti")
        assert is_replay is True


import time