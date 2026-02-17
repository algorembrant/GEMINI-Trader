"""
WebSocket connection manager for broadcasting real-time data
to all connected frontend clients.
"""

import json
import asyncio
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message_type: str, data: dict):
        """Broadcast a message to all connected clients."""
        message = json.dumps({
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message_type: str, data: dict):
        """Send a message to a specific client."""
        message = json.dumps({
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)
