from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IssueSeverity = Literal["warning", "error", "blocking"]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: IssueSeverity
    source_row_number: int | None = None
    source_field: str | None = None
    source_value: str | None = None
