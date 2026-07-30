from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformAccount:
    id: str
    platform: str
    account_name: str | None = None
    account_code: str | None = None
