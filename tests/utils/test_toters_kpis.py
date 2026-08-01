import pandas as pd

from utils.toters_kpis import calculate_toters_kpis


def _base_row(**overrides: object) -> dict:
    row = {
        "order_id": "order-1001",
        "order_date": "2026-03-01 12:30:00",
        "gross_revenue": 100000.0,
        "store_listing_fee": 25000.0,
        "total_marketing_cost": 27000.0,
        "vat": 5000.0,
        "total_platform_cost": 57000.0,
        "net_order_revenue": 43000.0,
        "marketing_discount": 10000.0,
        "marketing_fixed_price": 12000.0,
        "marketing_free_delivery": 3000.0,
        "marketing_punch_card": 2000.0,
        "marketing_highlight": 4000.0,
        "marketing_credit_note": -3000.0,
        "marketing_highlight_credit_note": -1000.0,
    }
    row.update(overrides)
    return row


def test_calculate_toters_kpis_preserves_marketing_breakdown() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["total_marketing_discount"] == 10000.0
    assert result["total_marketing_fixed_price"] == 12000.0
    assert result["total_marketing_free_delivery"] == 3000.0
    assert result["total_marketing_punch_card"] == 2000.0
    assert result["total_marketing_highlight"] == 4000.0
    assert result["total_marketing_credit_note"] == -3000.0
    assert (
        result["total_marketing_highlight_credit_note"]
        == -1000.0
    )


def test_calculate_toters_kpis_calculates_promotion_totals() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["gross_promotion_spend"] == 31000.0
    assert result["promotion_credits"] == 4000.0
    assert result["net_promotion_spend"] == 27000.0
    assert result["total_marketing_cost"] == 27000.0


def test_calculate_toters_kpis_supports_legacy_data() -> None:
    legacy_row = _base_row()

    for column in [
        "marketing_discount",
        "marketing_fixed_price",
        "marketing_free_delivery",
        "marketing_punch_card",
        "marketing_highlight",
        "marketing_credit_note",
        "marketing_highlight_credit_note",
    ]:
        legacy_row.pop(column)

    result = calculate_toters_kpis(
        pd.DataFrame([legacy_row])
    )

    assert result["total_marketing_cost"] == 27000.0
    assert result["gross_promotion_spend"] == 0.0
    assert result["promotion_credits"] == 0.0
    assert result["net_promotion_spend"] == 0.0


def test_calculate_toters_kpis_calculates_commission_by_promotion_type() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["listing_fee_rate"] == 0.25
    assert result["commission_on_marketing_discount"] == 2500.0
    assert result["commission_on_marketing_fixed_price"] == 3000.0
    assert result["commission_on_marketing_free_delivery"] == 750.0
    assert result["commission_on_marketing_punch_card"] == 500.0
    assert result["commission_on_marketing_highlight"] == 1000.0


def test_calculate_toters_kpis_calculates_true_promotion_cost() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["total_commission_on_promotions"] == 7750.0
    assert result["true_promotion_cost"] == 34750.0


def test_calculate_toters_kpis_calculates_commission_by_promotion_type() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["listing_fee_rate"] == 0.25
    assert result["commission_on_marketing_discount"] == 2500.0
    assert result["commission_on_marketing_fixed_price"] == 3000.0
    assert result["commission_on_marketing_free_delivery"] == 750.0
    assert result["commission_on_marketing_punch_card"] == 500.0
    assert result["commission_on_marketing_highlight"] == 1000.0


def test_calculate_toters_kpis_calculates_true_promotion_cost() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert result["total_commission_on_promotions"] == 7750.0
    assert result["true_promotion_cost"] == 34750.0
