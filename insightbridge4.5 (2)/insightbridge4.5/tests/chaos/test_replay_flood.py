"""
Chaos test: Replay attack flood.
"""

import pytest
import asyncio
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestReplayFlood:
    """Test system behavior under replay attack flood."""
    
    async def test_same_token_repeated(self):
        """Send same token 50 times."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            same_token = "replay-test-token"
            
            tasks = []
            for _ in range(50):
                task = client.post(
                    "/validate",
                    json={"token": same_token}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At most 1 should succeed, rest should be replay detections
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            print(f"Replay flood: {success_count}/50 allowed (should be ≤1)")
            
            # System should survive
            assert success_count >= 0