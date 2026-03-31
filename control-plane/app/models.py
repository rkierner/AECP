from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class AgentRegistrationRequest(BaseModel):
    agent_id: str
    runtime: str
    version: str
    owner: str
    capabilities: List[str] = Field(default_factory=list)
    permissions_requested: List[str] = Field(default_factory=list)


class AgentMetadata(BaseModel):
    agent_id: str
    runtime: str
    version: str
    owner: str
    capabilities: List[str]
    permissions_requested: List[str]
    registered_at: datetime
    last_seen: Optional[datetime] = None


class AgentRegistrationResponse(BaseModel):
    agent_id: str
    registered_at: datetime


class ViolationReport(BaseModel):
    agent_id: str
    violation_type: str
    severity: str
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=_utcnow)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class HealthResponse(BaseModel):
    status: str
    agents_registered: int


class AgentStatusSummary(BaseModel):
    agent_id: str
    display_name: str
    status: str  # "healthy" | "degraded" | "unhealthy" | "offline"
    last_heartbeat: Optional[datetime]
    events_today: int
    daily_spend_usd: float
    daily_budget_usd: float
    violations_today: int


class EventVolumeBucket(BaseModel):
    hour: str  # ISO 8601 UTC
    count: int


class DashboardStats(BaseModel):
    active_agents: int
    active_agents_delta: str
    events_today: int
    events_today_delta: str
    security_violations: int
    violations_delta: str
    daily_spend_usd: float
    spend_budget_usd: float
    spend_delta: str
    event_volume_series: List[EventVolumeBucket]
    cost_by_agent_series: Dict[str, Dict[str, float]]  # agent_id → {day_abbr → cost}
