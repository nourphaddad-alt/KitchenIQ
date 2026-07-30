from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthScore:
    score: int
    label: str
    interpretation: str
