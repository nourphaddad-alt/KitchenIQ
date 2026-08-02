from datetime import datetime
from decimal import Decimal

from application.services.account_level_costs import (
    aggregate_account_level_costs,
)
from domain.financial_event import FinancialEvent


def _event(**overrides: object) -> FinancialEvent:
    values = {
        "source_row_number": 1,
        "occurred_at": datetime(2026, 3, 1),
        "source_category": "",
        "event_type": "",
        "signed_amount": Decimal("100"),
        "currency": "LBP",
        "mapping_status": "validated",
        "confidence": "confirmed",
        "order_reference": None,
    }

    values.update(overrides)

    return FinancialEvent(**values)


def test_aggregates_account_level_highlight_costs() -> None:
    result = aggregate_account_level_costs(
        [
            _event(
                event_type="marketing_highlight",
                signed_amount=Decimal("-1000"),
            ),
            _event(
                event_type="vat_marketing_highlight",
                signed_amount=Decimal("-110"),
            ),
            _event(
                event_type="settlement",
                signed_amount=Decimal("5000"),
            ),
        ]
    )

    assert result == {
        "marketing_highlight": 1000.0,
        "vat_marketing_highlight": 110.0,
    }


def test_ignores_order_level_events() -> None:
    result = aggregate_account_level_costs(
        [
            _event(
                event_type="marketing_highlight",
                order_reference="order-1001",
                signed_amount=Decimal("-1000"),
            )
        ]
    )

    assert result == {}
