from __future__ import annotations

from dataclasses import dataclass, field

from .financial_event import FinancialEvent


@dataclass
class ImportResult:
    events: list[FinancialEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    unknown_categories: list[str] = field(default_factory=list)
    rows_processed: int = 0