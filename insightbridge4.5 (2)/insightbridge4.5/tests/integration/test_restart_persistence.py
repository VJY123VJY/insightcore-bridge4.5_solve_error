"""
Integration tests for restart persistence.
"""

import pytest
import time
from app.persistence.repositories import ReplayRepository
from app.core.replay_cache import ReplayCache


@pytest.mark.asyncio
class TestRestartPersistence:
    """Test that state survives restarts."""
    
    async def test_replay_cache_survives_restart(self, test_db):
        """Test that replay cache persists across sessions."""
        jti = "persistent-jti"
        exp = int(time.time()) + 3600
        
        # Session 1: Mark as seen
        repo1 = ReplayRepository(test_db)
        cache1 = ReplayCache(repo1)
        await cache1.mark_seen(jti, exp)
        
        # Simulate restart by creating new instances
        repo2 = ReplayRepository(test_db)
        cache2 = ReplayCache(repo2)
        
        # Should still be detected as replay
        is_replay = await cache2.is_replay(jti)
        assert is_replay is True
    
    async def test_purged_entries_stay_purged(self, test_db):
        """Test that purged entries don't reappear after restart."""
        jti = "expired-jti"
        exp = int(time.time()) - 3600  # Already expired
        
        # Add and purge
        repo1 = ReplayRepository(test_db)
        cache1 = ReplayCache(repo1)
        await cache1.mark_seen(jti, exp)
        await cache1.purge_expired()
        
        # Simulate restart
        repo2 = ReplayRepository(test_db)
        cache2 = ReplayCache(repo2)
        
        # Should not be in cache
        is_replay = await cache2.is_replay(jti)
        assert is_replay is False