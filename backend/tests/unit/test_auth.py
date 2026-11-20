import pytest
from fastapi import APIRouter, Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.models.user import User, UserRole
from app.dependencies import get_current_user, get_db, require_role
from app.main import create_app
from app.schemas.common import DataResponse

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Test router for role-based endpoint testing
dummy_rbac_router = APIRouter()


@dummy_rbac_router.get("/test/supervisor-only")
async def supervisor_only_endpoint(
    user: User = Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN)),
) -> DataResponse[dict]:
    return DataResponse(data={"message": f"Welcome {user.username}"})


@pytest.fixture
async def async_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # Seed test users
        operator = User(
            username="test_operator",
            email="operator@test.internal",
            hashed_password=hash_password("OperatorPass123!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        supervisor = User(
            username="test_supervisor",
            email="supervisor@test.internal",
            hashed_password=hash_password("SupervisorPass123!"),
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        inactive = User(
            username="inactive_user",
            email="inactive@test.internal",
            hashed_password=hash_password("InactivePass123!"),
            role=UserRole.OPERATOR,
            is_active=False,
        )
        session.add_all([operator, supervisor, inactive])
        await session.commit()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def app(async_session):
    test_app = create_app()
    test_app.include_router(dummy_rbac_router)

    async def override_get_db():
        yield async_session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.mark.asyncio
async def test_login_success(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_operator", "password": "OperatorPass123!"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "test_operator"
        assert data["user"]["role"] == "OPERATOR"
        assert "serviceflow_access_token" in res.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_operator", "password": "WrongPassword999!"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert data["error"]["message"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_unknown_user(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"username": "does_not_exist", "password": "AnyPassword123!"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert data["error"]["message"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_inactive_user(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"username": "inactive_user", "password": "InactivePass123!"},
        )
        assert res.status_code == 403
        data = res.json()
        assert data["error"]["code"] == "forbidden"


@pytest.mark.asyncio
async def test_get_current_user_me_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_operator", "password": "OperatorPass123!"},
        )
        token = login_res.json()["data"]["access_token"]

        # 2. Query /me with Bearer token
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        user_data = me_res.json()["data"]
        assert user_data["username"] == "test_operator"
        assert user_data["role"] == "OPERATOR"

        # 3. Query /me with Cookie
        cookie_res = await client.get("/api/v1/auth/me")
        assert cookie_res.status_code == 200
        assert cookie_res.json()["data"]["username"] == "test_operator"

        # 4. Logout / Clear cookies and query without token -> 401
        client.cookies.clear()
        unauth_res = await client.get("/api/v1/auth/me")
        assert unauth_res.status_code == 401


@pytest.mark.asyncio
async def test_rbac_authorization(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Operator Login
        op_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_operator", "password": "OperatorPass123!"},
        )
        op_token = op_login.json()["data"]["access_token"]

        # Supervisor Login
        sup_login = await client.post(
            "/api/v1/auth/login",
            json={"username": "test_supervisor", "password": "SupervisorPass123!"},
        )
        sup_token = sup_login.json()["data"]["access_token"]

        # Operator tries to access supervisor endpoint -> 403 Forbidden
        op_access = await client.get(
            "/test/supervisor-only",
            headers={"Authorization": f"Bearer {op_token}"},
        )
        assert op_access.status_code == 403
        assert op_access.json()["error"]["code"] == "forbidden"

        # Supervisor accesses supervisor endpoint -> 200 OK
        sup_access = await client.get(
            "/test/supervisor-only",
            headers={"Authorization": f"Bearer {sup_token}"},
        )
        assert sup_access.status_code == 200
        assert sup_access.json()["data"]["message"] == "Welcome test_supervisor"
