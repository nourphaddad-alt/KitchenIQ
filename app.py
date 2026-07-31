import pandas as pd
import streamlit as st
from application.dto.analysis_result import AnalysisResult
from application.services.health_score_service import HealthScoreService
from application.services.import_service import ImportService
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

    st.subheader("Toters Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Orders",
        f"{metrics.get('total_orders', 0):,}",
    )

    col2.metric(
        "Gross Revenue",
        format_lbp(metrics.get("gross_revenue", 0.0)),
    )

    col3.metric(
        "Net Order Revenue",
        format_lbp(metrics.get("net_order_revenue", 0.0)),
    )

    col4.metric(
        "Total Platform Cost",
        format_lbp(metrics.get("total_platform_cost", 0.0)),
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Average Order Value",
        format_lbp(metrics.get("average_order_value", 0.0)),
    )

    col6.metric(
        "Platform Cost Rate",
        format_rate(metrics.get("platform_cost_rate")),
    )

    col7.metric(
        "Marketing Cost",
        format_lbp(metrics.get("total_marketing_cost", 0.0)),
    )

    col8.metric(
        "Marketing Cost Rate",
        format_rate(metrics.get("marketing_cost_rate")),
    )

    col9, col10, col11, col12 = st.columns(4)

    col9.metric(
        "Listing Fee Rate",
        format_rate(metrics.get("listing_fee_rate")),
    )

    col10.metric(
        "Retained Revenue Rate",
        format_rate(metrics.get("retained_revenue_rate")),
    )

    col11.metric(
        "Orders With Marketing",
        f"{metrics.get('orders_with_marketing', 0):,}",
    )

    col12.metric(
        "Marketing Order Share",
        format_rate(metrics.get("marketing_order_share")),
    )

    st.subheader("Additional Toters Insights")

    col13, col14, col15, col16 = st.columns(4)

    col13.metric(
        "Average Net Order Value",
        format_lbp(metrics.get("average_net_order_value", 0.0)),
    )

    col14.metric(
        "Median Order Value",
        format_lbp(metrics.get("median_order_value", 0.0)),
    )

    col15.metric(
        "Listing Fees Paid",
        format_lbp(metrics.get("total_listing_fee", 0.0)),
    )

    col16.metric(
        "VAT Paid",
        format_lbp(metrics.get("total_vat", 0.0)),
    )

    col17, col18, col19 = st.columns(3)

    col17.metric(
        "Minimum Order Value",
        format_lbp(metrics.get("minimum_order_value", 0.0)),
    )

    col18.metric(
        "Maximum Order Value",
        format_lbp(metrics.get("maximum_order_value", 0.0)),
    )

    period_days = metrics.get("period_days")

    col19.metric(
        "Analysis Period",
        f"{period_days} days" if period_days is not None else "Unavailable",
    )

    st.subheader("Toters Processing Status")

    st.success(
        "The Toters invoice ledger has been validated, "
        "consolidated, analysed and diagnosed successfully."
    )

    display_problem_section(problems)
    display_recommendation_section(recommendations)

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