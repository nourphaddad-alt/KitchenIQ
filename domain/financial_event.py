from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class FinancialEvent:
    source_row_number: int
    occurred_at: datetime
    source_category: str
    event_type: str
    signed_amount: Decimal
    currency: str
    mapping_status: str
    confidence: str
    financial_event_id: str | None = None
    restaurant_id: str | None = None
    location_id: str | None = None
    platform_account_id: str | None = None
    source_file_id: str | None = None
    import_run_id: str | None = None
    source_activity_id: str | None = None
    order_reference: str | None = None
    settlement_period_start: date | None = None
    settlement_period_end: date | None = None
    details: str | None = None
