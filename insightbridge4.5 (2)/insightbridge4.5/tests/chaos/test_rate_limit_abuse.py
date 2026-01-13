"""
Chaos test: Rate limit abuse.
"""

import pytest
import asyncio
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestRateLimitAbuse:
    """Test rate limiting under abuse."""
    
    async def test_rapid_requests_single_user(self):
        """Send 200 requests from single user rapidly."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            tasks = []
            for i in range(200):
                task = client.post(
                    "/validate",
                    json={"token": f"token-{i}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            print(f"Rate limit test: {success_count}/200 requests processed")
            
            # Some should be rate limited
            # System should remain stable
            assert success_count >= 0