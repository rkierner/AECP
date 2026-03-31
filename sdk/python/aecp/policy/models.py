from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class CostLimits(BaseModel):
    daily_usd: float = Field(ge=0.0, default=100.0)


class RateLimits(BaseModel):
    requests_per_minute: int = Field(ge=1, default=1000)


class CredentialPolicy(BaseModel):
    type: str = "service_account_only"


class Policy(BaseModel):
    """
    Agent policy loaded from YAML.
    Defines what an agent is allowed to do, what credentials it may use,
    and what cost/rate limits apply.
    """

    agent_id: str
    allowed_actions: list[str] = Field(default_factory=list)
    credentials: CredentialPolicy = Field(default_factory=CredentialPolicy)
    cost_limits: CostLimits = Field(default_factory=CostLimits)
    rate_limits: RateLimits = Field(default_factory=RateLimits)

    @classmethod
    def from_yaml(cls, path: Path | str) -> Policy:
        """Load policy from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        """Load policy from a parsed dict (e.g. fetched from Control Plane)."""
        return cls.model_validate(data)

    @classmethod
    def permissive(cls, agent_id: str) -> Policy:
        """
        Creates a fully open policy using wildcard '*'.
        ONLY appropriate for local development or testing.
        """
        return cls(agent_id=agent_id, allowed_actions=["*"])
