from __future__ import annotations

from ..credential.token import Token
from .models import Policy


class PolicyViolationError(Exception):
    """
    Raised when an agent attempts a policy-prohibited operation.
    Carries machine-readable violation_type and severity for SecurityEvent emission.
    """

    def __init__(self, message: str, violation_type: str, severity: str = "HIGH") -> None:
        super().__init__(message)
        self.violation_type = violation_type
        self.severity = severity


class PolicyEnforcer:
    """
    Stateless policy enforcer.

    Validates actions and credentials against the agent's registered Policy.
    The SDK calls this before every action — enforcement happens at the call site,
    not in a central gateway, for minimal latency and maximum reliability.
    """

    def __init__(self, policy: Policy) -> None:
        self.policy = policy

    def enforce_action(self, action: str) -> None:
        """
        Raise PolicyViolationError if the action is not in the allowlist.
        Wildcard '*' grants all actions — use only in dev/test.
        """
        allowed = self.policy.allowed_actions
        if "*" in allowed or action in allowed:
            return
        raise PolicyViolationError(
            message=(
                f"Action '{action}' is not permitted for agent '{self.policy.agent_id}'. "
                f"Allowed: {allowed}"
            ),
            violation_type="unauthorized_action",
            severity="HIGH",
        )

    def enforce_credential(self, token: Token) -> None:
        """Raise PolicyViolationError if the token is not a service account credential."""
        if not token.is_service_account:
            raise PolicyViolationError(
                message=(
                    "User credentials detected. Only service account tokens are permitted. "
                    "Use a CredentialProvider to obtain service tokens."
                ),
                violation_type="user_credential_detected",
                severity="CRITICAL",
            )

    def check_cost_threshold(self, accumulated_cost_usd: float) -> bool:
        """
        Returns True if accumulated cost is within the daily limit.
        Returns False (does NOT raise) — caller decides whether to block.
        """
        return accumulated_cost_usd <= self.policy.cost_limits.daily_usd
