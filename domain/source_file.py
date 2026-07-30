from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceFile:
    id: str
    filename: str
    platform: str
    report_type: str
    uploaded_at: date | None = None
    original_filename: str | None = None
