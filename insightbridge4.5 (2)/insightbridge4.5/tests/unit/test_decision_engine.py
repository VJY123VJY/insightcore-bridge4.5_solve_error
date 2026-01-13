"""
Unit tests for decision engine.
"""

import pytest
from unittest.mock import AsyncMock
from app.core.decision_engine import DecisionEngine
from app.models import Decision


@pytest.mark.asyncio
class TestDecisionEngine:
    """Test enforcement decision logic."""
    
    async def test_high_score_allows(self):
        """Test that high score (>=70) results in ALLOW."""
        mock_provider = AsyncMock()
        mock_provider.get_score.return_value = 80
        
        engine = DecisionEngine(mock_provider)
        decision, score = await engine.make_decision("user123")
        
        assert decision == Decision.ALLOW
        assert score == 80
    
    async def test_medium_score_monitors(self):
        """Test that medium score (50-69) results in MONITOR."""
        mock_provider = AsyncMock()
        mock_provider.get_score.return_value = 60
        
        engine = DecisionEngine(mock_provider)
        decision, score = await engine.make_decision("user123")
        
        assert decision == Decision.MONITOR
        assert score == 60
    
    async def test_low_score_denies(self):
        """Test that low score (<50) results in DENY."""
        mock_provider = AsyncMock()
        mock_provider.get_score.return_value = 30
        
        engine = DecisionEngine(mock_provider)
        decision, score = await engine.make_decision("user123")
        
        assert decision == Decision.DENY
        assert score == 30
    
    async def test_zero_score_denies(self):
        """Test that zero score (error case) results in DENY."""
        mock_provider = AsyncMock()
        mock_provider.get_score.return_value = 0
        
        engine = DecisionEngine(mock_provider)
        decision, score = await engine.make_decision("user123")
        
        assert decision == Decision.DENY
        assert score == 0
    
    def test_score_thresholds(self):
        """Test threshold values are correct."""
        assert DecisionEngine.ALLOW_THRESHOLD == 70
        assert DecisionEngine.MONITOR_THRESHOLD == 50