from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from .base import BaseEvent, EventType


class ApiUsageEvent(BaseEvent):
    """Emitted after every LLM or external API call to track token consumption and cost."""

    event_type: Literal["agent.api_usage"] = EventType.API_USAGE.value
    agent_id: str
    execution_id: str
    provider: str
    token_type: Literal["service_account"] = "service_account"
    tokens_used: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0, default=0.0)
    model: Optional[str] = None
