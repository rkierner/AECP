from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .models import AgentMetadata, AgentRegistrationRequest


class AgentStore:
    """
    In-memory agent registry with asyncio-safe locking.

    Upgrade path to SQLite persistence:
      - Replace self._agents dict with aiosqlite connection
      - Schema: CREATE TABLE agents (
            agent_id TEXT PRIMARY KEY,
            runtime TEXT NOT NULL,
            version TEXT NOT NULL,
            owner TEXT NOT NULL,
            capabilities JSON NOT NULL,
            permissions_requested JSON NOT NULL,
            registered_at TEXT NOT NULL,
            last_seen TEXT
        )
      - Use aiosqlite.connect(db_path) in __init__ and wrap all operations
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentMetadata] = {}
        self._lock = asyncio.Lock()

    async def register(self, request: AgentRegistrationRequest) -> AgentMetadata:
        async with self._lock:
            now = datetime.now(tz=timezone.utc)
            metadata = AgentMetadata(
                agent_id=request.agent_id,
                runtime=request.runtime,
                version=request.version,
                owner=request.owner,
                capabilities=request.capabilities,
                permissions_requested=request.permissions_requested,
                registered_at=now,
                last_seen=now,
            )
            self._agents[request.agent_id] = metadata
            return metadata

    async def get(self, agent_id: str) -> AgentMetadata | None:
        async with self._lock:
            return self._agents.get(agent_id)

    def list_all(self) -> list[AgentMetadata]:
        # No lock needed — reading an immutable snapshot is safe for health checks
        return list(self._agents.values())
