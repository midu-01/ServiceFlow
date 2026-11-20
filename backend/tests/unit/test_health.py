import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_health_liveness(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_ready_endpoint_structure(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
        # In local test without running DB/Redis, ready endpoint returns 503 or 200 with structured dependencies dict
        assert response.status_code in [200, 503]
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]
