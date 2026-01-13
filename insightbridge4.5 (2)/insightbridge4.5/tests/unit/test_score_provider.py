"""
Unit tests for trusted score provider.
"""

import pytest
from app.core.score_provider import TrustedScoreProvider
from app.persistence.repositories import ScoreRepository
from app.persistence.database import Base
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestScoreProvider:
    """Test trusted score retrieval."""
    
    async def test_get_score_from_database(self, test_db):
        """Test retrieving score from database."""
        repo = ScoreRepository(test_db)
        provider = TrustedScoreProvider(repo)
        
        # For now, test fail-closed behavior
        score = await provider.get_score("unknown-user")
        assert score == 0  # Unknown user gets 0 (fail-closed)
    
    async def test_fail_closed_on_error(self, test_db):
        """Test that errors result in score of 0."""
        provider = TrustedScoreProvider(None)  # Invalid repo
        
        score = await provider.get_score("test-user")
        assert score == 0  # Should return 0 on error
    
    def test_user_id_hashing(self):
        """Test that user IDs are hashed for privacy."""
        user_id = "sensitive-user-123"
        hash1 = TrustedScoreProvider.hash_user_id(user_id)
        hash2 = TrustedScoreProvider.hash_user_id(user_id)
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Hash should be 64 chars (SHA256 hex)
        assert len(hash1) == 64
        
        # Hash should not contain original user_id
        assert user_id not in hash1