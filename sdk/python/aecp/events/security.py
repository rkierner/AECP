from __future__ import annotations

from typing import Any, Dict, Literal

from .base import BaseEvent, EventType, SeverityType, ViolationType


class SecurityEvent(BaseEvent):
    """
    Emitted when a policy violation is detected.
    Always emitted before execution is blocked — never suppressed.
    """

    event_type: Literal["agent.security"] = EventType.SECURITY.value
    agent_id: str
    violation_type: ViolationType
    severity: SeverityType
    details: Dict[str, Any]
