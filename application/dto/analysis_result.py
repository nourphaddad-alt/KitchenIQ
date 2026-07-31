from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from connectors.base.import_result import ImportOutcome, ImportResult
from domain.financial_event import FinancialEvent


@dataclass(frozen=True)
class AnalysisResult:
    restaurant_name: str
    platform: str
    import_result: ImportResult
    outcome: ImportOutcome = ImportOutcome.SUCCESS
    records: list[FinancialEvent] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
