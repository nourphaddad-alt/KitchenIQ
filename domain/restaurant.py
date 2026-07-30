from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Restaurant:
    id: str
    name: str | None = None
    code: str | None = None
