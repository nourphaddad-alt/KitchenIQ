from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .validation_issue import ValidationIssue


@dataclass
class ImportResult:
    records: list[Any] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    rows_received: int = 0
    rows_parsed: int = 0
    connector_code: str = ""
    connector_version: str = ""
    mapping_version: str = ""

    @property
    def has_blocking_issues(self) -> bool:
        return any(issue.severity == "blocking" for issue in self.issues)

    @property
    def is_successful(self) -> bool:
        return not self.has_blocking_issues and not any(
            issue.severity == "error" for issue in self.issues
        )
