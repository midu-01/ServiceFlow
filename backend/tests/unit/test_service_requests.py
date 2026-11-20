import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.db.models.user import User, UserRole
from app.dependencies import get_db
from app.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # Seed test users
        op1 = User(
            username="operator_one",
            email="op1@test.internal",
            hashed_password=hash_password("OperatorPass123!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        op2 = User(
            username="operator_two",
            email="op2@test.internal",
            hashed_password=hash_password("OperatorPass123!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        sup = User(
            username="supervisor_one",
            email="sup1@test.internal",
            hashed_password=hash_password("SupervisorPass123!"),
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        session.add_all([op1, op2, sup])
        await session.commit()
        await session.refresh(op1)
        await session.refresh(op2)
        await session.refresh(sup)

        # Seed pre-existing requests
        sr1 = ServiceRequest(
            title="Database Backup Routine",
            description="Run weekly snapshot backup of production tables.",
            status=RequestStatus.QUEUED,
            creator=op1,
        )
        sr2 = ServiceRequest(
            title="Search Index Rebuild",
            description="Rebuild full-text search inverted index.",
            status=RequestStatus.PROCESSING,
            progress_percent=40,
            creator=op1,
        )
        sr3 = ServiceRequest(
            title="User Report Export",
            description="Export CSV report of all registered accounts.",
            status=RequestStatus.QUEUED,
            creator=op2,
        )
        session.add_all([sr1, sr2, sr3])
        await session.commit()
        await session.refresh(sr1)
        await session.refresh(sr2)
        await session.refresh(sr3)

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def app(async_session):
    test_app = create_app()

    async def override_get_db():
        yield async_session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


def auth_header(user_id: uuid.UUID, role: UserRole) -> dict:
    token = create_access_token(subject=str(user_id), role=role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_service_request_success(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get op1
        from sqlalchemy import select
        res_user = await async_session.execute(select(User).where(User.username == "operator_one"))
        op1 = res_user.scalar_one()

        res = await client.post(
            "/api/v1/service-requests",
            headers=auth_header(op1.id, op1.role),
            json={
                "title": "API Gateway Rate Limit Update",
                "description": "Adjust global rate limiting bucket thresholds for partner tier.",
            },
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["title"] == "API Gateway Rate Limit Update"
        assert data["status"] == "QUEUED"
        assert data["progress_percent"] == 0
        assert data["created_by_id"] == str(op1.id)
        assert f"/api/v1/service-requests/{data['id']}" in res.headers["Location"]


@pytest.mark.asyncio
async def test_create_service_request_validation_failure(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from sqlalchemy import select
        res_user = await async_session.execute(select(User).where(User.username == "operator_one"))
        op1 = res_user.scalar_one()

        # Title too short (< 3 chars)
        res = await client.post(
            "/api/v1/service-requests",
            headers=auth_header(op1.id, op1.role),
            json={"title": "AB", "description": "This is a valid long description."},
        )
        assert res.status_code == 422
        data = res.json()
        assert data["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_list_requests_role_scoping(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from sqlalchemy import select
        res_op1 = await async_session.execute(select(User).where(User.username == "operator_one"))
        op1 = res_op1.scalar_one()

        res_sup = await async_session.execute(select(User).where(User.username == "supervisor_one"))
        sup = res_sup.scalar_one()

        # Operator 1 lists requests: should only see their own 2 requests
        op1_res = await client.get(
            "/api/v1/service-requests",
            headers=auth_header(op1.id, op1.role),
        )
        assert op1_res.status_code == 200
        op1_data = op1_res.json()
        assert op1_data["meta"]["total"] == 2
        for item in op1_data["data"]:
            assert item["created_by_id"] == str(op1.id)

        # Supervisor lists requests: should see all 3 requests
        sup_res = await client.get(
            "/api/v1/service-requests",
            headers=auth_header(sup.id, sup.role),
        )
        assert sup_res.status_code == 200
        sup_data = sup_res.json()
        assert sup_data["meta"]["total"] == 3


@pytest.mark.asyncio
async def test_list_requests_filtering_and_pagination(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from sqlalchemy import select
        res_sup = await async_session.execute(select(User).where(User.username == "supervisor_one"))
        sup = res_sup.scalar_one()

        # Filter by status QUEUED
        q_res = await client.get(
            "/api/v1/service-requests?status=QUEUED",
            headers=auth_header(sup.id, sup.role),
        )
        assert q_res.status_code == 200
        assert q_res.json()["meta"]["total"] == 2

        # Search query matching "Index"
        search_res = await client.get(
            "/api/v1/service-requests?search=Index",
            headers=auth_header(sup.id, sup.role),
        )
        assert search_res.status_code == 200
        assert search_res.json()["meta"]["total"] == 1
        assert search_res.json()["data"][0]["title"] == "Search Index Rebuild"

        # Pagination: limit=1
        page_res = await client.get(
            "/api/v1/service-requests?limit=1&offset=0",
            headers=auth_header(sup.id, sup.role),
        )
        assert page_res.status_code == 200
        meta = page_res.json()["meta"]
        assert len(page_res.json()["data"]) == 1
        assert meta["limit"] == 1
        assert meta["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_request_detail_and_authorization(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from sqlalchemy import select
        op1 = (await async_session.execute(select(User).where(User.username == "operator_one"))).scalar_one()
        op2 = (await async_session.execute(select(User).where(User.username == "operator_two"))).scalar_one()
        sup = (await async_session.execute(select(User).where(User.username == "supervisor_one"))).scalar_one()

        sr1 = (await async_session.execute(select(ServiceRequest).where(ServiceRequest.title == "Database Backup Routine"))).scalar_one()

        # 1. Creator (op1) gets details -> 200 OK
        res1 = await client.get(
            f"/api/v1/service-requests/{sr1.id}",
            headers=auth_header(op1.id, op1.role),
        )
        assert res1.status_code == 200
        assert res1.json()["data"]["id"] == str(sr1.id)

        # 2. Non-owner (op2) gets details -> 403 Forbidden
        res2 = await client.get(
            f"/api/v1/service-requests/{sr1.id}",
            headers=auth_header(op2.id, op2.role),
        )
        assert res2.status_code == 403
        assert res2.json()["error"]["code"] == "forbidden"

        # 3. Supervisor gets details -> 200 OK
        res3 = await client.get(
            f"/api/v1/service-requests/{sr1.id}",
            headers=auth_header(sup.id, sup.role),
        )
        assert res3.status_code == 200

        # 4. Non-existent ID -> 404 Not Found
        random_id = uuid.uuid4()
        res4 = await client.get(
            f"/api/v1/service-requests/{random_id}",
            headers=auth_header(sup.id, sup.role),
        )
        assert res4.status_code == 404


@pytest.mark.asyncio
async def test_atomic_cancellation_lifecycle(app, async_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        from sqlalchemy import select
        op1 = (await async_session.execute(select(User).where(User.username == "operator_one"))).scalar_one()
        op2 = (await async_session.execute(select(User).where(User.username == "operator_two"))).scalar_one()

        sr_queued = (await async_session.execute(select(ServiceRequest).where(ServiceRequest.title == "Database Backup Routine"))).scalar_one()
        sr_processing = (await async_session.execute(select(ServiceRequest).where(ServiceRequest.title == "Search Index Rebuild"))).scalar_one()

        # 1. op2 tries to cancel op1's request -> 403 Forbidden
        res_forbidden = await client.post(
            f"/api/v1/service-requests/{sr_queued.id}/cancel",
            headers=auth_header(op2.id, op2.role),
        )
        assert res_forbidden.status_code == 403

        # 2. op1 cancels sr_processing (status is PROCESSING) -> 409 Conflict
        res_conflict = await client.post(
            f"/api/v1/service-requests/{sr_processing.id}/cancel",
            headers=auth_header(op1.id, op1.role),
        )
        assert res_conflict.status_code == 409
        assert "cannot be cancelled" in res_conflict.json()["error"]["message"]

        # 3. op1 cancels sr_queued (status is QUEUED) -> 200 OK
        res_cancel = await client.post(
            f"/api/v1/service-requests/{sr_queued.id}/cancel",
            headers=auth_header(op1.id, op1.role),
        )
        assert res_cancel.status_code == 200
        assert res_cancel.json()["data"]["status"] == "CANCELLED"
        assert res_cancel.json()["data"]["cancelled_at"] is not None
