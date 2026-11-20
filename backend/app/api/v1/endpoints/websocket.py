from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import logger

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/service-requests")
async def websocket_service_requests(websocket: WebSocket) -> None:
    """Placeholder WebSocket endpoint (Implemented in Phase 11)."""
    await websocket.accept()
    logger.info("WebSocket connection established (scaffold)")
    try:
        while True:
            data = await websocket.receive_text()
            if data == '{"type": "ping"}':
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
