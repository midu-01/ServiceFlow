import asyncio
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.db.models.user import User, UserRole
from app.dependencies import get_db
from app.main import create_app
from app.workers.tasks.request_tasks import run_service_request_pipeline

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Seed test users
        op1 = User(
            username="e2e_operator_1",
            email="e2e_op1@serviceflow.internal",
            hashed_password=hash_password("OperatorPass123!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        op2 = User(
            username="e2e_operator_2",
            email="e2e_op2@serviceflow.internal",
            hashed_password=hash_password("OperatorPass123!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        sup = User(
            username="e2e_supervisor",
            email="e2e_sup@serviceflow.internal",
            hashed_password=hash_password("SupervisorPass123!"),
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        session.add_all([op1, op2, sup])
        await session.commit()

    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def app(session_factory):
    test_app = create_app()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.mark.asyncio
async def test_e2e_full_service_request_lifecycle(app, session_factory):
    """End-to-End: Authentication -> Submission -> Background Execution -> Verification."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login as Operator 1
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "e2e_operator_1", "password": "OperatorPass123!"},
        )
        assert login_res.status_code == 200
        op1_token = login_res.json()["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {op1_token}"}

        # 2. Submit Service Request
        create_res = await client.post(
            "/api/v1/service-requests",
            headers=auth_headers,
            json={
                "title": "E2E Billing Reconciliation",
                "description": "Execute complete reconciliation of quarterly billing transactions.",
            },
        )
        assert create_res.status_code == 201
        created_data = create_res.json()["data"]
        request_id = created_data["id"]
        assert created_data["status"] == "QUEUED"
        assert created_data["progress_percent"] == 0

        # 3. Simulate Background Worker Execution
        async with session_factory() as worker_session:
            completed_sr = await run_service_request_pipeline(
                request_id_str=request_id,
                session=worker_session,
                step_delay=0.0,
            )
            assert completed_sr is not None
            assert completed_sr.status == RequestStatus.COMPLETED
            assert completed_sr.progress_percent == 100

        # 4. Operator queries request detail
        detail_res = await client.get(
            f"/api/v1/service-requests/{request_id}",
            headers=auth_headers,
        )
        assert detail_res.status_code == 200
        detail_data = detail_res.json()["data"]
        assert detail_data["status"] == "COMPLETED"
        assert detail_data["progress_percent"] == 100
        assert detail_data["started_at"] is not None
        assert detail_data["completed_at"] is not None
        assert detail_data["error_message"] is None


@pytest.mark.asyncio
async def test_e2e_cross_operator_isolation(app):
    """Security Check: Verify strict tenant and ownership isolation between operators."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Operator 1 login & creation
        op1_login = await client.post("/api/v1/auth/login", json={"username": "e2e_operator_1", "password": "OperatorPass123!"})
        op1_token = op1_login.json()["data"]["access_token"]

        create_res = await client.post(
            "/api/v1/service-requests",
            headers={"Authorization": f"Bearer {op1_token}"},
            json={"title": "Private Operator 1 Request", "description": "Strictly confidential task."},
        )
        req_id = create_res.json()["data"]["id"]

        # Operator 2 login
        op2_login = await client.post("/api/v1/auth/login", json={"username": "e2e_operator_2", "password": "OperatorPass123!"})
        op2_token = op2_login.json()["data"]["access_token"]

        # Operator 2 attempts to read -> 403 Forbidden
        op2_read = await client.get(
            f"/api/v1/service-requests/{req_id}",
            headers={"Authorization": f"Bearer {op2_token}"},
        )
        assert op2_read.status_code == 403
        assert op2_read.json()["error"]["code"] == "forbidden"

        # Operator 2 attempts to cancel -> 403 Forbidden
        op2_cancel = await client.post(
            f"/api/v1/service-requests/{req_id}/cancel",
            headers={"Authorization": f"Bearer {op2_token}"},
        )
        assert op2_cancel.status_code == 403

        # Supervisor login & read -> 200 OK
        sup_login = await client.post("/api/v1/auth/login", json={"username": "e2e_supervisor", "password": "SupervisorPass123!"})
        sup_token = sup_login.json()["data"]["access_token"]

        sup_read = await client.get(
            f"/api/v1/service-requests/{req_id}",
            headers={"Authorization": f"Bearer {sup_token}"},
        )
        assert sup_read.status_code == 200


@pytest.mark.asyncio
async def test_e2e_race_condition_cancellation(app, session_factory):
    """Race Condition: Pre-cancellation halts worker safely and prevents invalid state transitions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        op1_login = await client.post("/api/v1/auth/login", json={"username": "e2e_operator_1", "password": "OperatorPass123!"})
        op1_token = op1_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {op1_token}"}

        # 1. Create request
        create_res = await client.post(
            "/api/v1/service-requests",
            headers=headers,
            json={"title": "Cancelled Task Before Pickup", "description": "This task is cancelled right away."},
        )
        req_id = create_res.json()["data"]["id"]

        # 2. Cancel while QUEUED -> 200 OK
        cancel_res = await client.post(
            f"/api/v1/service-requests/{req_id}/cancel",
            headers=headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["data"]["status"] == "CANCELLED"

        # 3. Worker task receives job -> verifies DB status is CANCELLED and halts without processing
        async with session_factory() as worker_session:
            pipeline_result = await run_service_request_pipeline(
                request_id_str=req_id,
                session=worker_session,
                step_delay=0.0,
            )
            assert pipeline_result is not None
            assert pipeline_result.status == RequestStatus.CANCELLED
            assert pipeline_result.started_at is None

        # 4. Attempting to cancel a CANCELLED task -> 409 Conflict
        second_cancel = await client.post(
            f"/api/v1/service-requests/{req_id}/cancel",
            headers=headers,
        )
        assert second_cancel.status_code == 409
        assert second_cancel.json()["error"]["code"] == "resource_conflict"


@pytest.mark.asyncio
async def test_e2e_burst_concurrent_submissions(app):
    """Verifies that rapid burst submissions succeed without ID collisions or data corruption."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        op1_login = await client.post("/api/v1/auth/login", json={"username": "e2e_operator_1", "password": "OperatorPass123!"})
        op1_token = op1_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {op1_token}"}

        # Submit 6 requests in rapid sequence
        created_ids = []
        for i in range(6):
            res = await client.post(
                "/api/v1/service-requests",
                headers=headers,
                json={
                    "title": f"Burst Task #{i+1}",
                    "description": f"Rapid submission test batch iteration {i+1}.",
                },
            )
            assert res.status_code == 201
            created_ids.append(res.json()["data"]["id"])

        # Check all 6 IDs are unique
        assert len(set(created_ids)) == 6

        # Query list
        list_res = await client.get("/api/v1/service-requests?limit=10", headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["meta"]["total"] >= 6
