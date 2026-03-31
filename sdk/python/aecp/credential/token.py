from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Token:
    """
    Immutable credential token obtained from a CredentialProvider.
    Never constructed directly by agent code.
    """

    value: str
    service_name: str
    expires_at: datetime
    is_service_account: bool
