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
        "Transaction Date": "2026-01-17 15:00:00",
        "Category": category,
        "Details": details,
        "Amount": amount,
    }


def _metrics(rows: list[dict[str, object]]) -> dict:
    result = ImportService().run_toters_import(
        dataframe=pd.DataFrame(rows),
        restaurant_name="Regression Restaurant",
        platform="Toters",
    )
    return result.metrics


def test_full_order_reversal_offsets_original_costs() -> None:
    rows = [
        # Valid active customer order.
        _row(
            "active-gross",
            "Gross App Revenue",
            "100000",
            order_code="active-1",
            details="Payment for order active-1",
        ),
        _row(
            "active-fee",
            "Store Listing Fee",
            "-25000",
            order_code="active-1",
            details="Service fee for order active-1",
        ),
        _row(
            "active-marketing",
            "Marketing Immediate Discount",
            "-10000",
            order_code="active-1",
            details="marketing cost for order active-1",
        ),
        _row(
            "active-vat",
            "Value Added Tax",
            "-2750",
            order_code="active-1",
            details="VAT for order active-1",
        ),

        # Second order later fully reversed.
        _row(
            "cancel-gross",
            "Gross App Revenue",
            "120000",
            order_code="cancelled-1",
            details="Payment for order cancelled-1",
        ),
        _row(
            "cancel-fee",
            "Store Listing Fee",
            "-30000",
            order_code="cancelled-1",
            details="Service fee for order cancelled-1",
        ),
        _row(
            "cancel-marketing",
            "Marketing Immediate Discount",
            "-12000",
            order_code="cancelled-1",
            details="marketing cost for order cancelled-1",
        ),
        _row(
            "cancel-vat",
            "Value Added Tax",
            "-3300",
            order_code="cancelled-1",
            details="VAT for order cancelled-1",
        ),
        _row(
            "reverse-gross",
            "Gross App Revenue",
            "-120000",
            order_code="cancelled-1",
            details=(
                "Payment deduction for wrong/missing items "
                "in order cancelled-1"
            ),
        ),
        _row(
            "reverse-fee",
            "Store Listing Fee",
            "30000",
            order_code="cancelled-1",
            details=(
                "Service fee deduction for wrong/missing items "
                "in order cancelled-1"
            ),
        ),
        _row(
            "reverse-marketing",
            "Marketing Immediate Discount",
            "12000",
            order_code="cancelled-1",
            details=(
                "Marketing cost deduction for wrong/missing items "
                "in order cancelled-1"
            ),
        ),
        _row(
            "reverse-vat",
            "Value Added Tax",
            "3300",
            order_code="cancelled-1",
            details=(
                "VAT adjustment for wrong/missing items "
                "in order cancelled-1"
            ),
        ),
    ]

    metrics = _metrics(rows)

    assert metrics["total_orders"] == 1
    assert metrics["gross_revenue"] == pytest.approx(100000.0)
    assert metrics["total_listing_fee"] == pytest.approx(25000.0)
    assert metrics["total_marketing_discount"] == pytest.approx(10000.0)
    assert metrics["total_marketing_cost"] == pytest.approx(10000.0)
    assert metrics["total_vat"] == pytest.approx(2750.0)
    assert metrics["total_platform_cost"] == pytest.approx(37750.0)
    assert metrics["net_order_revenue"] == pytest.approx(62250.0)


def test_account_level_marketing_credit_and_vat_reduce_platform_cost() -> None:
    rows = [
        _row(
            "gross",
            "Gross App Revenue",
            "100000",
            order_code="order-1",
            details="Payment for order order-1",
        ),
        _row(
            "fee",
            "Store Listing Fee",
            "-25000",
            order_code="order-1",
            details="Service fee for order order-1",
        ),
        _row(
            "marketing",
            "Marketing Immediate Discount",
            "-10000",
            order_code="order-1",
            details="marketing cost for order order-1",
        ),
        _row(
            "vat",
            "Value Added Tax",
            "-2750",
            order_code="order-1",
            details="VAT for order order-1",
        ),
        _row(
            "marketing-credit",
            "Marketing Credit Note",
            "4000",
            order_code=None,
            details="Marketing fees covered by Toters",
        ),
        _row(
            "marketing-credit-vat",
            "Value Added Tax",
            "440",
            order_code=None,
            details="VAT for Marketing fees covered by Toters",
        ),
    ]

    metrics = _metrics(rows)

    assert metrics["total_orders"] == 1
    assert metrics["gross_revenue"] == pytest.approx(100000.0)

    assert metrics["total_marketing_credit_note"] == pytest.approx(
        -4000.0
    )
    assert metrics["total_marketing_cost"] == pytest.approx(6000.0)

    assert metrics["vat_on_listing_fees"] == pytest.approx(2750.0)
    assert metrics["vat_on_marketing_credit_note"] == pytest.approx(
        440.0
    )
    assert metrics["vat_on_marketing"] == pytest.approx(-440.0)
    assert metrics["total_vat"] == pytest.approx(2310.0)

    assert metrics["total_platform_cost"] == pytest.approx(33310.0)
    assert metrics["net_order_revenue"] == pytest.approx(66690.0)
