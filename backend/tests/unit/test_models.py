import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import RequestStatus, ServiceRequest, User, UserRole

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


def test_metadata_tables():
    """Verify that both tables exist in metadata."""
    assert "users" in Base.metadata.tables
    assert "service_requests" in Base.metadata.tables


@pytest.mark.asyncio
async def test_create_user_and_request_relationship(async_session):
    """Verify entity persistence and foreign-key relationship."""
    # 1. Create User
    user = User(
        username="operator_test",
        email="operator@serviceflow.internal",
        hashed_password="argon2_hashed_secret",
        role=UserRole.OPERATOR,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.role == UserRole.OPERATOR
    assert user.is_active is True
    assert user.created_at is not None

    user_id = user.id

    # 2. Create Service Request for user
    sr = ServiceRequest(
        title="ETL Job Processing",
        description="Extract and load batch customer transactions.",
        status=RequestStatus.QUEUED,
        creator=user,
    )
    async_session.add(sr)
    await async_session.commit()
    await async_session.refresh(sr)

    assert isinstance(sr.id, uuid.UUID)
    assert sr.status == RequestStatus.QUEUED
    assert sr.progress_percent == 0
    assert sr.created_by_id == user_id

    # 3. Query relationship
    stmt = (
        select(User)
        .options(selectinload(User.service_requests))
        .where(User.id == user_id)
    )
    result = await async_session.execute(stmt)
    fetched_user = result.scalar_one()

    assert len(fetched_user.service_requests) == 1
    assert fetched_user.service_requests[0].title == "ETL Job Processing"
