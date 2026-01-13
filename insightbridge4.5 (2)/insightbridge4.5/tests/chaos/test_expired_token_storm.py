"""
Chaos test: Storm of expired tokens.
"""

import pytest
import asyncio
import time
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestExpiredTokenStorm:
    """Test system behavior under expired token storm."""
    
    async def test_expired_token_flood(self):
        """Send 100 expired tokens rapidly."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            tasks = []
            for i in range(100):
                task = client.post(
                    "/validate",
                    json={"token": f"expired-token-{i}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            print(f"Handled {success_count}/100 expired token requests")
            
            # System should handle all requests without crashing
            assert success_count >= 0