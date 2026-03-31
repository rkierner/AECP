from __future__ import annotations

from .base import CredentialProvider
from .token import Token


class VaultCredentialProvider(CredentialProvider):
    """
    HashiCorp Vault credential provider (placeholder).

    Implementation steps:
      1. Install hvac: pip install hvac
      2. Authenticate via AppRole:
           client = hvac.Client(url=vault_addr)
           client.auth.approle.login(role_id=role_id, secret_id=secret_id)
      3. Read secret:
           secret = client.secrets.kv.v2.read_secret_version(
               path=f"aecp/{service_name}", mount_point="secret"
           )
           token_value = secret["data"]["data"]["token"]
      4. Extract TTL from Vault lease for expires_at
      5. Return Token(value=token_value, service_name=service_name,
                      expires_at=..., is_service_account=True)

    See: https://developer.hashicorp.com/vault/docs/auth/approle
    See: https://hvac.readthedocs.io/
    """

    def __init__(self, vault_addr: str, role_id: str, secret_id: str | None = None) -> None:
        self.vault_addr = vault_addr
        self.role_id = role_id
        self.secret_id = secret_id
        # TODO: Initialize hvac.Client and authenticate on construction

    def get_service_token(self, service_name: str) -> Token:
        raise NotImplementedError(
            "VaultCredentialProvider is not yet implemented. "
            "See class docstring for step-by-step implementation guidance."
        )

    def is_service_account(self, token_hint: str) -> bool:
        raise NotImplementedError("VaultCredentialProvider is not yet implemented.")
