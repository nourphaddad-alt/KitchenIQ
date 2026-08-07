from __future__ import annotations

import pandas as pd
import pytest

from application.services.import_service import ImportService


def _row(
    activity_id: str,
    category: str,
    amount: str,
    *,
    order_code: str | None,
    details: str,
) -> dict[str, object]:
    return {
        "ID": activity_id,
        "Order Code": order_code,
        "Transaction Date": "2026-03-01 12:30:00",
        "Category": category,
        "Details": details,
        "Amount": amount,
    }


def test_import_rejects_unrouted_account_level_event() -> None:
    dataframe = pd.DataFrame([
        _row(
            "gross-1",
            "Gross App Revenue",
            "100000",
            order_code="order-1",
            details="Payment for order order-1",
        ),
        _row(
            "orphan-fee",
            "Store Listing Fee",
            "-25000",
            order_code=None,
            details="Platform service fee without order reference",
        ),
    ])

    with pytest.raises(
        ValueError,
        match=(
            "financial routing failure: "
            "account-level event type 'platform_commission'"
        ),
    ):
        ImportService().run_toters_import(
            dataframe=dataframe,
            restaurant_name="Routing Test",
            platform="Toters",
        )


def test_import_rejects_account_event_attached_to_order() -> None:
    dataframe = pd.DataFrame([
        _row(
            "gross-1",
            "Gross App Revenue",
            "100000",
            order_code="order-1",
            details="Payment for order order-1",
        ),
        _row(
            "invalid-marketing-vat",
            "Value Added Tax",
            "-1100",
            order_code="order-1",
            details="VAT for Marketing Highlight top-up",
        ),
    ])

    with pytest.raises(
        ValueError,
        match=(
            "financial routing failure: "
            "order-linked event type 'vat_marketing_highlight'"
        ),
    ):
        ImportService().run_toters_import(
            dataframe=dataframe,
            restaurant_name="Routing Test",
            platform="Toters",
        )
