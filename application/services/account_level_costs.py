from __future__ import annotations

from collections import defaultdict

from domain.financial_event import FinancialEvent


def aggregate_account_level_costs(
    records: list[FinancialEvent],
) -> dict[str, float]:
    """
    Aggregate platform-level financial events that are not linked
    to an individual customer order.

    These costs affect restaurant profitability but must never
    increase customer-order metrics.
    """
    totals: defaultdict[str, float] = defaultdict(float)

    for record in records:
        if record.order_reference:
            continue

        if record.event_type == "settlement":
            continue

        signed_amount = float(record.signed_amount)

        if record.event_type == "marketing_highlight":
            totals["marketing_highlight"] += -signed_amount

        elif record.event_type == "marketing_credit_note":
            totals["marketing_credit_note"] += signed_amount

        elif record.event_type == "vat_marketing_highlight":
            totals["vat_marketing_highlight"] += -signed_amount

        elif record.event_type == "vat_marketing_credit_note":
            totals["vat_marketing_credit_note"] += signed_amount

        elif record.event_type == "marketing_highlight_credit_note":
            totals["marketing_highlight_credit_note"] += signed_amount

        else:
            raise ValueError(
                "Toters financial routing failure: "
                "account-level event type "
                f"{record.event_type!r} has no account-ledger handler "
                f"(source row {record.source_row_number})."
            )

    return dict(totals)
