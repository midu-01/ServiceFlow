from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.core.config import settings
from app.core.logging import logger
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.realtime.manager import ws_manager
from app.repositories.user_repository import UserRepository

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/service-requests")
async def websocket_service_requests(websocket: WebSocket) -> None:
    """Full-duplex authenticated WebSocket endpoint streaming real-time service request events."""
    # 1. Origin verification
    origin = websocket.headers.get("origin")
    if origin:
        allowed_origins = [settings.FRONTEND_ORIGIN] + settings.ALLOWED_ORIGINS
        if origin not in allowed_origins:
            logger.warning(f"WebSocket handshake rejected: unauthorized origin '{origin}'")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # 2. Token extraction from query parameter or cookie
    token = websocket.query_params.get("token") or websocket.cookies.get("serviceflow_access_token")
    if not token:
        logger.warning("WebSocket handshake rejected: missing authentication credentials")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3. Cryptographic token verification
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Token missing subject identifier")
        user_uuid = uuid.UUID(sub)
    except Exception as exc:
        logger.warning(f"WebSocket handshake rejected: token validation failure: {exc}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 4. Authoritative database user verification
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_uuid)
        if user is None or not user.is_active:
            logger.warning(f"WebSocket handshake rejected: user {user_uuid} not active or not found")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id_str = str(user.id)
        user_role = user.role
        username = user.username

    # 5. Connection acceptance and registration
    await websocket.accept()
    await ws_manager.connect(websocket, user_id=user_id_str, role=user_role)

    # 6. Send initial connection.ready frame
    try:
        await websocket.send_json({
            "event_id": str(uuid.uuid4()),
            "event_type": "connection.ready",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "user_id": user_id_str,
                "username": username,
                "role": user_role.value,
                "message": "Connected to ServiceFlow real-time stream",
            },
        })
    except Exception as exc:
        logger.warning(f"Failed to transmit connection.ready: {exc}")
        ws_manager.disconnect(websocket, user_id=user_id_str)
        return

    # 7. Keepalive / heartbeat receive loop
    try:
        while True:
            text = await websocket.receive_text()
            if text in ('{"type":"ping"}', '{"type": "ping"}', "ping"):
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected normally: user_id={user_id_str}")
    except Exception as exc:
        logger.debug(f"WebSocket connection terminated unexpectedly: {exc}")
    finally:
        ws_manager.disconnect(websocket, user_id=user_id_str)

