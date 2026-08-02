import pandas as pd
import streamlit as st
from application.dto.analysis_result import AnalysisResult
from application.services.health_score_service import HealthScoreService
from application.services.import_service import ImportService
from application.services.order_consolidation import consolidate_orders
from data.schemas.uber_eats import UBER_EATS_REQUIRED_COLUMNS
from utils.analyser import analyse_delivery_platform
from utils.loader import load_file
from utils.mapper import map_uber_eats
from utils.validation import (
    validate_required_columns,
    validate_restaurant_name,
)


st.set_page_config(
    page_title="KitchenIQ",
    page_icon="🍽️",
    layout="wide",
)


def format_lbp(value: float) -> str:
    """
    Format Lebanese pound values so they fit inside metric cards.
    """
    value = float(value or 0)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B LBP"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M LBP"

    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K LBP"

    return f"{value:,.0f} LBP"


def format_rate(value) -> str:
    """
    Format a decimal rate as a percentage.
    """
    if value is None:
        return "Unavailable"

    return f"{value:.1%}"


def render_kpi(
    container,
    label: str,
    value: str,
    formula: str,
    definition: str,
) -> None:
    """
    Render one KPI metric with concise formula and definition help.
    """
    container.metric(
        label,
        value,
        help=(
            f"Formula: {formula}\n\n"
            f"Definition: {definition}"
        ),
    )


def format_evidence_value(
    key: str,
    value,
) -> str:
    """
    Format diagnostic evidence according to its metric type.
    """
    if value is None:
        return "Unavailable"

    if "rate" in key and isinstance(
        value,
        (int, float),
    ):
        return f"{value:.1%}"

    money_keys = {
        "gross_revenue",
        "net_order_revenue",
        "total_platform_cost",
        "total_marketing_cost",
        "total_listing_fee",
        "average_order_value",
        "average_net_order_value",
    }

    if (
        key in money_keys
        and isinstance(value, (int, float))
    ):
        return format_lbp(value)

    if isinstance(value, float):
        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def display_problem_section(
    problems: list,
) -> None:
    """
    Display structured diagnostic problems.
    """
    st.subheader("Detected Problems")

    if not problems:
        st.success(
            "No problems were detected using the current "
            "diagnostic rules."
        )
        return

    for problem in problems:
        severity = problem.get(
            "severity",
            "medium",
        ).lower()

        title = problem.get(
            "title",
            "Detected problem",
        )

        problem_message = problem.get(
            "message",
            "",
        )

        business_area = problem.get(
            "business_area",
            "general",
        )

        evidence = problem.get(
            "evidence",
            {},
        )

        if severity == "high":
            st.error(
                f"High Priority — {title}"
            )

        elif severity == "medium":
            st.warning(
                f"Medium Priority — {title}"
            )

        else:
            st.info(
                f"Low Priority — {title}"
            )

        st.caption(
            "Business area: "
            + business_area.replace(
                "_",
                " ",
            ).title()
        )

        st.write(
            problem_message
        )

        with st.expander(
            "View supporting evidence"
        ):
            if not evidence:
                st.write(
                    "No supporting evidence was provided."
                )

            for key, value in evidence.items():
                label = key.replace(
                    "_",
                    " ",
                ).title()

                formatted_value = (
                    format_evidence_value(
                        key,
                        value,
                    )
                )

                st.write(
                    f"**{label}:** {formatted_value}"
                )


def display_recommendation_section(
    recommendations: list,
) -> None:
    """
    Display structured operational recommendations.
    """
    st.subheader("Recommended Actions")

    if not recommendations:
        st.info(
            "No recommendations were generated because "
            "no current diagnostic rule was triggered."
        )
        return

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):
        title = recommendation.get(
            "title",
            "Recommendation",
        )

        priority = recommendation.get(
            "priority",
            "Not specified",
        )

        expected_impact = recommendation.get(
            "expected_impact",
            "Not specified",
        )

        st.markdown(
            f"### {index}. {title}"
        )

        col1, col2 = st.columns(2)

        col1.write(
            f"**Priority:** {priority.title()}"
        )

        col2.write(
            "**Metric to monitor:** "
            + recommendation.get(
                "metric_to_monitor",
                "Not specified",
            ).replace(
                "_",
                " ",
            ).title()
        )

        st.write(
            f"**Expected impact:** {expected_impact}"
        )

        actions = recommendation.get(
            "actions",
            [],
        )

        if actions:
            st.write(
                "**Recommended actions:**"
            )

            for action in actions:
                st.markdown(
                    f"- {action}"
                )

        st.divider()


def display_uber_analysis(
    restaurant: str,
    data,
    analysis: dict,
) -> None:
    """
    Display the Uber Eats analysis dashboard.
    """
    kpis = analysis["kpis"]
    problems = analysis["problems"]
    recommendations = analysis["recommendations"]

    st.success(
        f"Welcome {restaurant}! "
        "KitchenIQ has analysed your Uber Eats report."
    )

    st.caption(
        f"Uber Eats report · "
        f"{data.shape[0]} rows · "
        f"{data.shape[1]} columns"
    )

    st.subheader(
        "Performance Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Orders",
        f"{kpis.get('total_orders', 0):,}",
    )

    col2.metric(
        "Gross Sales",
        f"€{kpis.get('gross_sales', 0):,.2f}",
    )

    col3.metric(
        "Net Sales",
        f"€{kpis.get('net_sales', 0):,.2f}",
    )

    col4.metric(
        "Commission Paid",
        f"€{kpis.get('total_commission', 0):,.2f}",
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Average Order Value",
        f"€{kpis.get('average_order_value', 0):,.2f}",
    )

    col6.metric(
        "Commission Rate",
        format_rate(
            kpis.get(
                "commission_rate"
            )
        ),
    )

    average_rating = kpis.get(
        "average_customer_rating"
    )

    col7.metric(
        "Average Rating",
        (
            f"{average_rating:.2f} / 5"
            if average_rating is not None
            else "Unavailable"
        ),
    )

    period_days = kpis.get(
        "period_days"
    )

    col8.metric(
        "Analysis Period",
        (
            f"{period_days} days"
            if period_days is not None
            else "Unavailable"
        ),
    )

    display_problem_section(
        problems
    )

    display_recommendation_section(
        recommendations
    )

    with st.expander(
        "View normalised Uber Eats report"
    ):
        st.dataframe(
            data,
            width="stretch",
            hide_index=True,
        )


def build_executive_summary(
    restaurant: str,
    analysis_result: AnalysisResult,
) -> str:
    """
    Create a deterministic executive summary from the current Toters metrics.
    """
    metrics = analysis_result.metrics

    gross_revenue = format_lbp(
        metrics.get("gross_revenue", 0.0)
    )
    total_orders = f"{metrics.get('total_orders', 0):,}"
    retained_rate = format_rate(
        metrics.get("retained_revenue_rate")
    )

    diagnostics = analysis_result.diagnostics or []
    issue_titles = [
        problem.get("title", "an identified issue")
        for problem in diagnostics[:2]
        if problem.get("title")
    ]

    if len(issue_titles) >= 2:
        issue_text = f"{issue_titles[0]} and {issue_titles[1]}"
        return (
            f"{restaurant} generated {gross_revenue} from "
            f"{total_orders} Toters orders during the analysed period. "
            f"The restaurant retained {retained_rate} of gross revenue "
            f"after recorded platform deductions. The main areas requiring "
            f"attention are {issue_text}."
        )

    if len(issue_titles) == 1:
        return (
            f"{restaurant} generated {gross_revenue} from "
            f"{total_orders} Toters orders during the analysed period. "
            f"The restaurant retained {retained_rate} of gross revenue "
            f"after recorded platform deductions. The main area requiring "
            f"attention is {issue_titles[0]}."
        )

    return (
        f"{restaurant} generated {gross_revenue} from "
        f"{total_orders} Toters orders during the analysed period. "
        f"The restaurant retained {retained_rate} of gross revenue "
        f"after recorded platform deductions."
    )


def display_toters_results(
    restaurant: str,
    analysis_result: AnalysisResult,
) -> None:
    """
    Display Toters KPIs, diagnostic findings and recommendations.
    """
    metrics = analysis_result.metrics
    problems = analysis_result.diagnostics
    recommendations = analysis_result.recommendations
    health_score = HealthScoreService().calculate(analysis_result)

    st.success(
        f"Welcome {restaurant}! "
        "KitchenIQ has consolidated and analysed your "
        "Toters invoice report."
    )

    st.caption(
        f"Toters report · "
        f"{metrics.get('total_orders', 0):,} consolidated orders · "
        f"{len(analysis_result.records)} imported records"
    )

    st.subheader("Executive Summary")
    st.write(
        build_executive_summary(
            restaurant,
            analysis_result,
        )
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Health Score",
        f"{health_score.score}/100",
    )

    col2.metric(
        "Health Label",
        health_score.label,
    )

    st.markdown("**Interpretation**")
    st.write(health_score.interpretation)

    st.subheader("Top Three Priorities")

    for index, problem in enumerate(
        problems[:3],
        start=1,
    ):
        severity = problem.get(
            "severity",
            "medium",
        ).title()

        title = problem.get(
            "title",
            "Priority",
        )

        business_area = (
            problem.get(
                "business_area",
                "general",
            )
            .replace("_", " ")
            .title()
        )

        description = problem.get(
            "message",
            "",
        )

        st.markdown(f"### {index}. {title}")
        st.write(f"**Severity:** {severity}")
        st.write(f"**Business area:** {business_area}")
        st.write(description)
        st.divider()

    period_days = metrics.get("period_days")
    period_display = (
        f"{period_days} days"
        if period_days is not None
        else "Unavailable"
    )

    # -------------------------------------------------------------
    # OVERVIEW
    # -------------------------------------------------------------
    st.subheader("📊 Overview")

    overview_col1, overview_col2, overview_col3, overview_col4 = (
        st.columns(4)
    )

    render_kpi(
        overview_col1,
        "Total Orders",
        f"{metrics.get('total_orders', 0):,}",
        "Count of unique consolidated order IDs",
        "Number of customer orders identified in the Toters report.",
    )

    render_kpi(
        overview_col2,
        "Gross Revenue",
        format_lbp(metrics.get("gross_revenue", 0.0)),
        "Σ Gross Revenue",
        "Total customer spending before Toters deductions.",
    )

    render_kpi(
        overview_col3,
        "Net Revenue",
        format_lbp(metrics.get("net_order_revenue", 0.0)),
        "Gross Revenue − Total Platform Cost",
        "Revenue remaining after recorded Toters deductions.",
    )

    render_kpi(
        overview_col4,
        "Revenue Kept",
        format_rate(metrics.get("retained_revenue_rate")),
        "Net Revenue ÷ Gross Revenue",
        "Share of customer spending retained by the restaurant.",
    )

    overview_col5, overview_col6, overview_col7 = st.columns(3)

    render_kpi(
        overview_col5,
        "Total Platform Cost",
        format_lbp(metrics.get("total_platform_cost", 0.0)),
        "Listing Fees + Marketing Cost + VAT + Other Costs",
        "Total recorded cost of operating through Toters.",
    )

    render_kpi(
        overview_col6,
        "Average Order Value",
        format_lbp(metrics.get("average_order_value", 0.0)),
        "Gross Revenue ÷ Total Orders",
        "Average customer spend per order before deductions.",
    )

    render_kpi(
        overview_col7,
        "Analysis Period",
        period_display,
        "Max Order Date − Min Order Date + 1",
        "Number of days covered by the consolidated orders.",
    )

    # -------------------------------------------------------------
    # FINANCIAL PERFORMANCE
    # -------------------------------------------------------------
    st.subheader("💰 Financial Performance")

    financial_col1, financial_col2, financial_col3, financial_col4 = (
        st.columns(4)
    )

    render_kpi(
        financial_col1,
        "Gross Revenue",
        format_lbp(metrics.get("gross_revenue", 0.0)),
        "Σ Gross Revenue",
        "Total customer spending before Toters deductions.",
    )

    render_kpi(
        financial_col2,
        "Net Revenue",
        format_lbp(metrics.get("net_order_revenue", 0.0)),
        "Gross Revenue − Total Platform Cost",
        "Revenue remaining after recorded Toters deductions.",
    )

    render_kpi(
        financial_col3,
        "Revenue Kept",
        format_rate(metrics.get("retained_revenue_rate")),
        "Net Revenue ÷ Gross Revenue",
        "Share of customer spending retained by the restaurant.",
    )

    render_kpi(
        financial_col4,
        "Total Platform Cost",
        format_lbp(metrics.get("total_platform_cost", 0.0)),
        "Listing Fees + Marketing Cost + VAT + Other Costs",
        "Total recorded cost of operating through Toters.",
    )

    financial_col5, financial_col6, financial_col7, financial_col8 = (
        st.columns(4)
    )

    render_kpi(
        financial_col5,
        "Platform Cost Rate",
        format_rate(metrics.get("platform_cost_rate")),
        "Total Platform Cost ÷ Gross Revenue",
        "Share of gross revenue absorbed by all Toters costs.",
    )

    render_kpi(
        financial_col6,
        "Listing Fees Paid",
        format_lbp(metrics.get("total_listing_fee", 0.0)),
        "Σ Listing Fees",
        "Total commission amount charged by Toters.",
    )

    render_kpi(
        financial_col7,
        "Effective Commission Rate",
        format_rate(metrics.get("listing_fee_rate")),
        "Listing Fees Paid ÷ Gross Revenue",
        "Actual commission rate calculated from the invoice.",
    )

    render_kpi(
        financial_col8,
        "VAT Paid",
        format_lbp(metrics.get("total_vat", 0.0)),
        "Σ VAT",
        "Total VAT charged on Toters fees and services.",
    )

    financial_col9, financial_col10, financial_col11 = st.columns(3)

    render_kpi(
        financial_col9,
        "Average Net Order Value",
        format_lbp(metrics.get("average_net_order_value", 0.0)),
        "Net Revenue ÷ Total Orders",
        "Average revenue retained by the restaurant per order.",
    )

    render_kpi(
        financial_col10,
        "Minimum Order Value",
        format_lbp(metrics.get("minimum_order_value", 0.0)),
        "Minimum of Positive Gross Order Values",
        "Lowest positive customer order value.",
    )

    render_kpi(
        financial_col11,
        "Maximum Order Value",
        format_lbp(metrics.get("maximum_order_value", 0.0)),
        "Maximum Gross Order Value",
        "Highest customer order value.",
    )

    # -------------------------------------------------------------
    # MARKETING PERFORMANCE
    # -------------------------------------------------------------
    st.subheader("📣 Marketing Performance")

    # -------------------------------------------------------------
    # MARKETING SUMMARY
    # -------------------------------------------------------------
    marketing_col1, marketing_col2, marketing_col3, marketing_col4 = (
        st.columns(4)
    )

    render_kpi(
        marketing_col1,
        "Marketing Cost",
        format_lbp(metrics.get("total_marketing_cost", 0.0)),
        "Σ Net Marketing Deductions",
        "Net marketing cost charged after recorded promotion credits.",
    )

    render_kpi(
        marketing_col2,
        "Marketing Cost Rate",
        format_rate(metrics.get("marketing_cost_rate")),
        "Marketing Cost ÷ Gross Revenue",
        "Share of gross revenue absorbed by net marketing deductions.",
    )

    render_kpi(
        marketing_col3,
        "Orders With Marketing",
        f"{metrics.get('orders_with_marketing', 0):,}",
        "Count of Orders With Marketing Cost > 0",
        "Number of orders carrying at least one net marketing deduction.",
    )

    render_kpi(
        marketing_col4,
        "Marketing Order Share",
        format_rate(metrics.get("marketing_order_share")),
        "Orders With Marketing ÷ Total Orders",
        "Share of all orders affected by marketing deductions.",
    )

    # -------------------------------------------------------------
    # MARKETING COST STRUCTURE
    # -------------------------------------------------------------
    st.markdown("#### Marketing Cost Structure")

    promotion_col1, promotion_col2, promotion_col3 = st.columns(3)

    render_kpi(
        promotion_col1,
        "Discount Promotions",
        format_lbp(metrics.get("net_promotion_spend", 0.0)),
        "Gross Discount Promotions − Promotion Credits",
        (
            "Net cost of immediate discounts, fixed-price campaigns, "
            "free delivery and punch-card promotions."
        ),
    )

    render_kpi(
        promotion_col2,
        "Platform Advertising",
        format_lbp(metrics.get("total_marketing_highlight", 0.0)),
        "Σ Marketing Highlight",
        "Advertising and paid visibility purchased through Toters.",
    )

    render_kpi(
        promotion_col3,
        "Total Marketing Spend",
        format_lbp(metrics.get("total_marketing_cost", 0.0)),
        "Discount Promotions + Platform Advertising",
        "Total net marketing cost charged through Toters.",
    )

    # -------------------------------------------------------------
    # PROMOTION TYPE BREAKDOWN
    # -------------------------------------------------------------
    st.markdown("#### Promotion Type Breakdown")

    (
        promotion_type_col1,
        promotion_type_col2,
        promotion_type_col3,
        promotion_type_col4,
    ) = st.columns(4)

    render_kpi(
        promotion_type_col1,
        "Immediate Discounts",
        format_lbp(metrics.get("total_marketing_discount", 0.0)),
        "Σ Marketing Immediate Discount",
        "Customer discounts charged through immediate-discount campaigns.",
    )

    render_kpi(
        promotion_type_col2,
        "Fixed Price Promotions",
        format_lbp(metrics.get("total_marketing_fixed_price", 0.0)),
        "Σ Marketing Item Fixed Price",
        "Cost of campaigns selling selected products at fixed prices.",
    )

    render_kpi(
        promotion_type_col3,
        "Free Delivery",
        format_lbp(metrics.get("total_marketing_free_delivery", 0.0)),
        "Σ Marketing Free Delivery",
        "Restaurant-funded cost of free-delivery promotions.",
    )

    render_kpi(
        promotion_type_col4,
        "Punch Card",
        format_lbp(metrics.get("total_marketing_punch_card", 0.0)),
        "Σ Marketing Punch Card",
        "Cost of loyalty or repeat-purchase punch-card promotions.",
    )

    promotion_type_col5 = st.columns(1)[0]

    render_kpi(
        promotion_type_col5,
        "Marketing Highlight",
        format_lbp(metrics.get("total_marketing_highlight", 0.0)),
        "Σ Marketing Highlight",
        "Cost of paid visibility or highlighted placement on Toters.",
    )

    promotion_type_col7 = st.columns(1)[0]

    render_kpi(
        promotion_type_col7,
        "Highlight Credit Notes",
        format_lbp(
            abs(
                metrics.get(
                    "total_marketing_highlight_credit_note",
                    0.0,
                )
            )
        ),
        "|Σ Marketing Highlights Credit Note|",
        "Credits that reduce previously charged highlight costs.",
    )

    # -------------------------------------------------------------
    # PROMOTION PROFITABILITY
    # -------------------------------------------------------------
    st.markdown("#### Promotion Profitability")

    profitability_col1, profitability_col2 = st.columns(2)

    render_kpi(
        profitability_col1,
        "Commission on Promotions",
        format_lbp(
            metrics.get(
                "total_commission_on_promotions",
                0.0,
            )
        ),
        (
            "Discount Promotions "
            "× Effective Commission Rate"
        ),
        (
            "Commission attributable to immediate discounts "
            "and fixed-price promotions."
        ),
    )

    render_kpi(
        profitability_col2,
        "Fully Loaded Promotion Cost",
        format_lbp(
            metrics.get(
                "true_promotion_cost",
                0.0,
            )
        ),
        "Net Promotion Spend + Commission on Promotions",
        (
            "Total economic cost of discount promotions after "
            "credits and attributable commission."
        ),
    )

    st.subheader("Toters Processing Status")

    st.success(
        "The Toters invoice ledger has been validated, "
        "consolidated, analysed and diagnosed successfully."
    )

    display_problem_section(problems)
    display_recommendation_section(recommendations)

    with st.expander(
        "Commission Base Audit",
        expanded=False,
    ):
        consolidated_orders = consolidate_orders(
            analysis_result.records
        )

        if consolidated_orders.empty:
            st.info(
                "No consolidated orders are available "
                "for commission auditing."
            )
        else:
            audit_data = consolidated_orders.copy()

            audit_data["promotion_discount"] = (
                audit_data["marketing_discount"]
                + audit_data["marketing_fixed_price"]
            )

            audit_data["revenue_after_discount"] = (
                audit_data["gross_revenue"]
                - audit_data["promotion_discount"]
            )

            audit_data["commission_rate_on_gross"] = (
                audit_data["store_listing_fee"]
                / audit_data["gross_revenue"].where(
                    audit_data["gross_revenue"] > 0
                )
            )

            audit_data["commission_rate_after_discount"] = (
                audit_data["store_listing_fee"]
                / audit_data["revenue_after_discount"].where(
                    audit_data["revenue_after_discount"] > 0
                )
            )

            gross_revenue_total = audit_data[
                "gross_revenue"
            ].sum()

            adjusted_revenue_total = audit_data[
                "revenue_after_discount"
            ].sum()

            listing_fee_total = audit_data[
                "store_listing_fee"
            ].sum()

            weighted_rate_on_gross = (
                listing_fee_total / gross_revenue_total
                if gross_revenue_total > 0
                else None
            )

            weighted_rate_after_discount = (
                listing_fee_total / adjusted_revenue_total
                if adjusted_revenue_total > 0
                else None
            )

            audit_col1, audit_col2 = st.columns(2)

            audit_col1.metric(
                "Weighted Rate on Gross Revenue",
                format_rate(weighted_rate_on_gross),
            )

            audit_col2.metric(
                "Weighted Rate After Discounts",
                format_rate(weighted_rate_after_discount),
            )

            audit_columns = [
                "order_id",
                "gross_revenue",
                "promotion_discount",
                "revenue_after_discount",
                "store_listing_fee",
                "commission_rate_on_gross",
                "commission_rate_after_discount",
            ]

            st.dataframe(
                audit_data[audit_columns],
                width="stretch",
                hide_index=True,
            )

    with st.expander(
        "View consolidated Toters orders",
        expanded=False,
    ):
        if analysis_result.records:
            display_data = pd.DataFrame(
                [
                    {
                        "source_row_number": record.source_row_number,
                        "occurred_at": record.occurred_at,
                        "source_category": record.source_category,
                        "event_type": record.event_type,
                        "signed_amount": str(record.signed_amount),
                        "currency": record.currency,
                    }
                    for record in analysis_result.records
                ]
            )
        else:
            display_data = pd.DataFrame()

        st.dataframe(
            display_data,
            width="stretch",
            hide_index=True,
        )

st.caption("Build: 2026-08-02 financial-reconciliation-v2")

st.title(
    "🍽️ KitchenIQ"
)

st.subheader(
    "AI Operational Intelligence for Restaurants"
)

st.divider()


restaurant_name = st.text_input(
    "Restaurant Name"
)


platform = st.selectbox(
    "Delivery Platform",
    [
        "Uber Eats",
        "Toters",
        "Deliveroo",
        "Just Eat",
    ],
)


uploaded_file = st.file_uploader(
    "Upload Restaurant Report",
    type=[
        "csv",
        "xlsx",
    ],
)


if st.button(
    "Analyse Restaurant",
    type="primary",
):
    valid, message = (
        validate_restaurant_name(
            restaurant_name
        )
    )

    if not valid:
        st.error(
            message
        )
        st.stop()

    if uploaded_file is None:
        st.error(
            "Please upload a restaurant report."
        )
        st.stop()

    try:
        raw_data = load_file(
            uploaded_file
        )

    except Exception as error:
        st.error(
            "KitchenIQ could not read this file: "
            f"{error}"
        )
        st.stop()

    if raw_data is None:
        st.error(
            "KitchenIQ could not read this file."
        )
        st.stop()

    # -------------------------------------------------------------
    # UBER EATS
    # -------------------------------------------------------------
    if platform == "Uber Eats":
        try:
            data = map_uber_eats(
                raw_data
            )

        except Exception as error:
            st.error(
                "KitchenIQ could not map this Uber Eats "
                f"report: {error}"
            )
            st.stop()

        valid_columns, column_message = (
            validate_required_columns(
                data,
                UBER_EATS_REQUIRED_COLUMNS,
            )
        )

        if not valid_columns:
            st.error(
                column_message
            )
            st.stop()

        try:
            analysis = analyse_delivery_platform(
                data
            )

        except Exception as error:
            st.error(
                "KitchenIQ could not analyse this Uber Eats "
                f"report: {error}"
            )
            st.stop()

        display_uber_analysis(
            restaurant=restaurant_name,
            data=data,
            analysis=analysis,
        )

    # -------------------------------------------------------------
    # TOTERS
    # -------------------------------------------------------------
    elif platform == "Toters":
        # Schema validation is owned by the Toters connector so there is a
        # single, authoritative source of truth for required columns.
        try:
            import_service = ImportService()
            analysis_result = import_service.run_toters_import(
                dataframe=raw_data,
                restaurant_name=restaurant_name,
                platform=platform,
            )

            st.write("### DEBUG – Raw Metrics")
            st.json(analysis_result.metrics)

        except ValueError as error:
            st.error(
                str(error)
            )
            st.stop()

        except Exception as error:
            st.error(
                "KitchenIQ could not process this Toters "
                f"report: {error}"
            )
            st.stop()

        try:
            display_toters_results(
                restaurant=restaurant_name,
                analysis_result=analysis_result,
            )

        except ValueError as error:
            st.error(
                str(error)
            )
            st.stop()

        except Exception as error:
            st.error(
                "KitchenIQ could not calculate, diagnose "
                "or recommend actions for the Toters report: "
                f"{error}"
            )
            st.stop()

    # -------------------------------------------------------------
    # NOT YET SUPPORTED
    # -------------------------------------------------------------
    else:
        st.warning(
            f"{platform} is listed in KitchenIQ, "
            "but its connector has not been built yet."
        )

        st.info(
            "Please select Uber Eats or Toters "
            "for the current version."
        )
# Deployment marker: order-count-fix-d071bf4

# Deployment marker: full-financial-reconciliation-ui
