from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


class PolicyLoader:
    """
    Loads agent policies from YAML files at startup.

    Each file must contain a top-level `agent_id` key.
    Policy files are named freely — `agent_id` inside is the lookup key.

    Future enhancement: inotify/watchdog-based hot reload for zero-restart
    policy updates. For v1, a service restart is required to pick up changes.
    """

    def __init__(self, policies_dir: Path) -> None:
        self.policies_dir = policies_dir
        self.policies: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        self.policies.clear()

        if not self.policies_dir.exists():
            logger.warning("policies_dir_not_found", path=str(self.policies_dir))
            return

        for path in sorted(self.policies_dir.glob("*.yaml")):
            try:
                with path.open() as f:
                    policy: dict[str, Any] = yaml.safe_load(f)

                agent_id = policy.get("agent_id")
                if not agent_id:
                    logger.warning("policy_missing_agent_id", file=path.name)
                    continue

                self.policies[agent_id] = policy
                logger.info("policy_loaded", agent_id=agent_id, file=path.name)

            except Exception as exc:
                logger.error("policy_load_failed", file=path.name, error=str(exc))

    def get_policy(self, agent_id: str) -> dict[str, Any] | None:
        return self.policies.get(agent_id)
