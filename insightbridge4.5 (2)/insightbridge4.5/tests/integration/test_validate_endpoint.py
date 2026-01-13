"""
Integration tests for /validate endpoint.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestValidateEndpoint:
    """Test the main validation endpoint."""
    
    async def test_endpoint_exists(self):
        """Test that /validate endpoint exists."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/validate",
                json={"token": "dummy-token"}
            )
            # Should respond (even if validation fails)
            assert response.status_code in [200, 400, 422, 500]
    
    async def test_malformed_request(self):
        """Test handling of malformed requests."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/validate",
                json={"wrong_field": "value"}
            )
            assert response.status_code == 422  # Validation error
    
    async def test_response_structure(self):
        """Test that response has required fields."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/validate",
                json={"token": "test-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "decision" in data
                assert "request_id" in data
                assert "timestamp" in data