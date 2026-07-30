from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .validation_issue import ValidationIssue


@dataclass(frozen=True)
class ImportRun:
    id: str
    started_at: datetime
    completed_at: datetime | None = None
    connector_code: str | None = None
    connector_version: str | None = None
    mapping_version: str | None = None
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)
