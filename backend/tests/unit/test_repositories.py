import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import RequestStatus, ServiceRequest, User, UserRole
from app.repositories.service_request_repository import ServiceRequestRepository
from app.repositories.user_repository import UserRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_repository(async_session):
    repo = UserRepository(async_session)

    user = User(
        username="supervisor_dan",
        email="dan@serviceflow.internal",
        hashed_password="hashed_pw",
        role=UserRole.SUPERVISOR,
    )
    repo.add(user)
    await repo.commit()
    await repo.refresh(user)

    fetched = await repo.get_by_username("supervisor_dan")
    assert fetched is not None
    assert fetched.email == "dan@serviceflow.internal"

    by_email = await repo.get_by_email("dan@serviceflow.internal")
    assert by_email is not None
    assert by_email.id == user.id

    missing = await repo.get_by_username("unknown_user")
    assert missing is None


@pytest.mark.asyncio
async def test_service_request_repository_and_atomic_cancel(async_session):
    user_repo = UserRepository(async_session)
    sr_repo = ServiceRequestRepository(async_session)

    user = User(
        username="operator_bob",
        email="bob@serviceflow.internal",
        hashed_password="hashed_pw",
        role=UserRole.OPERATOR,
    )
    user_repo.add(user)
    await user_repo.commit()
    await user_repo.refresh(user)

    # 1. Create two requests
    req1 = ServiceRequest(
        title="Payment Reconciliation Batch",
        description="Run nightly reconciliation of payment settlement files.",
        status=RequestStatus.QUEUED,
        creator=user,
    )
    req2 = ServiceRequest(
        title="Email Audit Delivery",
        description="Scan logs for transactional email delivery discrepancies.",
        status=RequestStatus.PROCESSING,
        progress_percent=20,
        creator=user,
    )
    sr_repo.add(req1)
    sr_repo.add(req2)
    await sr_repo.commit()

    # 2. Filtered listing
    items, total = await sr_repo.list_filtered(created_by_id=user.id)
    assert total == 2
    assert len(items) == 2

    # Status filter
    queued_items, q_total = await sr_repo.list_filtered(status=RequestStatus.QUEUED)
    assert q_total == 1
    assert queued_items[0].title == "Payment Reconciliation Batch"

    # Search filter
    search_items, s_total = await sr_repo.list_filtered(search="Payment")
    assert s_total == 1
    assert search_items[0].id == req1.id

    # 3. Atomic Cancellation:
    # req1 is QUEUED -> should succeed
    cancelled = await sr_repo.atomic_cancel(req1.id, created_by_id=user.id)
    assert cancelled is True

    updated_req1 = await sr_repo.get_by_id(req1.id)
    assert updated_req1.status == RequestStatus.CANCELLED
    assert updated_req1.cancelled_at is not None

    # req2 is PROCESSING -> should fail (return False)
    cancelled_req2 = await sr_repo.atomic_cancel(req2.id, created_by_id=user.id)
    assert cancelled_req2 is False

    # 4. Progress update
    updated_req2 = await sr_repo.update_progress(
        req2.id,
        progress_percent=100,
        current_step="Step 5: Finished",
        status=RequestStatus.COMPLETED,
    )
    assert updated_req2.progress_percent == 100
    assert updated_req2.status == RequestStatus.COMPLETED
    assert updated_req2.completed_at is not None
