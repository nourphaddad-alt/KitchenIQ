from __future__ import annotations

import pandas as pd

from domain.financial_event import FinancialEvent

# Event types that make up a marketing deduction on an order.
_MARKETING_EVENT_TYPES = {
    "marketing_fixed_price",
    "marketing_discount",
    "marketing_free_delivery",
    "marketing_punch_card",
    "marketing_highlight",
    "marketing_credit_note",
    "marketing_highlight_credit_note",
}

# Credit/reversal event types keep their original sign so they can
# offset previously charged costs instead of being added on top of them.
_CREDIT_EVENT_TYPES = {
    "marketing_credit_note",
    "marketing_highlight_credit_note",
}

# Event types that are period-level reconciliations, not order economics.
# They must never be attributed to an order or increase the order count.
_EXCLUDED_FROM_ORDERS = {"settlement"}

CONSOLIDATED_ORDER_COLUMNS = [
    "order_id",
    "order_date",
    "gross_revenue",
    "store_listing_fee",
    "total_marketing_cost",
    "vat",
    "total_platform_cost",
    "net_order_revenue",
]


def _cost_contribution(event: FinancialEvent) -> float:
    """
    Normalize the sign of one cost-type event explicitly.

    Ordinary deductions are recorded as magnitudes owed by the restaurant.
    Credit/reversal event types are the exception: their original sign is
    preserved so they can reduce, rather than inflate, total cost.
    """
    amount = float(event.signed_amount)

    if event.event_type in _CREDIT_EVENT_TYPES:
        return amount

    return abs(amount)


def consolidate_orders(records: list[FinancialEvent]) -> pd.DataFrame:
    """
    Group canonical FinancialEvents into exactly one row per order.

    Every recognised event type contributes to its order. Settlement
    events and events without an order reference are excluded because
    they cannot be attributed to a single consolidated order.
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
            {
                "order_id": order_reference,
                "order_date": record.occurred_at,
                "gross_revenue": 0.0,
                "store_listing_fee": 0.0,
                "total_marketing_cost": 0.0,
                "vat": 0.0,
                "courier_cost": 0.0,
            },
        )

        order["order_date"] = min(order["order_date"], record.occurred_at)

        if record.event_type == "gross_revenue":
            order["gross_revenue"] += float(record.signed_amount)
        elif record.event_type == "platform_commission":
            order["store_listing_fee"] += _cost_contribution(record)
        elif record.event_type in _MARKETING_EVENT_TYPES:
            order["total_marketing_cost"] += _cost_contribution(record)
        elif record.event_type == "vat":
            order["vat"] += _cost_contribution(record)
        elif record.event_type == "courier_cost":
            order["courier_cost"] += _cost_contribution(record)

    rows = []

    for order in orders.values():
        total_platform_cost = (
            order["store_listing_fee"]
            + order["total_marketing_cost"]
            + order["vat"]
            + order["courier_cost"]
        )

        rows.append(
            {
                "order_id": order["order_id"],
                "order_date": order["order_date"],
                "gross_revenue": order["gross_revenue"],
                "store_listing_fee": order["store_listing_fee"],
                "total_marketing_cost": order["total_marketing_cost"],
                "vat": order["vat"],
                "total_platform_cost": total_platform_cost,
                "net_order_revenue": order["gross_revenue"] - total_platform_cost,
            }
        )

    return pd.DataFrame(rows, columns=CONSOLIDATED_ORDER_COLUMNS)
