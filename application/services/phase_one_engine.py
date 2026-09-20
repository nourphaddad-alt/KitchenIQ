from __future__ import annotations

from statistics import median
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


def _benchmark_status(
    value: float,
    *,
    healthy_test,
    red_flag_test,
) -> str:
    if healthy_test(value):
        return "Healthy"
    if red_flag_test(value):
        return "Red flag"
    return "Watch"


def assess_discovery(
    *,
    search_rank: int,
    rating: float,
    review_response_rate: float,
    photo_coverage_rate: float,
    conversion_rate: float,
) -> list[dict[str, object]]:
    """Assess the Phase 1 discovery metrics against the Excel benchmarks."""
    if search_rank < 1:
        raise ValueError("search_rank must be at least 1")
    if not 0 <= rating <= 5:
        raise ValueError("rating must be between 0 and 5")

    review_response_rate = _rate("review_response_rate", review_response_rate)
    photo_coverage_rate = _rate("photo_coverage_rate", photo_coverage_rate)
    conversion_rate = _rate("conversion_rate", conversion_rate)

    return [
        {
            "metric": "Core keyword rank",
            "value": search_rank,
            "status": _benchmark_status(
                search_rank,
                healthy_test=lambda value: value <= 10,
                red_flag_test=lambda value: value > 20,
            ),
            "action": "Retag the concept using the terms customers search for.",
        },
        {
            "metric": "Average rating",
            "value": rating,
            "status": _benchmark_status(
                rating,
                healthy_test=lambda value: value >= 4.5,
                red_flag_test=lambda value: value < 4.0,
            ),
            "action": "Run review recovery and fix the recurring complaint theme.",
        },
        {
            "metric": "Reviews answered within 24h",
            "value": review_response_rate,
            "status": _benchmark_status(
                review_response_rate,
                healthy_test=lambda value: value >= 1,
                red_flag_test=lambda value: value < 0.8,
            ),
            "action": "Assign daily review ownership and answer every review.",
        },
        {
            "metric": "Items with professional photos",
            "value": photo_coverage_rate,
            "status": _benchmark_status(
                photo_coverage_rate,
                healthy_test=lambda value: value >= 0.9,
                red_flag_test=lambda value: value < 0.7,
            ),
            "action": "Photograph missing items and reshoot low-converting items.",
        },
        {
            "metric": "Listing conversion rate",
            "value": conversion_rate,
            "status": _benchmark_status(
                conversion_rate,
                healthy_test=lambda value: value >= 0.15,
                red_flag_test=lambda value: value < 0.10,
            ),
            "action": "Improve the first image, item name and short description.",
        },
    ]


def audit_operations(
    *,
    total_orders: int,
    cancelled_orders: int,
    on_time_prep_orders: int,
    average_delivery_minutes: float,
    city_average_delivery_minutes: float,
    scheduled_hours: float,
    online_hours: float,
    gross_revenue: float,
    refunded_value: float,
    forgotten_item_orders: int,
) -> list[dict[str, object]]:
    """Calculate all six Phase 1 operational controls."""
    if total_orders <= 0:
        raise ValueError("total_orders must be greater than zero")

    counts = {
        "cancelled_orders": cancelled_orders,
        "on_time_prep_orders": on_time_prep_orders,
        "forgotten_item_orders": forgotten_item_orders,
    }
    for name, value in counts.items():
        if value < 0 or value > total_orders:
            raise ValueError(f"{name} must be between 0 and total_orders")

    scheduled_hours = _non_negative("scheduled_hours", scheduled_hours)
    online_hours = _non_negative("online_hours", online_hours)
    if scheduled_hours == 0:
        raise ValueError("scheduled_hours must be greater than zero")
    if online_hours > scheduled_hours:
        raise ValueError("online_hours cannot exceed scheduled_hours")

    average_delivery_minutes = _non_negative(
        "average_delivery_minutes", average_delivery_minutes
    )
    city_average_delivery_minutes = _non_negative(
        "city_average_delivery_minutes", city_average_delivery_minutes
    )
    if city_average_delivery_minutes == 0:
        raise ValueError("city_average_delivery_minutes must be greater than zero")

    gross_revenue = _non_negative("gross_revenue", gross_revenue)
    refunded_value = _non_negative("refunded_value", refunded_value)
    cancel_rate = cancelled_orders / total_orders
    prep_rate = on_time_prep_orders / total_orders
    delivery_variance = (
        average_delivery_minutes / city_average_delivery_minutes - 1
    )
    uptime_rate = online_hours / scheduled_hours
    refund_rate = _safe_divide(refunded_value, gross_revenue)
    forgotten_rate = forgotten_item_orders / total_orders

    return [
        {
            "metric": "Cancel rate",
            "value": cancel_rate,
            "status": _benchmark_status(
                cancel_rate,
                healthy_test=lambda value: value < 0.02,
                red_flag_test=lambda value: value > 0.05,
            ),
            "action": "Review cancel reasons and sync item availability.",
        },
        {
            "metric": "Prep within quoted window",
            "value": prep_rate,
            "status": _benchmark_status(
                prep_rate,
                healthy_test=lambda value: value > 0.95,
                red_flag_test=lambda value: value < 0.85,
            ),
            "action": "Reset prep promises and isolate slow items or dayparts.",
        },
        {
            "metric": "Delivery time vs city",
            "value": delivery_variance,
            "status": _benchmark_status(
                delivery_variance,
                healthy_test=lambda value: value <= 0,
                red_flag_test=lambda value: value > 0.15,
            ),
            "action": "Raise the variance with the platform or reduce the radius.",
        },
        {
            "metric": "Menu uptime",
            "value": uptime_rate,
            "status": _benchmark_status(
                uptime_rate,
                healthy_test=lambda value: value > 0.98,
                red_flag_test=lambda value: value < 0.90,
            ),
            "action": "Audit unplanned offline windows and opening-hour sync.",
        },
        {
            "metric": "Refund value / revenue",
            "value": refund_rate,
            "status": (
                "Unavailable"
                if refund_rate is None
                else _benchmark_status(
                    refund_rate,
                    healthy_test=lambda value: value < 0.01,
                    red_flag_test=lambda value: value > 0.03,
                )
            ),
            "action": "Fix the packaging or recipe of the top refunded SKUs.",
        },
        {
            "metric": "Forgotten-item incident rate",
            "value": forgotten_rate,
            "status": _benchmark_status(
                forgotten_rate,
                healthy_test=lambda value: value < 0.005,
                red_flag_test=lambda value: value > 0.02,
            ),
            "action": "Add item-count verification to the packing hand-off.",
        },
    ]


def calculate_profit_baseline(
    *,
    gross_revenue: float,
    orders: int,
    platform_fees: float,
    vat: float,
    discounts: float,
    ad_spend: float,
    cogs: float,
    packaging: float,
    fixed_costs: float,
    operating_days: int,
) -> dict[str, float | None]:
    """Build a transparent contribution and break-even baseline."""
    if orders <= 0:
        raise ValueError("orders must be greater than zero")
    if operating_days <= 0:
        raise ValueError("operating_days must be greater than zero")

    values = {
        "gross_revenue": gross_revenue,
        "platform_fees": platform_fees,
        "vat": vat,
        "discounts": discounts,
        "ad_spend": ad_spend,
        "cogs": cogs,
        "packaging": packaging,
        "fixed_costs": fixed_costs,
    }
    values = {name: _non_negative(name, value) for name, value in values.items()}

    platform_costs = (
        values["platform_fees"]
        + values["vat"]
        + values["discounts"]
        + values["ad_spend"]
    )
    net_platform_payout = values["gross_revenue"] - platform_costs
    contribution = net_platform_payout - values["cogs"] - values["packaging"]
    net_profit = contribution - values["fixed_costs"]
    contribution_per_order = contribution / orders
    break_even_orders = (
        values["fixed_costs"] / contribution_per_order
        if contribution_per_order > 0
        else None
    )

    return {
        "platform_costs": platform_costs,
        "platform_cost_rate": _safe_divide(platform_costs, values["gross_revenue"]),
        "net_platform_payout": net_platform_payout,
        "retained_revenue_rate": _safe_divide(
            net_platform_payout, values["gross_revenue"]
        ),
        "variable_costs": values["cogs"] + values["packaging"],
        "contribution": contribution,
        "contribution_margin_rate": _safe_divide(
            contribution, values["gross_revenue"]
        ),
        "contribution_per_order": contribution_per_order,
        "net_profit": net_profit,
        "net_margin_rate": _safe_divide(net_profit, values["gross_revenue"]),
        "break_even_orders_period": break_even_orders,
        "break_even_orders_per_day": (
            break_even_orders / operating_days
            if break_even_orders is not None
            else None
        ),
        "volume_buffer_rate": (
            orders / break_even_orders - 1
            if break_even_orders and break_even_orders > 0
            else None
        ),
    }


def calculate_repricing(
    *,
    unit_cogs: float,
    packaging: float,
    platform_fee_rate: float,
    vat_rate: float,
    target_contribution: float,
    current_price: float | None = None,
) -> dict[str, float | None]:
    """Price an SKU to deliver a target currency contribution after fees."""
    unit_cogs = _non_negative("unit_cogs", unit_cogs)
    packaging = _non_negative("packaging", packaging)
    platform_fee_rate = _rate("platform_fee_rate", platform_fee_rate)
    vat_rate = _rate("vat_rate", vat_rate)
    target_contribution = _non_negative(
        "target_contribution", target_contribution
    )
    combined_rate = platform_fee_rate + vat_rate
    if combined_rate >= 1:
        raise ValueError("combined platform fee and VAT rate must be below 100%")

    recommended_price = (
        unit_cogs + packaging + target_contribution
    ) / (1 - combined_rate)
    current_contribution = None
    current_coverage_ratio = None
    if current_price is not None:
        current_price = _non_negative("current_price", current_price)
        current_fees = current_price * combined_rate
        current_contribution = (
            current_price - current_fees - unit_cogs - packaging
        )
        true_cost = unit_cogs + packaging + current_fees
        current_coverage_ratio = _safe_divide(current_price, true_cost)

    return {
        "recommended_price": recommended_price,
        "combined_fee_rate": combined_rate,
        "current_contribution": current_contribution,
        "current_coverage_ratio": current_coverage_ratio,
        "price_change": (
            recommended_price - current_price
            if current_price is not None
            else None
        ),
    }


def classify_menu_items(
    items: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Classify menu items by contribution margin and sales velocity."""
    normalized: list[dict[str, object]] = []
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError("every menu item needs a name")
        units = _non_negative("units", float(item.get("units", 0)))
        price = _non_negative("price", float(item.get("price", 0)))
        variable_cost = _non_negative(
            "variable_cost", float(item.get("variable_cost", 0))
        )
        unit_contribution = price - variable_cost
        normalized.append(
            {
                "name": name,
                "units": units,
                "price": price,
                "variable_cost": variable_cost,
                "unit_contribution": unit_contribution,
                "revenue": units * price,
            }
        )

    if not normalized:
        raise ValueError("at least one menu item is required")

    volume_cutoff = median(float(item["units"]) for item in normalized)
    margin_cutoff = median(
        float(item["unit_contribution"]) for item in normalized
    )
    total_revenue = sum(float(item["revenue"]) for item in normalized)
    star_revenue = 0.0
    for item in normalized:
        high_volume = float(item["units"]) >= volume_cutoff
        high_margin = float(item["unit_contribution"]) >= margin_cutoff
        if high_volume and high_margin:
            quadrant = "Star"
            star_revenue += float(item["revenue"])
            action = "Feature and protect availability."
        elif high_volume:
            quadrant = "Plow horse"
            action = "Reprice or lower its variable cost."
        elif high_margin:
            quadrant = "Puzzle"
            action = "Improve visibility or test it in a bundle."
        else:
            quadrant = "Dog"
            action = "Re-engineer, simplify or remove."
        item["quadrant"] = quadrant
        item["action"] = action

    return {
        "items": normalized,
        "volume_cutoff": volume_cutoff,
        "unit_contribution_cutoff": margin_cutoff,
        "star_revenue_share": _safe_divide(star_revenue, total_revenue),
    }


def calculate_bundle(
    *,
    hero_price: float,
    hero_cost: float,
    add_on_price: float,
    add_on_cost: float,
    bundle_price: float,
    platform_fee_rate: float,
) -> dict[str, float | None]:
    values = {
        "hero_price": hero_price,
        "hero_cost": hero_cost,
        "add_on_price": add_on_price,
        "add_on_cost": add_on_cost,
        "bundle_price": bundle_price,
    }
    values = {name: _non_negative(name, value) for name, value in values.items()}
    platform_fee_rate = _rate("platform_fee_rate", platform_fee_rate)
    list_price = values["hero_price"] + values["add_on_price"]
    bundle_contribution = (
        values["bundle_price"] * (1 - platform_fee_rate)
        - values["hero_cost"]
        - values["add_on_cost"]
    )
    hero_contribution = (
        values["hero_price"] * (1 - platform_fee_rate)
        - values["hero_cost"]
    )
    return {
        "customer_saving": list_price - values["bundle_price"],
        "bundle_contribution": bundle_contribution,
        "bundle_contribution_rate": _safe_divide(
            bundle_contribution, values["bundle_price"]
        ),
        "contribution_uplift_vs_hero": bundle_contribution - hero_contribution,
    }


def calculate_ad_performance(
    *,
    attributed_revenue: float,
    ad_spend: float,
    attributed_orders: int,
    contribution_before_ads: float,
) -> dict[str, float | None]:
    attributed_revenue = _non_negative(
        "attributed_revenue", attributed_revenue
    )
    ad_spend = _non_negative("ad_spend", ad_spend)
    contribution_before_ads = float(contribution_before_ads)
    if attributed_orders < 0:
        raise ValueError("attributed_orders cannot be negative")
    return {
        "roas": _safe_divide(attributed_revenue, ad_spend),
        "cost_per_attributed_order": _safe_divide(ad_spend, attributed_orders),
        "contribution_after_ads": contribution_before_ads - ad_spend,
        "profitable": contribution_before_ads - ad_spend > 0,
    }
