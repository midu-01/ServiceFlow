import asyncio
import time
from datetime import datetime
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
            username="concurrency_eval_user",
            email="eval@serviceflow.internal",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.OPERATOR,
        )
        session.add(user)
        await session.commit()

    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_proven_concurrency_with_overlapping_intervals(session_factory):
    """Rigorous verification: Proves that multiple workers execute simultaneously with overlapping time windows."""
    from sqlalchemy import select

    # 1. Seed 4 queued requests
    created_requests = []
    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()
        repo = ServiceRequestRepository(session)
        for i in range(4):
            sr = ServiceRequest(
                title=f"Parallel Execution Benchmark #{i+1}",
                description=f"Concurrency benchmark workload unit {i+1}.",
                status=RequestStatus.QUEUED,
                creator=user,
            )
            repo.add(sr)
            created_requests.append(sr)
        await repo.commit()
        for sr in created_requests:
            await repo.refresh(sr)

    # 2. Worker runner with independent session and discrete step delay
    timings = {}

    async def execute_worker_task(sr_id: str, index: int):
        t_start = time.perf_counter()
        async with session_factory() as task_session:
            completed_sr = await run_service_request_pipeline(
                request_id_str=sr_id,
                session=task_session,
                step_delay=0.04,  # 5 steps * 0.04s = ~0.20s per task
            )
        t_end = time.perf_counter()
        timings[index] = {
            "id": sr_id,
            "status": completed_sr.status.value,
            "progress": completed_sr.progress_percent,
            "t_start": t_start,
            "t_end": t_end,
            "duration": t_end - t_start,
        }
        return completed_sr

    overall_start = time.perf_counter()
    results = await asyncio.gather(
        *[execute_worker_task(str(sr.id), idx) for idx, sr in enumerate(created_requests)]
    )
    overall_end = time.perf_counter()
    overall_duration = overall_end - overall_start

    # 3. Assertions & Overlap Proof:
    assert len(results) == 4
    for res in results:
        assert res.status == RequestStatus.COMPLETED
        assert res.progress_percent == 100

    sum_individual_durations = sum(t["duration"] for t in timings.values())
    
    # If tasks ran sequentially, overall_duration would equal sum_individual_durations (~0.8s).
    # Since tasks ran concurrently, overall_duration is significantly less than the sum!
    print(f"\n[CONCURRENCY PROOF] Overall Wall-clock Time: {overall_duration:.3f}s")
    print(f"[CONCURRENCY PROOF] Sum of Individual Task Times: {sum_individual_durations:.3f}s")
    print(f"[CONCURRENCY PROOF] Parallelism Speedup Factor: {sum_individual_durations / overall_duration:.2f}x")

    assert overall_duration < sum_individual_durations * 0.7, (
        f"Expected concurrent overlap! Overall time ({overall_duration:.3f}s) should be much less than "
        f"sequential sum ({sum_individual_durations:.3f}s)."
    )

    # Prove overlapping time windows: Latest task start must be before Earliest task completion
    latest_start = max(t["t_start"] for t in timings.values())
    earliest_end = min(t["t_end"] for t in timings.values())
    assert latest_start < earliest_end, "All 4 worker tasks overlapped simultaneously in time!"
