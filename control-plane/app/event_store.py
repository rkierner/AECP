from __future__ import annotations

import asyncio
from collections import deque
from typing import Optional


class EventStore:
    """
    Bounded in-memory event store with asyncio-safe locking and SSE fan-out.

    Holds the last MAX_EVENTS events across all agents. Subscribers receive
    a push notification via asyncio.Queue whenever a new event is ingested.

    This is intentionally simple — the source of truth is Kafka. This store
    is a read-side cache for the dashboard, not a durable log.
    """

    MAX_EVENTS = 2000

    def __init__(self) -> None:
        self._events: deque[dict] = deque(maxlen=self.MAX_EVENTS)
        self._lock = asyncio.Lock()
        self._subscribers: list[asyncio.Queue] = []

    async def ingest(self, event: dict) -> None:
        """Append an event and fan out to all active SSE subscribers."""
        async with self._lock:
            self._events.append(event)
            dead: list[asyncio.Queue] = []
            for q in self._subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Slow consumer — drop and mark for removal
                    dead.append(q)
            for q in dead:
                self._subscribers.remove(q)

    async def list_recent(
        self,
        limit: int = 200,
        event_type: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> list[dict]:
        """Return a filtered snapshot, newest-first, up to `limit` entries."""
        async with self._lock:
            snapshot = list(self._events)

        if event_type:
            snapshot = [e for e in snapshot if e.get("event_type") == event_type]
        if agent_id:
            snapshot = [e for e in snapshot if e.get("agent_id") == agent_id]

        # Reverse so newest first, then apply limit
        snapshot.reverse()
        return snapshot[:limit]

    async def subscribe(self) -> asyncio.Queue:
        """Register a new SSE subscriber. Returns a Queue that receives events."""
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        async with self._lock:
            self._subscribers.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        """Remove a subscriber on client disconnect."""
        async with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass  # already removed (e.g. evicted as slow consumer)

    def snapshot(self) -> list[dict]:
        """Synchronous snapshot for stats computation — no lock needed for reads."""
        return list(self._events)
