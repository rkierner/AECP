from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class ControlPlaneClient:
    """
    HTTP client for the AECP Control Plane REST API.

    All methods are fail-safe: network errors are logged as warnings and
    never propagated. The Control Plane is an enhancement, not a dependency —
    agents must continue functioning even if it is unreachable.

    Uses httpx (sync) for simplicity. For high-throughput agents, swap to
    httpx.AsyncClient within an async context.
    """

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def register_agent(self, event: Any) -> None:
        """POST /agents/register — non-blocking, fail-safe."""
        try:
            import httpx

            payload = {
                "agent_id": event.agent_id,
                "runtime": event.runtime,
                "version": event.version,
                "owner": event.owner,
                "capabilities": list(event.capabilities),
                "permissions_requested": list(event.permissions_requested),
            }
            response = httpx.post(
                f"{self.base_url}/agents/register",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info(
                "control_plane_registration_ok",
                agent_id=event.agent_id,
                status_code=response.status_code,
            )
        except Exception as exc:
            logger.warning(
                "control_plane_register_failed",
                agent_id=getattr(event, "agent_id", "unknown"),
                error=str(exc),
            )

    def get_policy(self, agent_id: str) -> dict[str, Any] | None:
        """GET /policies/{agent_id} — returns None on 404 or network error."""
        try:
            import httpx

            response = httpx.get(
                f"{self.base_url}/policies/{agent_id}",
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning(
                "control_plane_policy_fetch_failed",
                agent_id=agent_id,
                error=str(exc),
            )
            return None

    def report_violation(self, event: Any) -> None:
        """POST /violations — fail-safe, best-effort delivery."""
        try:
            import httpx

            payload = {
                "agent_id": event.agent_id,
                "violation_type": str(event.violation_type),
                "severity": str(event.severity),
                "details": dict(event.details),
                "correlation_id": event.correlation_id,
            }
            response = httpx.post(
                f"{self.base_url}/violations",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning(
                "control_plane_violation_report_failed",
                agent_id=getattr(event, "agent_id", "unknown"),
                error=str(exc),
            )
