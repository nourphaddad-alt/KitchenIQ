from __future__ import annotations

import pandas as pd
import pytest

from application.services.import_service import ImportService


def _row(
    activity_id: str,
    category: str,
    amount: str,
    *,
    order_code: str | None = None,
    details: str = "",
) -> dict[str, object]:
    return {
        "ID": activity_id,
        "Order Code": order_code,
        "Transaction Date": "2026-03-01 12:00:00",
        "Category": category,
        "Details": details,
        "Amount": amount,
    }


def test_account_level_marketing_reversals_preserve_sign() -> None:
    dataframe = pd.DataFrame([
        _row(
            "gross-1",
            "Gross App Revenue",
            "100000",
            order_code="order-1",
            details="Payment for order",
        ),
        _row(
            "highlight-charge",
            "Marketing Highlight",
            "-10000",
        ),
        _row(
            "highlight-reversal",
            "Marketing Highlight",
            "4000",
        ),
        _row(
            "credit-note",
            "Marketing Credit Note",
            "4000",
            details="Marketing fees covered by Toters",
        ),
        _row(
            "credit-reversal",
            "Marketing Credit Note",
            "-1000",
            details="Marketing fees covered by Toters",
        ),
    ])

    metrics = ImportService().run_toters_import(
        dataframe=dataframe,
        restaurant_name="Sign Test",
    ).metrics

    assert metrics["total_marketing_highlight"] == pytest.approx(6000.0)
    assert metrics["total_marketing_credit_note"] == pytest.approx(3000.0)
    assert metrics["net_marketing_highlight"] == pytest.approx(6000.0)

    assert metrics["discount_promotion_spend"] == pytest.approx(
        0.0
    )

    assert (
        metrics["discount_promotion_spend"]
        + metrics["net_marketing_highlight"]
        - metrics["total_marketing_credit_note"]
    ) == pytest.approx(3000.0)

    assert metrics["fully_loaded_promotion_cost"] == pytest.approx(
        0.0
    )
    assert metrics["total_marketing_cost"] == pytest.approx(3000.0)
    assert metrics["total_platform_cost"] == pytest.approx(3000.0)
    assert metrics["net_order_revenue"] == pytest.approx(97000.0)


def test_account_level_highlight_credit_reversal_preserves_sign() -> None:
    dataframe = pd.DataFrame([
        _row(
            "gross-1",
            "Gross App Revenue",
            "100000",
            order_code="order-1",
            details="Payment for order",
        ),
        _row(
            "highlight-charge",
            "Marketing Highlight",
            "-10000",
        ),
        _row(
            "highlight-credit",
            "Marketing Highlights Credit Note",
            "2000",
        ),
        _row(
            "highlight-credit-reversal",
            "Marketing Highlights Credit Note",
            "-500",
        ),
    ])

    metrics = ImportService().run_toters_import(
        dataframe=dataframe,
        restaurant_name="Highlight Credit Test",
    ).metrics

    assert metrics["total_marketing_highlight"] == pytest.approx(10000.0)
    assert metrics["total_marketing_highlight_credit_note"] == pytest.approx(
        1500.0
    )
    assert metrics["net_marketing_highlight"] == pytest.approx(8500.0)
    assert metrics["total_marketing_cost"] == pytest.approx(8500.0)
    assert metrics["total_platform_cost"] == pytest.approx(8500.0)
    assert metrics["net_order_revenue"] == pytest.approx(91500.0)
