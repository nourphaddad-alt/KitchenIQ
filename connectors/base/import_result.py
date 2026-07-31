from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .validation_issue import ValidationIssue


class ImportOutcome(str, Enum):
    """
    The only three outcomes an import may finish with.

    No pipeline stage may treat an import as successful unless
    the outcome is explicitly SUCCESS or PARTIAL_SUCCESS.
    """

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


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
    def has_error_issues(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def is_successful(self) -> bool:
        return not self.has_blocking_issues and not self.has_error_issues

    @property
    def outcome(self) -> ImportOutcome:
        """
        FAILED whenever schema validation blocked the import, or zero
        FinancialEvents were produced (Rule 3): an import with no records
        can never be presented as successful, even if no rows errored.
        """
        if self.has_blocking_issues or not self.records:
            return ImportOutcome.FAILED
        if self.has_error_issues:
            return ImportOutcome.PARTIAL_SUCCESS
        return ImportOutcome.SUCCESS
