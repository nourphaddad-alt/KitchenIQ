from __future__ import annotations

import pandas as pd
import streamlit as st

from application.services.phase_one_engine import (
    assess_discovery,
    audit_operations,
    calculate_ad_performance,
    calculate_bundle,
    calculate_profit_baseline,
    calculate_repricing,
    classify_menu_items,
)
from application.services.phase_two_engine import (
    calculate_margin_progress,
    calculate_minimum_spend_threshold,
    calculate_promotion_scenario,
    rank_promotions,
)


def _money(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B LBP"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M LBP"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K LBP"
    return f"{value:,.0f} LBP"


def _percent(value: float | None) -> str:
    return "Unavailable" if value is None else f"{value:.1%}"


def _run_safely(calculation, state_key: str, **kwargs) -> None:
    try:
        st.session_state[state_key] = calculation(**kwargs)
    except ValueError as error:
        st.error(str(error))


def _render_discovery() -> None:
    st.markdown("### Concept & discovery audit")
    st.write(
        "Enter the latest listing evidence. KitchenIQ compares it with the "
        "Phase 1 visibility and conversion benchmarks."
    )
    with st.form("phase_one_discovery"):
        col1, col2, col3 = st.columns(3)
        search_rank = col1.number_input(
            "Core keyword search rank", min_value=1, value=12
        )
        rating = col2.number_input(
            "Average rating", min_value=0.0, max_value=5.0, value=4.2, step=0.1
        )
        review_rate = col3.number_input(
            "Reviews answered within 24h (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
        )
        col4, col5 = st.columns(2)
        photo_rate = col4.number_input(
            "Menu items with professional photos (%)",
            min_value=0.0,
            max_value=100.0,
            value=80.0,
        )
        conversion_rate = col5.number_input(
            "Listing view-to-order conversion (%)",
            min_value=0.0,
            max_value=100.0,
            value=12.0,
        )
        submitted = st.form_submit_button("Run discovery audit", type="primary")
    if submitted:
        _run_safely(
            assess_discovery,
            "phase_one_discovery_result",
            search_rank=int(search_rank),
            rating=rating,
            review_response_rate=review_rate / 100,
            photo_coverage_rate=photo_rate / 100,
            conversion_rate=conversion_rate / 100,
        )
    result = st.session_state.get("phase_one_discovery_result")
    if result:
        rows = []
        for item in result:
            value = item["value"]
            if "rate" in str(item["metric"]).lower() or item["metric"] in {
                "Reviews answered within 24h",
                "Items with professional photos",
            }:
                value = _percent(float(value))
            elif item["metric"] == "Average rating":
                value = f"{float(value):.1f} / 5"
            else:
                value = str(value)
            rows.append({**item, "value": value})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def _render_operations() -> None:
    st.markdown("### Operations control room")
    st.caption(
        "Use the same reporting period for every field. Delivery variance "
        "uses the city benchmark you provide."
    )
    with st.form("phase_one_operations"):
        c1, c2, c3 = st.columns(3)
        total_orders = c1.number_input("Total orders", min_value=1, value=500)
        cancelled = c2.number_input("Cancelled orders", min_value=0, value=10)
        on_time = c3.number_input("Orders prepped on time", min_value=0, value=450)
        c4, c5, c6 = st.columns(3)
        delivery = c4.number_input(
            "Average delivery time (minutes)", min_value=0.0, value=35.0
        )
        city_delivery = c5.number_input(
            "City average delivery time (minutes)", min_value=0.1, value=32.0
        )
        scheduled = c6.number_input(
            "Scheduled operating hours", min_value=0.1, value=200.0
        )
        c7, c8, c9 = st.columns(3)
        online = c7.number_input("Hours online", min_value=0.0, value=190.0)
        revenue = c8.number_input(
            "Gross revenue (LBP)", min_value=0.0, value=100_000_000.0
        )
        refunds = c9.number_input(
            "Refunded value (LBP)", min_value=0.0, value=1_500_000.0
        )
        forgotten = st.number_input(
            "Orders with a forgotten item", min_value=0, value=4
        )
        submitted = st.form_submit_button("Audit operations", type="primary")
    if submitted:
        _run_safely(
            audit_operations,
            "phase_one_operations_result",
            total_orders=int(total_orders),
            cancelled_orders=int(cancelled),
            on_time_prep_orders=int(on_time),
            average_delivery_minutes=delivery,
            city_average_delivery_minutes=city_delivery,
            scheduled_hours=scheduled,
            online_hours=online,
            gross_revenue=revenue,
            refunded_value=refunds,
            forgotten_item_orders=int(forgotten),
        )
    result = st.session_state.get("phase_one_operations_result")
    if result:
        rows = [
            {**item, "value": _percent(item["value"])}
            for item in result
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def _render_profit_and_pricing() -> None:
    st.markdown("### Profit baseline and break-even")
    st.caption(
        "Gross revenue is reduced by platform fees, VAT, restaurant-funded "
        "discounts and ads, then by COGS, packaging and fixed costs."
    )
    with st.form("phase_one_profit"):
        c1, c2, c3 = st.columns(3)
        gross = c1.number_input(
            "Gross revenue (LBP)", min_value=0.0, value=100_000_000.0
        )
        orders = c2.number_input("Orders", min_value=1, value=500)
        days = c3.number_input("Operating days", min_value=1, value=30)
        c4, c5, c6 = st.columns(3)
        fees = c4.number_input(
            "Platform fees (LBP)", min_value=0.0, value=25_000_000.0
        )
        vat = c5.number_input("VAT (LBP)", min_value=0.0, value=3_000_000.0)
        discounts = c6.number_input(
            "Restaurant-funded discounts (LBP)",
            min_value=0.0,
            value=5_000_000.0,
        )
        c7, c8, c9, c10 = st.columns(4)
        ads = c7.number_input("Ad spend (LBP)", min_value=0.0, value=2_000_000.0)
        cogs = c8.number_input("COGS (LBP)", min_value=0.0, value=28_000_000.0)
        packaging = c9.number_input(
            "Packaging (LBP)", min_value=0.0, value=4_000_000.0
        )
        fixed = c10.number_input(
            "Fixed costs (LBP)", min_value=0.0, value=20_000_000.0
        )
        submitted = st.form_submit_button("Calculate profit baseline", type="primary")
    if submitted:
        _run_safely(
            calculate_profit_baseline,
            "phase_one_profit_result",
            gross_revenue=gross,
            orders=int(orders),
            platform_fees=fees,
            vat=vat,
            discounts=discounts,
            ad_spend=ads,
            cogs=cogs,
            packaging=packaging,
            fixed_costs=fixed,
            operating_days=int(days),
        )
    result = st.session_state.get("phase_one_profit_result")
    if result:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Net platform payout", _money(result["net_platform_payout"]))
        c2.metric("Contribution", _money(result["contribution"]))
        c3.metric("Net profit", _money(result["net_profit"]))
        c4.metric("Net margin", _percent(result["net_margin_rate"]))
        b1, b2, b3 = st.columns(3)
        b1.metric("Contribution / order", _money(result["contribution_per_order"]))
        b2.metric(
            "Break-even orders / day",
            (
                f"{result['break_even_orders_per_day']:,.1f}"
                if result["break_even_orders_per_day"] is not None
                else "Not reachable"
            ),
        )
        b3.metric("Volume buffer", _percent(result["volume_buffer_rate"]))

    st.markdown("### SKU repricing")
    st.caption(
        "Assumption: target contribution is an LBP amount per item. "
        "Recommended price = (COGS + packaging + target contribution) ÷ "
        "(1 − platform fee rate − VAT rate)."
    )
    with st.form("phase_one_repricing"):
        c1, c2, c3 = st.columns(3)
        current_price = c1.number_input(
            "Current item price (LBP)", min_value=0.0, value=800_000.0
        )
        unit_cogs = c2.number_input(
            "Unit COGS (LBP)", min_value=0.0, value=250_000.0
        )
        unit_packaging = c3.number_input(
            "Unit packaging (LBP)", min_value=0.0, value=30_000.0
        )
        c4, c5, c6 = st.columns(3)
        fee_rate = c4.number_input(
            "Platform fee (%)", min_value=0.0, max_value=99.0, value=25.0
        )
        vat_rate = c5.number_input(
            "VAT on sale (%)", min_value=0.0, max_value=99.0, value=0.0
        )
        target = c6.number_input(
            "Target contribution / item (LBP)",
            min_value=0.0,
            value=250_000.0,
        )
        submitted = st.form_submit_button("Recommend item price")
    if submitted:
        _run_safely(
            calculate_repricing,
            "phase_one_repricing_result",
            unit_cogs=unit_cogs,
            packaging=unit_packaging,
            platform_fee_rate=fee_rate / 100,
            vat_rate=vat_rate / 100,
            target_contribution=target,
            current_price=current_price,
        )
    result = st.session_state.get("phase_one_repricing_result")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Recommended price", _money(result["recommended_price"]))
        c2.metric("Price change", _money(result["price_change"]))
        c3.metric(
            "Current price coverage",
            (
                f"{result['current_coverage_ratio']:.2f}x"
                if result["current_coverage_ratio"] is not None
                else "Unavailable"
            ),
        )


def _render_menu_iq() -> None:
    st.markdown("### Menu matrix")
    st.caption(
        "Items are split at the median sales volume and median unit "
        "contribution for the data entered below."
    )
    default_items = pd.DataFrame(
        [
            {"name": "Hero item", "units": 120, "price": 900_000, "variable_cost": 350_000},
            {"name": "Side", "units": 80, "price": 300_000, "variable_cost": 90_000},
            {"name": "Slow item", "units": 20, "price": 750_000, "variable_cost": 500_000},
        ]
    )
    menu_data = st.data_editor(
        st.session_state.get("phase_one_menu_input", default_items),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="phase_one_menu_editor",
    )
    if st.button("Classify menu", type="primary"):
        st.session_state["phase_one_menu_input"] = menu_data
        _run_safely(
            classify_menu_items,
            "phase_one_menu_result",
            items=menu_data.to_dict("records"),
        )
    result = st.session_state.get("phase_one_menu_result")
    if result:
        st.metric("Revenue from Stars", _percent(result["star_revenue_share"]))
        st.dataframe(pd.DataFrame(result["items"]), hide_index=True, width="stretch")

    st.markdown("### Combo / bundle economics")
    with st.form("phase_one_bundle"):
        c1, c2, c3 = st.columns(3)
        hero_price = c1.number_input("Hero price", min_value=0.0, value=800_000.0)
        hero_cost = c2.number_input("Hero variable cost", min_value=0.0, value=300_000.0)
        add_on_price = c3.number_input("Side/drink price", min_value=0.0, value=250_000.0)
        c4, c5, c6 = st.columns(3)
        add_on_cost = c4.number_input("Side/drink variable cost", min_value=0.0, value=60_000.0)
        bundle_price = c5.number_input("Bundle price", min_value=0.0, value=950_000.0)
        fee = c6.number_input("Bundle platform fee (%)", min_value=0.0, max_value=100.0, value=25.0)
        submitted = st.form_submit_button("Test bundle")
    if submitted:
        _run_safely(
            calculate_bundle,
            "phase_one_bundle_result",
            hero_price=hero_price,
            hero_cost=hero_cost,
            add_on_price=add_on_price,
            add_on_cost=add_on_cost,
            bundle_price=bundle_price,
            platform_fee_rate=fee / 100,
        )
    result = st.session_state.get("phase_one_bundle_result")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Customer saving", _money(result["customer_saving"]))
        c2.metric("Bundle contribution", _money(result["bundle_contribution"]))
        c3.metric(
            "Contribution uplift vs hero",
            _money(result["contribution_uplift_vs_hero"]),
        )


def _render_marketing() -> None:
    st.markdown("### Marketing and ads")
    st.caption(
        "ROAS is shown alongside contribution after ads so revenue does not "
        "hide an unprofitable campaign."
    )
    with st.form("phase_one_ads"):
        c1, c2, c3, c4 = st.columns(4)
        revenue = c1.number_input("Attributed revenue", min_value=0.0, value=10_000_000.0)
        spend = c2.number_input("Ad spend", min_value=0.0, value=2_000_000.0)
        orders = c3.number_input("Attributed orders", min_value=0, value=25)
        contribution = c4.number_input(
            "Contribution before ads", value=3_000_000.0
        )
        submitted = st.form_submit_button("Calculate ad economics", type="primary")
    if submitted:
        _run_safely(
            calculate_ad_performance,
            "phase_one_ads_result",
            attributed_revenue=revenue,
            ad_spend=spend,
            attributed_orders=int(orders),
            contribution_before_ads=contribution,
        )
    result = st.session_state.get("phase_one_ads_result")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("ROAS", f"{result['roas']:.2f}x" if result["roas"] is not None else "Unavailable")
        c2.metric("Cost / attributed order", _money(result["cost_per_attributed_order"]))
        c3.metric("Contribution after ads", _money(result["contribution_after_ads"]))
        if not result["profitable"]:
            st.warning("This campaign does not cover its ad spend from contribution.")


def render_phase_one_workspace() -> None:
    st.header("Phase 1 · Restaurant audit & profit foundation")
    st.write(
        "Diagnose discovery, operations, costs, pricing, menu, bundles and "
        "marketing. Use Platform Report Analysis below to import Toters or "
        "Uber Eats data."
    )
    discovery, operations, profit, menu, marketing = st.tabs(
        ["Discovery", "Operations", "Profit & pricing", "Menu & bundles", "Marketing"]
    )
    with discovery:
        _render_discovery()
    with operations:
        _render_operations()
    with profit:
        _render_profit_and_pricing()
    with menu:
        _render_menu_iq()
    with marketing:
        _render_marketing()


def _promotion_form() -> None:
    st.markdown("### Build and test an offer")
    st.info(
        "Incrementality is an estimate against the baseline you enter; it is "
        "not a causal claim. Use matched periods and retest before scaling."
    )
    with st.form("phase_two_promotion"):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Promotion name", value="Weekday bundle test")
        offer_type = c2.selectbox(
            "Offer type",
            ["Discount", "Bundle", "Free item", "Minimum-spend offer"],
        )
        product = c3.text_input("Product / bundle", value="Hero + drink")
        c4, c5, c6 = st.columns(3)
        baseline_orders = c4.number_input("Baseline orders", min_value=0, value=100)
        promotion_orders = c5.number_input("Promotion orders", min_value=0, value=135)
        list_price = c6.number_input("List price / order", min_value=0.0, value=900_000.0)
        c7, c8, c9 = st.columns(3)
        discount = c7.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=15.0)
        fee = c8.number_input("Platform fee (%)", min_value=0.0, max_value=100.0, value=25.0)
        cogs = c9.number_input("COGS / order", min_value=0.0, value=280_000.0)
        c10, c11, c12 = st.columns(3)
        packaging = c10.number_input("Packaging / order", min_value=0.0, value=30_000.0)
        ad_spend = c11.number_input("Campaign ad spend", min_value=0.0, value=2_000_000.0)
        cannibalization = c12.number_input(
            "Estimated cannibalization loss", min_value=0.0, value=0.0
        )
        c13, c14, c15 = st.columns(3)
        minimum_spend = c13.number_input("Minimum spend", min_value=0.0, value=0.0)
        timing = c14.text_input("Day / time window", value="Mon–Thu, 2–5pm")
        duration = c15.number_input("Duration (days)", min_value=1, value=7)
        submitted = st.form_submit_button("Calculate and add to MVP ranking", type="primary")
    if submitted:
        try:
            scenario = calculate_promotion_scenario(
                name=name,
                baseline_orders=int(baseline_orders),
                promotion_orders=int(promotion_orders),
                list_price=list_price,
                discount_rate=discount / 100,
                platform_fee_rate=fee / 100,
                unit_cogs=cogs,
                packaging=packaging,
                ad_spend=ad_spend,
                cannibalization_loss=cannibalization,
                offer_type=offer_type,
                product=product,
                minimum_spend=minimum_spend,
                timing=timing,
                duration_days=int(duration),
            )
            scenarios = st.session_state.setdefault("phase_two_scenarios", [])
            scenarios.append(scenario)
            st.session_state["phase_two_latest"] = scenario
        except ValueError as error:
            st.error(str(error))
    result = st.session_state.get("phase_two_latest")
    if result:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Incremental orders", f"{result['incremental_orders']:+,}")
        c2.metric("Promo contribution / order", _money(result["promotion_unit_contribution"]))
        c3.metric("Net incremental contribution", _money(result["net_incremental_contribution"]))
        c4.metric("MVP score", _money(result["mvp_score"]))
        st.write(
            "Break-even promotion volume: "
            + (
                f"{result['break_even_promotion_orders']:,} orders"
                if result["break_even_promotion_orders"] is not None
                else "unreachable because unit contribution is not positive"
            )
        )


def _offer_guardrails() -> None:
    st.markdown("### Minimum-spend guardrail")
    st.caption(
        "For fixed-value offers, this computes the basket needed to cover "
        "variable cost, the discount and a target contribution."
    )
    with st.form("phase_two_threshold"):
        c1, c2, c3, c4 = st.columns(4)
        variable_cost = c1.number_input("Basket variable cost", min_value=0.0, value=300_000.0)
        fixed_discount = c2.number_input("Fixed discount", min_value=0.0, value=100_000.0)
        fee = c3.number_input("Threshold platform fee (%)", min_value=0.0, max_value=99.0, value=25.0)
        target = c4.number_input("Target basket contribution", min_value=0.0, value=250_000.0)
        submitted = st.form_submit_button("Recommend minimum spend")
    if submitted:
        _run_safely(
            calculate_minimum_spend_threshold,
            "phase_two_threshold_result",
            variable_cost=variable_cost,
            fixed_discount=fixed_discount,
            platform_fee_rate=fee / 100,
            target_contribution=target,
        )
    result = st.session_state.get("phase_two_threshold_result")
    if result is not None:
        st.metric("Recommended minimum spend", _money(result))


def _mvp_leaderboard() -> None:
    st.markdown("### Most Valuable Promotion leaderboard")
    scenarios = st.session_state.get("phase_two_scenarios", [])
    if not scenarios:
        st.info("Add at least one tested offer in the Simulator tab.")
        return
    ranked = rank_promotions(scenarios)
    rows = [
        {
            "Rank": item["rank"],
            "Promotion": item["name"],
            "Mechanic": item["offer_type"],
            "Product": item["product"],
            "Incremental orders": item["incremental_orders"],
            "Net incremental contribution": _money(item["net_incremental_contribution"]),
            "MVP score": _money(item["mvp_score"]),
            "Recommendation": item["recommendation"],
        }
        for item in ranked
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    best = ranked[0]
    st.success(f"Next decision: {best['name']} — {best['recommendation']}")
    st.caption(
        "Test → learn → scale: change one mechanic at a time, use a comparable "
        "baseline, and add the next result to this leaderboard."
    )
    if st.button("Clear promotion test history"):
        st.session_state["phase_two_scenarios"] = []
        st.session_state.pop("phase_two_latest", None)
        st.rerun()


def _profit_target() -> None:
    st.markdown("### 17% net-profit target")
    with st.form("phase_two_target"):
        c1, c2, c3 = st.columns(3)
        period = c1.text_input("Period label", value="Current month")
        revenue = c2.number_input("Business revenue", min_value=0.0, value=100_000_000.0)
        profit = c3.number_input("Net profit", value=8_000_000.0)
        submitted = st.form_submit_button("Calculate and track progress", type="primary")
    if submitted:
        try:
            progress = calculate_margin_progress(revenue=revenue, net_profit=profit)
            progress["period"] = period
            st.session_state["phase_two_progress"] = progress
            history = st.session_state.setdefault("phase_two_progress_history", [])
            history.append(dict(progress))
        except ValueError as error:
            st.error(str(error))
    result = st.session_state.get("phase_two_progress")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Current net margin", _percent(result["current_margin_rate"]))
        c2.metric("Target", "17.0%")
        c3.metric("Margin gap", _percent(result["gap_rate"]))
        if result["target_reached"]:
            st.success("The 17% target is reached for this period.")
        else:
            st.warning(f"Additional net profit required: {_money(result['profit_gap'])}")
    history = st.session_state.get("phase_two_progress_history", [])
    if history:
        st.markdown("#### Progress history")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Period": item["period"],
                        "Net margin": _percent(item["current_margin_rate"]),
                        "Gap to 17%": _percent(item["gap_rate"]),
                        "Profit gap": _money(item["profit_gap"]),
                    }
                    for item in history
                ]
            ),
            hide_index=True,
            width="stretch",
        )


def render_phase_two_workspace() -> None:
    st.header("Phase 2 · Most Valuable Promotion")
    st.write(
        "Design offers, estimate true incremental contribution after discount, "
        "platform commission, COGS, packaging, ads and cannibalization, then "
        "rank tests by profit rather than order volume."
    )
    simulator, guardrails, leaderboard, target = st.tabs(
        ["Promotion simulator", "Offer guardrails", "MVP ranking", "17% target"]
    )
    with simulator:
        _promotion_form()
    with guardrails:
        _offer_guardrails()
    with leaderboard:
        _mvp_leaderboard()
    with target:
        _profit_target()
