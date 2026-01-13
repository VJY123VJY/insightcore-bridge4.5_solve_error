"""
Enforcement decision engine.
CRITICAL: Never trust JWT payload for scores - always use TrustedScoreProvider.
"""

from app.models import Decision, DenyReason
from app.core.score_provider import TrustedScoreProvider


class DecisionEngine:
    """Makes ALLOW/DENY/MONITOR decisions based on trusted data."""
    
    # Score thresholds
    ALLOW_THRESHOLD = 70
    MONITOR_THRESHOLD = 50
    
    def __init__(self, score_provider: TrustedScoreProvider):
        self.score_provider = score_provider
    
    async def make_decision(self, user_id: str) -> tuple[Decision, int]:
        """
        Make enforcement decision based on trusted score.
        
        Returns:
            (Decision, score)
        """
        # Get TRUSTED score (NOT from JWT)
        score = await self.score_provider.get_score(user_id)
        
        # Make decision
        if score >= self.ALLOW_THRESHOLD:
            return Decision.ALLOW, score
        elif score >= self.MONITOR_THRESHOLD:
            return Decision.MONITOR, score
        else:
            return Decision.DENY, score
    
    def should_enforce_deny(self, decision: Decision) -> bool:
        """Determine if DENY should be enforced (vs logged only)."""
        # In production, DENY and MONITOR both allow through but log
        # In strict mode, DENY blocks
        # For v4.0, we enforce DENY
        return decision == Decision.DENY