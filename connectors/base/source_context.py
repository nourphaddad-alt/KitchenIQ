from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceContext:
    platform: str
    report_type: str
    restaurant_id: str | None = None
    location_id: str | None = None
    currency: str = "LBP"
    period_start: date | None = None
    period_end: date | None = None
    original_filename: str | None = None
