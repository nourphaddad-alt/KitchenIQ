from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class FinancialEvent:
    source_row_number: int
    source_activity_id: str
    order_code: str | None
    occurred_at: datetime
    source_category: str
    event_type: str
    signed_amount: Decimal
    currency: str
    mapping_status: str
    confidence: str
    details: str | None = None