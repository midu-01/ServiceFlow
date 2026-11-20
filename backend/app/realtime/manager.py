from typing import Dict, List, Set
from fastapi import WebSocket
from app.core.logging import logger


class ConnectionManager:
    """Manages active WebSocket connections by user and role."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        self.user_connections.setdefault(user_id, []).append(websocket)
        logger.info(f"WebSocket client connected: user={user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        self.active_connections.discard(websocket)
        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                ws for ws in self.user_connections[user_id] if ws != websocket
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"WebSocket client disconnected: user={user_id}")

    async def broadcast_json(self, message: dict) -> None:
        dead_connections: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead_conn in dead_connections:
            self.active_connections.discard(dead_conn)


ws_manager = ConnectionManager()
