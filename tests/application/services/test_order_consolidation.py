from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

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
        "marketing_discount",
        "marketing_fixed_price",
        "marketing_free_delivery",
        "marketing_punch_card",
        "marketing_highlight",
        "marketing_credit_note",
        "marketing_highlight_credit_note",
        "total_marketing_cost",
        "vat",
        "courier_cost",
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
            event_type="vat_order",
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


@pytest.mark.parametrize(
    (
        "event_type",
        "source_category",
        "column_name",
        "signed_amount",
        "expected_value",
    ),
    [
        (
            "marketing_discount",
            "Marketing Immediate Discount",
            "marketing_discount",
            Decimal("10000"),
            10000.0,
        ),
        (
            "marketing_fixed_price",
            "Marketing Item Fixed Price",
            "marketing_fixed_price",
            Decimal("12000"),
            12000.0,
        ),
        (
            "marketing_free_delivery",
            "Marketing Free Delivery",
            "marketing_free_delivery",
            Decimal("7000"),
            7000.0,
        ),
        (
            "marketing_punch_card",
            "Marketing Punch Card",
            "marketing_punch_card",
            Decimal("8000"),
            8000.0,
        ),
        (
            "marketing_highlight",
            "Marketing Highlight",
            "marketing_highlight",
            Decimal("9000"),
            9000.0,
        ),
        (
            "marketing_credit_note",
            "Marketing Credit Note",
            "marketing_credit_note",
            Decimal("-4000"),
            -4000.0,
        ),
        (
            "marketing_highlight_credit_note",
            "Marketing Highlights Credit Note",
            "marketing_highlight_credit_note",
            Decimal("-3000"),
            -3000.0,
        ),
    ],
)
def test_consolidate_orders_preserves_each_marketing_event_type(
    event_type: str,
    source_category: str,
    column_name: str,
    signed_amount: Decimal,
    expected_value: float,
) -> None:
    records = [
        _event(),
        _event(
            source_row_number=3,
            source_category=source_category,
            event_type=event_type,
            signed_amount=signed_amount,
        ),
    ]

    result = consolidate_orders(records)

    assert len(result) == 1

    row = result.iloc[0]

    assert row[column_name] == expected_value
    assert row["total_marketing_cost"] == expected_value
