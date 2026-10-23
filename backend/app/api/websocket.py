import json
import logging
import asyncio
from typing import Dict, List, Set, Any
from fastapi import WebSocket

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per run_id with Redis Pub/Sub integration."""

    def __init__(self):
        # run_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._redis_listeners: Dict[str, asyncio.Task] = {}

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        """Accept WebSocket and register under run_id."""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()
            self._start_redis_listener(run_id)
        self.active_connections[run_id].add(websocket)
        logger.info(f"WebSocket connected for run {run_id}. Total listeners: {len(self.active_connections[run_id])}")

    def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        """Unregister WebSocket and cleanup listener if empty."""
        if run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
                self._stop_redis_listener(run_id)
        logger.info(f"WebSocket disconnected for run {run_id}")

    async def broadcast(self, run_id: str, event_data: Dict[str, Any]) -> None:
        """Send JSON event to all connected clients for run_id."""
        # 1. Direct memory broadcast to active sockets
        if run_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(event_data)
                except Exception as e:
                    logger.warning(f"Error sending WebSocket message: {e}")
                    dead_connections.add(connection)
            for dead in dead_connections:
                self.active_connections[run_id].discard(dead)

        # 2. Publish to Redis channel for multi-instance scaling
        await self._publish_to_redis(run_id, event_data)

    async def _publish_to_redis(self, run_id: str, event_data: Dict[str, Any]) -> None:
        """Publish event to Redis channel run:{run_id}:events."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.publish(f"run:{run_id}:events", json.dumps(event_data))
            await r.aclose()
        except Exception:
            # Redis optional in development
            pass

    def _start_redis_listener(self, run_id: str) -> None:
        """Start background task listening to Redis pub/sub channel."""
        try:
            task = asyncio.create_task(self._listen_redis_channel(run_id))
            self._redis_listeners[run_id] = task
        except Exception:
            pass

    def _stop_redis_listener(self, run_id: str) -> None:
        """Cancel Redis pub/sub listener task."""
        if run_id in self._redis_listeners:
            self._redis_listeners[run_id].cancel()
            del self._redis_listeners[run_id]

    async def _listen_redis_channel(self, run_id: str) -> None:
        """Listen to Redis channel and forward messages to local websockets."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(f"run:{run_id}:events")
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    data = json.loads(message["data"])
                    if run_id in self.active_connections:
                        for ws in list(self.active_connections[run_id]):
                            try:
                                await ws.send_json(data)
                            except Exception:
                                pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Redis listener stopped for {run_id}: {e}")


ws_manager = ConnectionManager()
