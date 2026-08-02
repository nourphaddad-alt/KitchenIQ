from __future__ import annotations

import pandas as pd

from domain.financial_event import FinancialEvent


_MARKETING_EVENT_TYPES = {
    "marketing_fixed_price",
    "marketing_discount",
    "marketing_free_delivery",
    "marketing_punch_card",
    "marketing_highlight",
    "marketing_credit_note",
    "marketing_highlight_credit_note",
}


_MARKETING_COLUMN_BY_EVENT_TYPE = {
    "marketing_discount": "marketing_discount",
    "marketing_fixed_price": "marketing_fixed_price",
    "marketing_free_delivery": "marketing_free_delivery",
    "marketing_punch_card": "marketing_punch_card",
    "marketing_highlight": "marketing_highlight",
    "marketing_credit_note": "marketing_credit_note",
    "marketing_highlight_credit_note": (
        "marketing_highlight_credit_note"
    ),
}


_CREDIT_EVENT_TYPES = {
    "marketing_credit_note",
    "marketing_highlight_credit_note",
}


_EXCLUDED_FROM_ORDERS = {
    "settlement",
}


CONSOLIDATED_ORDER_COLUMNS = [
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


def _cost_contribution(event: FinancialEvent) -> float:
    """
    Normalize the sign of one cost-type event.

    Ordinary deductions are stored as positive cost magnitudes.
    Credit and reversal events preserve their original sign so they
    reduce the related marketing cost rather than increase it.
    """
    amount = float(event.signed_amount)

    if event.event_type in _CREDIT_EVENT_TYPES:
        return amount

    return abs(amount)


def _empty_order(
    order_reference: str,
    occurred_at,
) -> dict[str, object]:
    """
    Create the canonical mutable accumulator for one Toters order.
    """
    return {
        "order_id": order_reference,
        "order_date": occurred_at,
        "gross_revenue": 0.0,
        "store_listing_fee": 0.0,
        "marketing_discount": 0.0,
        "marketing_fixed_price": 0.0,
        "marketing_free_delivery": 0.0,
        "marketing_punch_card": 0.0,
        "marketing_highlight": 0.0,
        "marketing_credit_note": 0.0,
        "marketing_highlight_credit_note": 0.0,
        "vat": 0.0,
        "courier_cost": 0.0,
    }


def consolidate_orders(
    records: list[FinancialEvent],
) -> pd.DataFrame:
    """
    Group canonical FinancialEvents into exactly one row per order.

    Detailed marketing event values are preserved in dedicated columns.
    The legacy total_marketing_cost field remains available as the sum
    of those detailed columns.

    Settlement events and records without an order reference are
    excluded because they cannot be attributed to one customer order.
    """
    orders: dict[str, dict[str, object]] = {}

    for record in records:
        if record.event_type in _EXCLUDED_FROM_ORDERS:
            continue

        order_reference = record.order_reference

        if not order_reference:
            continue

        order = orders.setdefault(
            order_reference,
            _empty_order(
                order_reference,
                record.occurred_at,
            ),
        )

        order["order_date"] = min(
            order["order_date"],
            record.occurred_at,
        )

        if record.event_type == "gross_revenue":
            order["gross_revenue"] += float(
                record.signed_amount
            )

        elif record.event_type == "platform_commission":
            order["store_listing_fee"] += (
                _cost_contribution(record)
            )

        elif record.event_type in _MARKETING_EVENT_TYPES:
            marketing_column = (
                _MARKETING_COLUMN_BY_EVENT_TYPE[
                    record.event_type
                ]
            )

            order[marketing_column] += (
                _cost_contribution(record)
            )

        elif record.event_type == "vat_order":
            order["vat"] += _cost_contribution(record)

        elif record.event_type == "courier_cost":
            order["courier_cost"] += (
                _cost_contribution(record)
            )

    rows: list[dict[str, object]] = []

    for order in orders.values():
        total_marketing_cost = sum(
            float(order[column])
            for column in _MARKETING_COLUMN_BY_EVENT_TYPE.values()
        )

        total_platform_cost = (
            float(order["store_listing_fee"])
            + total_marketing_cost
            + float(order["vat"])
            + float(order["courier_cost"])
        )

        rows.append(
            {
                "order_id": order["order_id"],
                "order_date": order["order_date"],
                "gross_revenue": order["gross_revenue"],
                "store_listing_fee": (
                    order["store_listing_fee"]
                ),
                "marketing_discount": (
                    order["marketing_discount"]
                ),
                "marketing_fixed_price": (
                    order["marketing_fixed_price"]
                ),
                "marketing_free_delivery": (
                    order["marketing_free_delivery"]
                ),
                "marketing_punch_card": (
                    order["marketing_punch_card"]
                ),
                "marketing_highlight": (
                    order["marketing_highlight"]
                ),
                "marketing_credit_note": (
                    order["marketing_credit_note"]
                ),
                "marketing_highlight_credit_note": (
                    order[
                        "marketing_highlight_credit_note"
                    ]
                ),
                "total_marketing_cost": (
                    total_marketing_cost
                ),
                "vat": order["vat"],
                "courier_cost": order["courier_cost"],
                "total_platform_cost": (
                    total_platform_cost
                ),
                "net_order_revenue": (
                    float(order["gross_revenue"])
                    - total_platform_cost
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=CONSOLIDATED_ORDER_COLUMNS,
    )
