from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import BaseEvent, EventType


class AgentRegistrationEvent(BaseEvent):
    """Emitted once on agent startup."""

    event_type: Literal["agent.registration"] = EventType.REGISTRATION.value
    agent_id: str
    runtime: str
    version: str
    owner: str
    capabilities: list[str] = Field(default_factory=list)
    permissions_requested: list[str] = Field(default_factory=list)
