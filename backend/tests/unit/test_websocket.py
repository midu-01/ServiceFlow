import uuid
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models.user import User, UserRole
from app.db.session import AsyncSessionLocal
from app.main import create_app
from app.realtime.manager import ws_manager

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def test_setup():
    # Setup test database engine and mock AsyncSessionLocal
    engine = create_async_engine(TEST_DB_URL, echo=False)

    import asyncio
    async def _init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            op1 = User(
                username="ws_operator_1",
                email="ws_op1@test.internal",
                hashed_password=hash_password("Pass123!"),
                role=UserRole.OPERATOR,
                is_active=True,
            )
            op2 = User(
                username="ws_operator_2",
                email="ws_op2@test.internal",
                hashed_password=hash_password("Pass123!"),
                role=UserRole.OPERATOR,
                is_active=True,
            )
            sup = User(
                username="ws_supervisor",
                email="ws_sup@test.internal",
                hashed_password=hash_password("Pass123!"),
                role=UserRole.SUPERVISOR,
                is_active=True,
            )
            session.add_all([op1, op2, sup])
            await session.commit()
            await session.refresh(op1)
            await session.refresh(op2)
            await session.refresh(sup)
            return op1.id, op2.id, sup.id, factory

    op1_id, op2_id, sup_id, factory = asyncio.run(_init_db())

    # Monkeypatch AsyncSessionLocal in websocket module to query this factory
    from app.api.v1.endpoints import websocket as ws_module
    original_factory = ws_module.AsyncSessionLocal
    ws_module.AsyncSessionLocal = factory

    app = create_app()
    client = TestClient(app)

    yield {
        "client": client,
        "op1_id": op1_id,
        "op2_id": op2_id,
        "sup_id": sup_id,
    }

    ws_module.AsyncSessionLocal = original_factory
    asyncio.run(engine.dispose())


def test_websocket_connect_success_and_heartbeat(test_setup):
    client = test_setup["client"]
    op1_id = test_setup["op1_id"]
    token = create_access_token(subject=str(op1_id), role="OPERATOR")

    with client.websocket_connect(f"/api/v1/ws/service-requests?token={token}") as websocket:
        # Receive connection.ready frame
        data = websocket.receive_json()
        assert data["event_type"] == "connection.ready"
        assert data["data"]["username"] == "ws_operator_1"
        assert data["data"]["role"] == "OPERATOR"

        # Send heartbeat ping
        websocket.send_text('{"type": "ping"}')
        pong = websocket.receive_text()
        assert pong == '{"type":"pong"}'


def test_websocket_reject_invalid_token(test_setup):
    client = test_setup["client"]
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws/service-requests?token=invalid.token.here"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_reject_unauthorized_origin(test_setup):
    client = test_setup["client"]
    op1_id = test_setup["op1_id"]
    token = create_access_token(subject=str(op1_id), role="OPERATOR")

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/v1/ws/service-requests?token={token}",
            headers={"Origin": "https://malicious-site.com"},
        ):
            pass
    assert exc_info.value.code == 1008


def test_websocket_role_filtered_event_distribution(test_setup):
    client = test_setup["client"]
    op1_id = str(test_setup["op1_id"])
    op2_id = str(test_setup["op2_id"])
    sup_id = str(test_setup["sup_id"])

    token_op1 = create_access_token(subject=op1_id, role="OPERATOR")
    token_op2 = create_access_token(subject=op2_id, role="OPERATOR")
    token_sup = create_access_token(subject=sup_id, role="SUPERVISOR")

    # Connect op1 and sup
    with client.websocket_connect(f"/api/v1/ws/service-requests?token={token_op1}") as ws_op1:
        with client.websocket_connect(f"/api/v1/ws/service-requests?token={token_sup}") as ws_sup:
            # Drain connection.ready messages
            ws_op1.receive_json()
            ws_sup.receive_json()

            import asyncio
            # Broadcast event belonging to op1
            event_op1 = {
                "event_id": str(uuid.uuid4()),
                "event_type": "service_request.progress_updated",
                "occurred_at": "2026-11-20T20:30:00Z",
                "request_id": str(uuid.uuid4()),
                "data": {
                    "progress_percent": 60,
                    "created_by_id": op1_id,
                },
            }
            asyncio.run(ws_manager.broadcast_event(event_op1))

            # Both op1 (owner) and supervisor should receive it
            msg_op1 = ws_op1.receive_json()
            assert msg_op1["event_type"] == "service_request.progress_updated"
            assert msg_op1["data"]["created_by_id"] == op1_id

            msg_sup = ws_sup.receive_json()
            assert msg_sup["event_type"] == "service_request.progress_updated"

            # Now broadcast event belonging to op2 (who is not op1)
            event_op2 = {
                "event_id": str(uuid.uuid4()),
                "event_type": "service_request.created",
                "occurred_at": "2026-11-20T20:30:05Z",
                "request_id": str(uuid.uuid4()),
                "data": {
                    "title": "Op2 Secret Request",
                    "created_by_id": op2_id,
                },
            }
            asyncio.run(ws_manager.broadcast_event(event_op2))

            # Supervisor receives it
            msg_sup_2 = ws_sup.receive_json()
            assert msg_sup_2["event_type"] == "service_request.created"
            assert msg_sup_2["data"]["title"] == "Op2 Secret Request"

            # Send a ping to op1 to verify op1 did NOT receive event_op2 (op1 queue has no event)
            ws_op1.send_text('{"type": "ping"}')
            pong_msg = ws_op1.receive_text()
            assert pong_msg == '{"type":"pong"}'
