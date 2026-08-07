import pandas as pd

from utils.toters_kpis import calculate_toters_kpis


def _base_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "order_id": "order-1001",
        "order_date": "2026-03-01 12:30:00",
        "gross_revenue": 100000.0,
        "store_listing_fee": 25000.0,
        "total_marketing_cost": 27000.0,
        "vat": 5000.0,
        "courier_cost": 0.0,
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
    result = calculate_toters_kpis(pd.DataFrame([_base_row()]))

    assert result["total_marketing_discount"] == 10000.0
    assert result["total_marketing_fixed_price"] == 12000.0
    assert result["total_marketing_free_delivery"] == 3000.0
    assert result["total_marketing_punch_card"] == 2000.0
    assert result["total_marketing_highlight"] == 4000.0
    assert result["total_marketing_credit_note"] == -3000.0
    assert result["total_marketing_highlight_credit_note"] == -1000.0


def test_calculate_toters_kpis_calculates_promotion_totals() -> None:
    result = calculate_toters_kpis(pd.DataFrame([_base_row()]))

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

    result = calculate_toters_kpis(pd.DataFrame([legacy_row]))

    assert result["total_marketing_cost"] == 27000.0
    assert result["gross_promotion_spend"] == 0.0
    assert result["promotion_credits"] == 0.0
    assert result["net_promotion_spend"] == 0.0


def test_calculate_toters_kpis_calculates_commission_by_promotion_type() -> None:
    result = calculate_toters_kpis(pd.DataFrame([_base_row()]))

    assert result["listing_fee_rate"] == 0.25
    assert result["commission_on_marketing_discount"] == 2500.0
    assert result["commission_on_marketing_fixed_price"] == 3000.0
    assert result["commission_on_marketing_free_delivery"] == 750.0
    assert result["commission_on_marketing_punch_card"] == 500.0
    assert result["commission_on_marketing_highlight"] == 1000.0


def test_calculate_toters_kpis_calculates_true_promotion_cost() -> None:
    result = calculate_toters_kpis(pd.DataFrame([_base_row()]))

    assert result["total_commission_on_promotions"] == 5500.0
    assert result["true_promotion_cost"] == 32500.0


def test_cost_only_courier_activity_does_not_increase_order_count() -> None:
    customer_order = _base_row(
        order_id="order-1001",
        gross_revenue=100000.0,
        courier_cost=0.0,
    )

    courier_only_activity = _base_row(
        order_id="courier-activity-1",
        gross_revenue=0.0,
        store_listing_fee=0.0,
        total_marketing_cost=0.0,
        vat=0.0,
        courier_cost=5000.0,
        total_platform_cost=5000.0,
        net_order_revenue=-5000.0,
        marketing_discount=0.0,
        marketing_fixed_price=0.0,
        marketing_free_delivery=0.0,
        marketing_punch_card=0.0,
        marketing_highlight=0.0,
        marketing_credit_note=0.0,
        marketing_highlight_credit_note=0.0,
    )

    result = calculate_toters_kpis(
        pd.DataFrame([customer_order, courier_only_activity])
    )

    assert result["total_orders"] == 1
    assert result["average_order_value"] == 100000.0
    assert result["total_courier_cost"] == 5000.0


def test_account_level_costs_are_merged_into_financial_totals() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()]),
        account_level_costs={
            "marketing_highlight": 10000.0,
            "vat_marketing_highlight": 1100.0,
            "marketing_highlight_credit_note": 1000.0,
        },
    )

    assert result["total_marketing_highlight"] == 14000.0
    assert result["total_marketing_highlight_credit_note"] == -2000.0
    assert result["vat_on_orders"] == 5000.0
    assert result["vat_on_marketing"] == 1100.0
    assert result["total_vat"] == 6100.0
    assert result["total_marketing_cost"] == 36000.0
    assert result["total_platform_cost"] == 67100.0
    assert result["net_order_revenue"] == 32900.0


def test_commission_attribution_excludes_highlight_spend() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()]),
        account_level_costs={
            "marketing_highlight": 10000.0,
        },
    )

    assert result["listing_fee_rate"] == 0.25
    assert result["total_commission_on_promotions"] == 5500.0


def test_cost_only_courier_vat_is_not_classified_as_order_vat() -> None:
    customer_order = _base_row(
        order_id="order-1001",
        gross_revenue=100000.0,
        store_listing_fee=25000.0,
        vat=2750.0,
        courier_cost=0.0,
    )

    courier_only_activity = _base_row(
        order_id="courier-activity-1",
        gross_revenue=0.0,
        store_listing_fee=0.0,
        total_marketing_cost=0.0,
        vat=550.0,
        courier_cost=5000.0,
        total_platform_cost=5550.0,
        net_order_revenue=-5550.0,
        marketing_discount=0.0,
        marketing_fixed_price=0.0,
        marketing_free_delivery=0.0,
        marketing_punch_card=0.0,
        marketing_highlight=0.0,
        marketing_credit_note=0.0,
        marketing_highlight_credit_note=0.0,
    )

    result = calculate_toters_kpis(
        pd.DataFrame(
            [
                customer_order,
                courier_only_activity,
            ]
        )
    )

    assert result["total_orders"] == 1
    assert result["vat_on_orders"] == 2750.0
    assert result["vat_on_listing_fees"] == 2750.0
    assert result["vat_on_courier"] == 550.0
    assert result["total_vat"] == 3300.0
    assert result["total_courier_cost"] == 5000.0



def test_median_order_value_is_not_part_of_kpi_contract() -> None:
    result = calculate_toters_kpis(
        pd.DataFrame([_base_row()])
    )

    assert "median_order_value" not in result
    assert result["minimum_order_value"] == 100000.0
    assert result["maximum_order_value"] == 100000.0
