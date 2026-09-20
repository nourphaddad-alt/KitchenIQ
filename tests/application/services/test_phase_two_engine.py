from __future__ import annotations

import pytest

from application.services.phase_two_engine import (
    calculate_margin_progress,
    calculate_minimum_spend_threshold,
    calculate_promotion_scenario,
    rank_promotions,
)


def _scenario(name: str = "Offer", promotion_orders: int = 140) -> dict[str, object]:
    return calculate_promotion_scenario(
        name=name,
        baseline_orders=100,
        promotion_orders=promotion_orders,
        list_price=100,
        discount_rate=0.10,
        platform_fee_rate=0.20,
        unit_cogs=30,
        packaging=5,
        ad_spend=100,
        cannibalization_loss=50,
        offer_type="Bundle",
        product="Hero + side",
        minimum_spend=120,
        timing="Weekday lunch",
        duration_days=7,
    )


def test_promotion_scenario_reconciles_full_economics() -> None:
    result = _scenario()

    assert result["baseline_unit_contribution"] == 45
    assert result["promotion_unit_contribution"] == 37
    assert result["incremental_orders"] == 40
    assert result["baseline_period_contribution"] == 4_500
    assert result["promotion_period_contribution"] == 5_080
    assert result["net_incremental_contribution"] == 530
    assert result["mvp_score"] == 530
    assert result["break_even_promotion_orders"] == 126
    assert result["profitable_to_scale"] is True


def test_promotion_can_increase_orders_but_destroy_contribution() -> None:
    result = calculate_promotion_scenario(
        name="Deep discount",
        baseline_orders=100,
        promotion_orders=120,
        list_price=100,
        discount_rate=0.50,
        platform_fee_rate=0.30,
        unit_cogs=35,
        packaging=5,
        ad_spend=500,
    )

    assert result["incremental_orders"] == 20
    assert result["promotion_unit_contribution"] == -5
    assert result["net_incremental_contribution"] < 0
    assert result["break_even_promotion_orders"] is None
    assert result["profitable_to_scale"] is False


def test_rank_promotions_uses_incremental_contribution() -> None:
    best = _scenario("Best", 150)
    weak = _scenario("Weak", 110)

    ranked = rank_promotions([weak, best])

    assert [item["name"] for item in ranked] == ["Best", "Weak"]
    assert ranked[0]["rank"] == 1
    assert "Scale" in str(ranked[0]["recommendation"])


def test_minimum_spend_funds_discount_cost_and_target() -> None:
    threshold = calculate_minimum_spend_threshold(
        variable_cost=300,
        fixed_discount=100,
        platform_fee_rate=0.20,
        target_contribution=240,
    )

    assert threshold == pytest.approx(800)


def test_margin_progress_quantifies_17_percent_gap() -> None:
    result = calculate_margin_progress(revenue=1_000, net_profit=100)

    assert result["current_margin_rate"] == pytest.approx(0.10)
    assert result["gap_rate"] == pytest.approx(0.07)
    assert result["profit_gap"] == pytest.approx(70)
    assert result["target_reached"] is False


def test_margin_progress_reports_target_reached_without_hiding_surplus() -> None:
    result = calculate_margin_progress(revenue=1_000, net_profit=200)

    assert result["gap_rate"] == pytest.approx(-0.03)
    assert result["profit_gap"] == pytest.approx(-30)
    assert result["target_reached"] is True
