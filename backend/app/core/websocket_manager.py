"""
Madhyastha — WebSocket Connection Manager
Manages real-time connections for joint mediation sessions
"""

from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger("madhyastha.ws")


class ConnectionManager:
    """Manages WebSocket connections for joint mediation sessions"""

    def __init__(self):
        # session_id → list of (websocket, party_id, role) tuples
        self.active_connections: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, party_id: str, role: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append({
            "websocket": websocket,
            "party_id": party_id,
            "role": role,
        })
        logger.info(f"WS connected: party={party_id} role={role} session={session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                conn for conn in self.active_connections[session_id]
                if conn["websocket"] != websocket
            ]
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WS disconnected: session={session_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        await websocket.send_json(message)

    async def broadcast_to_session(self, session_id: str, message: dict, exclude_party: str = None):
        """Broadcast a message to all connections in a session"""
        if session_id not in self.active_connections:
            return

        for conn in self.active_connections[session_id]:
            if exclude_party and conn["party_id"] == exclude_party:
                continue
            try:
                await conn["websocket"].send_json(message)
            except Exception as e:
                logger.error(f"WS broadcast error: {e}")

    async def send_to_all_in_session(self, session_id: str, message: dict):
        """Send to ALL connections in a session (including sender)"""
        if session_id not in self.active_connections:
            return

        for conn in self.active_connections[session_id]:
            try:
                await conn["websocket"].send_json(message)
            except Exception as e:
                logger.error(f"WS send error: {e}")

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session"""
        return len(self.active_connections.get(session_id, []))


# Global instance
manager = ConnectionManager()
