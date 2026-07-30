from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    restaurant_id: str | None = None
    name: str | None = None
    code: str | None = None
