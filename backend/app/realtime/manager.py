from dataclasses import dataclass
from typing import Dict, List, Set
from fastapi import WebSocket
from app.core.logging import logger
from app.db.models.user import UserRole


@dataclass
class ClientConnection:
    websocket: WebSocket
    user_id: str
    role: UserRole


class ConnectionManager:
    """Manages active WebSocket connections with role-based event filtering."""

    def __init__(self) -> None:
        self.connections: Dict[WebSocket, ClientConnection] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: UserRole) -> None:
        conn = ClientConnection(websocket=websocket, user_id=user_id, role=role)
        self.connections[websocket] = conn
        self.user_connections.setdefault(user_id, set()).add(websocket)
        logger.info(f"WebSocket client registered: user_id={user_id}, role={role.value}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        if websocket in self.connections:
            del self.connections[websocket]
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"WebSocket client unregistered: user_id={user_id}")

    async def broadcast_event(self, event_envelope: dict) -> None:
        """Broadcasts event envelope with server-side authorization filtering."""
        target_creator_id = event_envelope.get("data", {}).get("created_by_id")
        dead_connections: List[WebSocket] = []

        for ws, client in list(self.connections.items()):
            # Authorization filtering:
            # 1. Supervisors and Admins receive all service request events
            # 2. Operators receive only events for their own requests
            if client.role in (UserRole.SUPERVISOR, UserRole.ADMIN):
                should_deliver = True
            elif client.role == UserRole.OPERATOR:
                # If created_by_id matches, deliver; else skip
                should_deliver = (target_creator_id == client.user_id)
            else:
                should_deliver = False

            if not should_deliver:
                continue

            try:
                await ws.send_json(event_envelope)
            except Exception as exc:
                logger.debug(f"Failed to send to WebSocket (cleaning up): {exc}")
                dead_connections.append(ws)

        # Clean up disconnected / stale sockets
        for dead_ws in dead_connections:
            if dead_ws in self.connections:
                client = self.connections[dead_ws]
                self.disconnect(dead_ws, client.user_id)

    @property
    def total_active_connections(self) -> int:
        return len(self.connections)


ws_manager = ConnectionManager()
