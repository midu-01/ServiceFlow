import asyncio
import uuid
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.db.models.user import User, UserRole
from app.repositories.service_request_repository import ServiceRequestRepository
from app.workers.tasks.request_tasks import run_service_request_pipeline

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        user = User(
            username="worker_test_user",
            email="worker@test.internal",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.OPERATOR,
        )
        session.add(user)
        await session.commit()

    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_worker_pipeline_success(async_session):
    repo = ServiceRequestRepository(async_session)

    # 1. Create a queued request
    from sqlalchemy import select
    user = (await async_session.execute(select(User))).scalar_one()

    sr = ServiceRequest(
        title="Automated Data Ingestion",
        description="Ingest telemetry records from field devices.",
        status=RequestStatus.QUEUED,
        creator=user,
    )
    repo.add(sr)
    await repo.commit()
    await repo.refresh(sr)

    # 2. Run pipeline with zero delay for instant test
    completed_sr = await run_service_request_pipeline(
        request_id_str=str(sr.id),
        session=async_session,
        step_delay=0.0,
    )

    assert completed_sr is not None
    assert completed_sr.status == RequestStatus.COMPLETED
    assert completed_sr.progress_percent == 100
    assert completed_sr.started_at is not None
    assert completed_sr.completed_at is not None
    assert completed_sr.error_message is None
    assert "Step 5" in completed_sr.current_step


@pytest.mark.asyncio
async def test_worker_pipeline_idempotency_cancelled(async_session):
    repo = ServiceRequestRepository(async_session)

    from sqlalchemy import select
    user = (await async_session.execute(select(User))).scalar_one()

    # Pre-cancel request before worker picks it
    sr = ServiceRequest(
        title="Cancelled Job",
        description="Cancelled before pickup.",
        status=RequestStatus.CANCELLED,
        creator=user,
    )
    repo.add(sr)
    await repo.commit()
    await repo.refresh(sr)

    result_sr = await run_service_request_pipeline(
        request_id_str=str(sr.id),
        session=async_session,
        step_delay=0.0,
    )

    assert result_sr is not None
    assert result_sr.status == RequestStatus.CANCELLED
    assert result_sr.started_at is None
    assert result_sr.progress_percent == 0


@pytest.mark.asyncio
async def test_worker_pipeline_non_existent_id(async_session):
    random_id = str(uuid.uuid4())
    result = await run_service_request_pipeline(
        request_id_str=random_id,
        session=async_session,
        step_delay=0.0,
    )
    assert result is None


@pytest.mark.asyncio
async def test_concurrent_multi_request_execution(session_factory):
    """Verifies that multiple requests execute concurrently without deadlock or state interference."""
    from sqlalchemy import select

    requests = []
    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()
        repo = ServiceRequestRepository(session)
        # Create 4 concurrent requests
        for i in range(4):
            sr = ServiceRequest(
                title=f"Concurrent Job #{i+1}",
                description=f"Batch job {i+1} execution under concurrent worker pool.",
                status=RequestStatus.QUEUED,
                creator=user,
            )
            repo.add(sr)
            requests.append(sr)
        await repo.commit()
        for sr in requests:
            await repo.refresh(sr)

    # Run each concurrent task with its own scoped worker database session
    async def run_single_worker(sr_id: str):
        async with session_factory() as task_session:
            return await run_service_request_pipeline(
                request_id_str=sr_id,
                session=task_session,
                step_delay=0.005,
            )

    tasks = [run_single_worker(str(sr.id)) for sr in requests]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    for res in results:
        assert res is not None
        assert res.status == RequestStatus.COMPLETED
        assert res.progress_percent == 100
        assert res.started_at is not None
        assert res.completed_at is not None
