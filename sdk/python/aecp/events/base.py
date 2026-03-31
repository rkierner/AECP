from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class EventType(str, Enum):
    REGISTRATION = "agent.registration"
    EXECUTION = "agent.execution"
    API_USAGE = "agent.api_usage"
    SECURITY = "agent.security"
    HEARTBEAT = "agent.heartbeat"


class RuntimeType(str, Enum):
    JAVA = "java"
    PYTHON = "python"
    NODE = "node"
    DOTNET = "dotnet"
    GO = "go"


class StatusType(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


class SeverityType(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationType(str, Enum):
    USER_CREDENTIAL_DETECTED = "user_credential_detected"
    UNAUTHORIZED_ACTION = "unauthorized_action"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    COST_LIMIT_EXCEEDED = "cost_limit_exceeded"


class AgentStatusType(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class BaseEvent(BaseModel):
    """
    Root event model. All AECP events extend this.
    Matches base-event.schema.json in common/schema/.
    """

    event_id: str = Field(default_factory=_new_uuid)
    event_type: EventType
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=_utcnow)
    correlation_id: str = Field(default_factory=_new_uuid)

    model_config = {"use_enum_values": True}

    def to_json(self) -> str:
        return self.model_dump_json()
