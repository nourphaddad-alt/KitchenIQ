from __future__ import annotations

from math import ceil
from typing import Iterable, Mapping


def _non_negative(name: str, value: float) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def _rate(name: str, value: float) -> float:
    value = float(value)
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def _safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def calculate_promotion_scenario(
    *,
    name: str,
    baseline_orders: int,
    promotion_orders: int,
    list_price: float,
    discount_rate: float,
    platform_fee_rate: float,
    unit_cogs: float,
    packaging: float,
    ad_spend: float,
    cannibalization_loss: float = 0,
    offer_type: str = "Discount",
    product: str = "",
    minimum_spend: float = 0,
    timing: str = "",
    duration_days: int = 1,
) -> dict[str, object]:
    """Estimate promotion incrementality from a user-provided baseline."""
    if baseline_orders < 0 or promotion_orders < 0:
        raise ValueError("order counts cannot be negative")
    if duration_days <= 0:
        raise ValueError("duration_days must be greater than zero")

    list_price = _non_negative("list_price", list_price)
    discount_rate = _rate("discount_rate", discount_rate)
    platform_fee_rate = _rate("platform_fee_rate", platform_fee_rate)
    unit_cogs = _non_negative("unit_cogs", unit_cogs)
    packaging = _non_negative("packaging", packaging)
    ad_spend = _non_negative("ad_spend", ad_spend)
    cannibalization_loss = _non_negative(
        "cannibalization_loss", cannibalization_loss
    )
    minimum_spend = _non_negative("minimum_spend", minimum_spend)

    promotion_price = list_price * (1 - discount_rate)
    baseline_unit_contribution = (
        list_price * (1 - platform_fee_rate) - unit_cogs - packaging
    )
    promotion_unit_contribution = (
        promotion_price * (1 - platform_fee_rate) - unit_cogs - packaging
    )
    baseline_period_contribution = baseline_orders * baseline_unit_contribution
    promotion_period_contribution = (
        promotion_orders * promotion_unit_contribution - ad_spend
    )
    incremental_orders = promotion_orders - baseline_orders
    net_incremental_contribution = (
        promotion_period_contribution
        - baseline_period_contribution
        - cannibalization_loss
    )
    required_promotion_orders = None
    if promotion_unit_contribution > 0:
        required_promotion_orders = ceil(
            (
                baseline_period_contribution
                + ad_spend
                + cannibalization_loss
            )
            / promotion_unit_contribution
        )

    return {
        "name": name.strip() or "Untitled promotion",
        "offer_type": offer_type,
        "product": product,
        "minimum_spend": minimum_spend,
        "timing": timing,
        "duration_days": duration_days,
        "baseline_orders": baseline_orders,
        "promotion_orders": promotion_orders,
        "incremental_orders": incremental_orders,
        "incremental_order_rate": _safe_divide(
            incremental_orders, baseline_orders
        ),
        "promotion_price": promotion_price,
        "discount_cost": promotion_orders * list_price * discount_rate,
        "baseline_unit_contribution": baseline_unit_contribution,
        "promotion_unit_contribution": promotion_unit_contribution,
        "promotion_contribution_rate": _safe_divide(
            promotion_unit_contribution, promotion_price
        ),
        "baseline_period_contribution": baseline_period_contribution,
        "promotion_period_contribution": promotion_period_contribution,
        "cannibalization_loss": cannibalization_loss,
        "net_incremental_contribution": net_incremental_contribution,
        "mvp_score": net_incremental_contribution,
        "break_even_promotion_orders": required_promotion_orders,
        "profitable_to_scale": net_incremental_contribution > 0,
    }


def rank_promotions(
    scenarios: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Rank tested offers by the Excel-defined MVP metric."""
    ranked = [dict(scenario) for scenario in scenarios]
    ranked.sort(
        key=lambda scenario: float(scenario["mvp_score"]),
        reverse=True,
    )
    for rank, scenario in enumerate(ranked, start=1):
        scenario["rank"] = rank
        scenario["recommendation"] = (
            "Scale carefully and validate in another test window."
            if float(scenario["mvp_score"]) > 0
            else "Do not scale; change one mechanic and retest."
        )
    return ranked


def calculate_minimum_spend_threshold(
    *,
    variable_cost: float,
    fixed_discount: float,
    platform_fee_rate: float,
    target_contribution: float,
) -> float:
    """Return the basket value needed to fund costs and target contribution."""
    variable_cost = _non_negative("variable_cost", variable_cost)
    fixed_discount = _non_negative("fixed_discount", fixed_discount)
    platform_fee_rate = _rate("platform_fee_rate", platform_fee_rate)
    target_contribution = _non_negative(
        "target_contribution", target_contribution
    )
    if platform_fee_rate >= 1:
        raise ValueError("platform_fee_rate must be below 100%")
    return (
        variable_cost + fixed_discount + target_contribution
    ) / (1 - platform_fee_rate)


def calculate_margin_progress(
    *,
    revenue: float,
    net_profit: float,
    target_rate: float = 0.17,
) -> dict[str, float | bool | None]:
    revenue = _non_negative("revenue", revenue)
    target_rate = _rate("target_rate", target_rate)
    current_rate = _safe_divide(float(net_profit), revenue)
    if current_rate is None:
        return {
            "current_margin_rate": None,
            "target_rate": target_rate,
            "gap_rate": None,
            "profit_gap": None,
            "target_reached": False,
        }
    profit_gap = revenue * target_rate - float(net_profit)
    return {
        "current_margin_rate": current_rate,
        "target_rate": target_rate,
        "gap_rate": target_rate - current_rate,
        "profit_gap": profit_gap,
        "target_reached": current_rate >= target_rate,
    }
