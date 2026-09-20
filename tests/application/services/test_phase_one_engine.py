from __future__ import annotations

import pytest

from application.services.phase_one_engine import (
    assess_discovery,
    audit_operations,
    calculate_ad_performance,
    calculate_bundle,
    calculate_profit_baseline,
    calculate_repricing,
    classify_menu_items,
)


def test_discovery_audit_applies_specification_boundaries() -> None:
    result = assess_discovery(
        search_rank=10,
        rating=4.5,
        review_response_rate=1,
        photo_coverage_rate=0.90,
        conversion_rate=0.15,
    )

    assert [item["status"] for item in result] == ["Healthy"] * 5


def test_operations_audit_calculates_all_six_controls() -> None:
    result = audit_operations(
        total_orders=1000,
        cancelled_orders=10,
        on_time_prep_orders=960,
        average_delivery_minutes=30,
        city_average_delivery_minutes=30,
        scheduled_hours=200,
        online_hours=198,
        gross_revenue=100_000_000,
        refunded_value=500_000,
        forgotten_item_orders=4,
    )

    assert len(result) == 6
    assert [item["status"] for item in result] == ["Healthy"] * 6
    assert result[2]["value"] == pytest.approx(0)


def test_operations_rejects_impossible_counts() -> None:
    with pytest.raises(ValueError, match="cancelled_orders"):
        audit_operations(
            total_orders=10,
            cancelled_orders=11,
            on_time_prep_orders=10,
            average_delivery_minutes=30,
            city_average_delivery_minutes=30,
            scheduled_hours=10,
            online_hours=10,
            gross_revenue=100,
            refunded_value=0,
            forgotten_item_orders=0,
        )


def test_profit_baseline_reconciles_waterfall_and_break_even() -> None:
    result = calculate_profit_baseline(
        gross_revenue=100_000,
        orders=100,
        platform_fees=20_000,
        vat=2_000,
        discounts=3_000,
        ad_spend=5_000,
        cogs=25_000,
        packaging=5_000,
        fixed_costs=10_000,
        operating_days=20,
    )

    assert result["platform_costs"] == 30_000
    assert result["net_platform_payout"] == 70_000
    assert result["contribution"] == 40_000
    assert result["net_profit"] == 30_000
    assert result["net_margin_rate"] == pytest.approx(0.30)
    assert result["break_even_orders_period"] == pytest.approx(25)
    assert result["break_even_orders_per_day"] == pytest.approx(1.25)


def test_break_even_is_unavailable_when_order_contribution_is_not_positive() -> None:
    result = calculate_profit_baseline(
        gross_revenue=10_000,
        orders=10,
        platform_fees=5_000,
        vat=0,
        discounts=0,
        ad_spend=0,
        cogs=5_000,
        packaging=1_000,
        fixed_costs=2_000,
        operating_days=10,
    )

    assert result["contribution"] == -1_000
    assert result["break_even_orders_period"] is None


def test_repricing_guarantees_requested_currency_contribution() -> None:
    result = calculate_repricing(
        unit_cogs=250,
        packaging=50,
        platform_fee_rate=0.25,
        vat_rate=0.05,
        target_contribution=400,
        current_price=800,
    )

    assert result["recommended_price"] == pytest.approx(1_000)
    recommended_price = float(result["recommended_price"])
    achieved = recommended_price * 0.70 - 250 - 50
    assert achieved == pytest.approx(400)


def test_menu_matrix_classifies_all_quadrants() -> None:
    result = classify_menu_items(
        [
            {"name": "Star", "units": 100, "price": 20, "variable_cost": 5},
            {"name": "Horse", "units": 90, "price": 10, "variable_cost": 8},
            {"name": "Puzzle", "units": 20, "price": 20, "variable_cost": 5},
            {"name": "Dog", "units": 10, "price": 10, "variable_cost": 8},
        ]
    )

    assert {item["name"]: item["quadrant"] for item in result["items"]} == {
        "Star": "Star",
        "Horse": "Plow horse",
        "Puzzle": "Puzzle",
        "Dog": "Dog",
    }


def test_bundle_and_ads_use_contribution_not_only_revenue() -> None:
    bundle = calculate_bundle(
        hero_price=800,
        hero_cost=300,
        add_on_price=200,
        add_on_cost=50,
        bundle_price=900,
        platform_fee_rate=0.20,
    )
    ads = calculate_ad_performance(
        attributed_revenue=1_000,
        ad_spend=200,
        attributed_orders=10,
        contribution_before_ads=150,
    )

    assert bundle["customer_saving"] == 100
    assert bundle["bundle_contribution"] == 370
    assert bundle["contribution_uplift_vs_hero"] == 30
    assert ads["roas"] == 5
    assert ads["contribution_after_ads"] == -50
    assert ads["profitable"] is False
