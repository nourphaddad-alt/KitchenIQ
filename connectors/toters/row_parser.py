from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from domain.financial_event import FinancialEvent
from .mapper import map_category


def parse_decimal(value: object) -> Decimal:
    """
    Convert a Toters financial amount into an exact Decimal value.

    The original sign is preserved.
    """

    if pd.isna(value):
        raise ValueError("Amount is missing.")

    normalized_value = str(value).strip().replace(",", "")

    if not normalized_value:
        raise ValueError("Amount is empty.")

    try:
        return Decimal(normalized_value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {value!r}") from exc


def normalize_optional_text(value: object) -> str | None:
    """
    Convert an optional cell into clean text.

    Blank values become None.
    """

    if pd.isna(value):
        return None

    normalized_value = str(value).strip()

    return normalized_value or None


def parse_datetime(value: object) -> datetime:
    """
    Convert a Toters date value into a Python datetime.

    Raises ValueError when the date is missing or invalid.
    """

    if pd.isna(value):
        raise ValueError("Transaction date is missing.")

    parsed_value = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed_value):
        raise ValueError(f"Invalid transaction date: {value!r}")

    return parsed_value.to_pydatetime()


def parse_invoice_row(
    row: pd.Series,
    source_row_number: int,
    currency: str = "LBP",
) -> FinancialEvent:
    """
    Convert one validated Toters invoice row into one FinancialEvent.
    """

    source_activity_id = normalize_optional_text(row.get("transaction_id"))

    if source_activity_id is None:
        raise ValueError("Source activity ID is missing.")

    source_category = normalize_optional_text(row.get("category"))

    if source_category is None:
        raise ValueError("Category is missing.")

    category_mapping = map_category(source_category)

    if category_mapping is None:
        raise ValueError(f"Unknown category: {source_category!r}")

    return FinancialEvent(
        source_row_number=source_row_number,
        source_activity_id=source_activity_id,
        order_reference=normalize_optional_text(row.get("order_reference")),
        occurred_at=parse_datetime(row.get("transaction_date")),
        source_category=source_category,
        event_type=category_mapping.event_type,
        signed_amount=parse_decimal(row.get("amount")),
        currency=currency,
        mapping_status=category_mapping.mapping_status,
        confidence=category_mapping.confidence,
        details=normalize_optional_text(row.get("details")),
    )