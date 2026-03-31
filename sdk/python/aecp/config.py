from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AgentConfig:
    """
    Configuration for an AECP-instrumented agent.
    Fields are immutable after construction — copy and replace for variants.

    Minimal required fields: agent_id, version, owner.
    All other fields have sensible defaults for local development.
    """

    # Agent identity
    agent_id: str
    version: str
    owner: str
    capabilities: list[str] = field(default_factory=list)
    permissions_requested: list[str] = field(default_factory=list)
    runtime: str = "python"

    # Control Plane connectivity
    control_plane_url: str = "http://localhost:8080"
    control_plane_timeout_seconds: float = 5.0

    # MQ Publisher
    publisher_type: Literal["kafka", "inmemory"] = "inmemory"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "aecp.events"
    kafka_dlq_topic: str = "aecp.events.dlq"

    # Heartbeat
    heartbeat_interval_seconds: float = 30.0
