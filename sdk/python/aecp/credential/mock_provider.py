from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .base import CredentialProvider
from .token import Token

# Predictable token values keyed by service name.
# These are safe for local dev/testing — never production values.
_SERVICE_TOKENS: dict[str, str] = {
    "jira": "svc-jira-mock-abc123",
    "openai": "svc-openai-mock-def456",
    "anthropic": "svc-anthropic-mock-ghi789",
    "aws": "svc-aws-mock-jkl012",
    "github": "svc-github-mock-mno345",
    "default": "svc-default-mock-xyz000",
}


class MockCredentialProvider(CredentialProvider):
    """
    Deterministic mock for local development and testing.

    All returned tokens are marked is_service_account=True with a 1-hour TTL.
    Add entries to _SERVICE_TOKENS above to support additional services.
    """

    def get_service_token(self, service_name: str) -> Token:
        value = _SERVICE_TOKENS.get(service_name, _SERVICE_TOKENS["default"])
        return Token(
            value=value,
            service_name=service_name,
            expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
            is_service_account=True,
        )

    def is_service_account(self, token_hint: str) -> bool:
        return token_hint in _SERVICE_TOKENS.values()
