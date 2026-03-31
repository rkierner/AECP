from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from .base import BaseEvent, EventType, StatusType


class ExecutionEvent(BaseEvent):
    """Emitted after every governed agent action completes (success or failure)."""

    event_type: Literal["agent.execution"] = EventType.EXECUTION.value
    agent_id: str
    execution_id: str
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = None
    action: str
    status: StatusType
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
