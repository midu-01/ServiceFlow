import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient
from app.core.errors import ConflictError, NotFoundError
from app.main import create_app

dummy_router = APIRouter()


@dummy_router.get("/test/not-found")
async def trigger_not_found():
    raise NotFoundError("Test entity not found")


@dummy_router.get("/test/conflict")
async def trigger_conflict():
    raise ConflictError("State cannot transition")


@dummy_router.get("/test/unhandled")
async def trigger_unhandled():
    raise RuntimeError("Sensitive internal database connection failed: secret_pw=123")


@pytest.fixture
def app():
    test_app = create_app()
    test_app.include_router(dummy_router)
    return test_app


@pytest.mark.asyncio
async def test_not_found_error_envelope(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/test/not-found")
        assert res.status_code == 404
        data = res.json()
        assert data["error"]["code"] == "not_found"
        assert data["error"]["message"] == "Test entity not found"
        assert "X-Request-ID" in res.headers


@pytest.mark.asyncio
async def test_conflict_error_envelope(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/test/conflict")
        assert res.status_code == 409
        data = res.json()
        assert data["error"]["code"] == "resource_conflict"
        assert data["error"]["message"] == "State cannot transition"


@pytest.mark.asyncio
async def test_unhandled_error_does_not_leak_stacktrace(app):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        res = await client.get("/test/unhandled")
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "internal_error"
        # Must NOT leak secret_pw or internal exception text
        assert "secret_pw" not in data["error"]["message"]
        assert "Traceback" not in str(data)
        assert data["error"]["message"] == "An unexpected server error occurred. Please try again later."


@pytest.mark.asyncio
async def test_request_id_preserved_when_provided(app):
    custom_id = "custom-req-id-12345"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert res.status_code == 200
        assert res.headers["X-Request-ID"] == custom_id
