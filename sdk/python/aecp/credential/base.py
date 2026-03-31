from __future__ import annotations

from abc import ABC, abstractmethod

from .token import Token


class CredentialProvider(ABC):
    """
    Abstraction over secret stores (HashiCorp Vault, AWS IAM, GCP Workload Identity, etc.).

    All credentials must flow through a registered CredentialProvider.
    Agents must never inject raw token strings — the SDK actively blocks this
    and emits a CRITICAL SecurityEvent if a violation is detected.
    """

    @abstractmethod
    def get_service_token(self, service_name: str) -> Token:
        """
        Retrieve a service account token for the given service.

        Args:
            service_name: Logical service identifier (e.g. 'jira', 'openai', 'aws-s3').

        Returns:
            A Token with is_service_account=True.

        Raises:
            RuntimeError: If the provider cannot resolve a token (e.g. Vault unreachable).
        """
        ...

    @abstractmethod
    def is_service_account(self, token_hint: str) -> bool:
        """
        Returns True if the given token value is a known service account credential.
        Used by the SDK to detect accidental user credential injection.
        """
        ...
