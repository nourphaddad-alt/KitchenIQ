from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from application.services.order_consolidation import consolidate_orders
from domain.financial_event import FinancialEvent


def _event(**overrides: object) -> FinancialEvent:
    fields = {
        "source_row_number": 2,
        "occurred_at": datetime(2026, 3, 1, 12, 30),
        "source_category": "Gross App Revenue",
        "event_type": "gross_revenue",
        "signed_amount": Decimal("150000"),
        "currency": "LBP",
        "mapping_status": "validated",
        "confidence": "confirmed",
        "order_reference": "order-1001",
    }
    fields.update(overrides)
    return FinancialEvent(**fields)


def test_consolidate_orders_returns_empty_dataframe_for_no_records() -> None:
    result = consolidate_orders([])

    assert result.empty
    assert list(result.columns) == [
        "order_id",
        "order_date",
        "gross_revenue",
        "store_listing_fee",
        "total_marketing_cost",
        "vat",
        "total_platform_cost",
        "net_order_revenue",
    ]


def test_consolidate_orders_groups_multiple_events_into_one_order() -> None:
    records = [
        _event(source_row_number=2, event_type="gross_revenue", signed_amount=Decimal("150000")),
        _event(
            source_row_number=3,
            source_category="Store Listing Fee",
            event_type="platform_commission",
            signed_amount=Decimal("15000"),
        ),
        _event(
            source_row_number=4,
            source_category="Value Added Tax",
            event_type="vat",
            signed_amount=Decimal("5000"),
        ),
    ]

    result = consolidate_orders(records)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["order_id"] == "order-1001"
    assert row["gross_revenue"] == 150000.0
    assert row["store_listing_fee"] == 15000.0
    assert row["vat"] == 5000.0
    assert row["total_platform_cost"] == 20000.0
    assert row["net_order_revenue"] == 130000.0


def test_consolidate_orders_excludes_settlement_events() -> None:
    records = [
        _event(order_reference="order-1001"),
        _event(
            source_row_number=3,
            source_category="Balance Settlement",
            event_type="settlement",
            signed_amount=Decimal("130000"),
            order_reference=None,
        ),
    ]

    result = consolidate_orders(records)

    assert len(result) == 1
    assert result.iloc[0]["order_id"] == "order-1001"


def test_consolidate_orders_excludes_events_without_order_reference() -> None:
    records = [_event(order_reference=None)]

    result = consolidate_orders(records)

    assert result.empty


def test_consolidate_orders_preserves_credit_note_sign() -> None:
    records = [
        _event(),
        _event(
            source_row_number=3,
            source_category="Marketing Item Fixed Price",
            event_type="marketing_fixed_price",
            signed_amount=Decimal("10000"),
        ),
        _event(
            source_row_number=4,
            source_category="Marketing Credit Note",
            event_type="marketing_credit_note",
            signed_amount=Decimal("-4000"),
        ),
    ]

    result = consolidate_orders(records)

    assert len(result) == 1
    # 10000 charged, then a 4000 credit reduces total marketing cost.
    assert result.iloc[0]["total_marketing_cost"] == 6000.0


def test_consolidate_orders_normalizes_negative_cost_amounts() -> None:
    records = [
        _event(),
        _event(
            source_row_number=3,
            source_category="Store Listing Fee",
            event_type="platform_commission",
            signed_amount=Decimal("-15000"),
        ),
    ]

    result = consolidate_orders(records)

    assert result.iloc[0]["store_listing_fee"] == 15000.0
