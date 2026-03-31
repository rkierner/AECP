from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from .base import BaseEvent, AgentStatusType, EventType


class HeartbeatEvent(BaseEvent):
    """Emitted periodically (default 30s) to signal liveness."""

    event_type: Literal["agent.heartbeat"] = EventType.HEARTBEAT.value
    agent_id: str
    status: AgentStatusType
    last_seen: datetime
    metadata: Optional[Dict[str, Any]] = None
