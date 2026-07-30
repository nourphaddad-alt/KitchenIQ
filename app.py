import streamlit as st

from data.schemas.toters import TOTERS_REQUIRED_COLUMNS
from data.schemas.uber_eats import UBER_EATS_REQUIRED_COLUMNS
from utils.analyser import analyse_delivery_platform
from utils.loader import load_file
from utils.mapper import map_uber_eats
from utils.toters_mapper import map_toters
from utils.validation import (
    validate_required_columns,
    validate_restaurant_name,
)


st.set_page_config(
    page_title="KitchenIQ",
    page_icon="🍽️",
    layout="wide",
)


st.title("🍽️ KitchenIQ")
st.subheader("AI Operational Intelligence for Restaurants")
st.divider()


restaurant_name = st.text_input("Restaurant Name")


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
    type=["csv", "xlsx"],
)


def display_uber_analysis(
    restaurant: str,
    platform_name: str,
    data,
    analysis: dict,
) -> None:
    """
    Display Uber Eats KPIs, detected problems and recommendations.
    """
    kpis = analysis["kpis"]
    problems = analysis["problems"]
    recommendations = analysis["recommendations"]

    st.success(
        f"Welcome {restaurant}! "
        "KitchenIQ has analysed your Uber Eats report."
    )

    st.caption(
        f"{platform_name} report · "
        f"{data.shape[0]} rows · "
        f"{data.shape[1]} columns"
    )

    st.subheader("Performance Overview")

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

    commission_rate = kpis.get("commission_rate")

    col6.metric(
        "Commission Rate",
        (
            f"{commission_rate:.1%}"
            if commission_rate is not None
            else "Unavailable"
        ),
    )

    average_rating = kpis.get("average_customer_rating")

    col7.metric(
        "Average Rating",
        (
            f"{average_rating:.2f} / 5"
            if average_rating is not None
            else "Unavailable"
        ),
    )

    period_days = kpis.get("period_days")

    col8.metric(
        "Analysis Period",
        (
            f"{period_days} days"
            if period_days is not None
            else "Unavailable"
        ),
    )

    st.subheader("Detected Problems")

    if not problems:
        st.success(
            "No problems were detected using the current diagnostic rules."
        )

    else:
        for problem in problems:
            severity = problem.get("severity", "medium").lower()
            title = problem.get("title", "Detected problem")
            problem_message = problem.get("message", "")
            evidence = problem.get("evidence", {})

            if severity == "high":
                st.error(f"High Priority — {title}")

            elif severity == "medium":
                st.warning(f"Medium Priority — {title}")

            else:
                st.info(f"Low Priority — {title}")

            st.write(problem_message)

            with st.expander("View supporting evidence"):
                for key, value in evidence.items():
                    label = key.replace("_", " ").title()

                    if (
                        "rate" in key
                        and isinstance(value, (int, float))
                    ):
                        st.write(f"**{label}:** {value:.1%}")

                    elif isinstance(value, float):
                        st.write(f"**{label}:** {value:.2f}")

                    else:
                        st.write(f"**{label}:** {value}")

    st.subheader("Recommended Actions")

    if not recommendations:
        st.info(
            "No recommendations were generated because no current "
            "diagnostic rule was triggered."
        )

    else:
        for recommendation in recommendations:
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

            st.markdown(f"### {title}")
            st.write(f"**Priority:** {priority.title()}")
            st.write(f"**Expected impact:** {expected_impact}")

            actions = recommendation.get("actions", [])

            if actions:
                st.write("**Actions:**")

                for action in actions:
                    st.markdown(f"- {action}")

            metric_to_monitor = recommendation.get(
                "metric_to_monitor"
            )

            if metric_to_monitor:
                metric_label = metric_to_monitor.replace(
                    "_",
                    " ",
                ).title()

                st.caption(
                    f"Metric to monitor: {metric_label}"
                )

            st.divider()

    with st.expander("View normalised report data"):
        st.dataframe(
            data,
            width="stretch",
        )


def display_toters_results(
    restaurant: str,
    data,
) -> None:
    """
    Display the consolidated Toters order-level dataset.
    """
    total_orders = len(data)

    gross_revenue = data["gross_revenue"].sum()
    net_revenue = data["net_order_revenue"].sum()
    total_platform_cost = data["total_platform_cost"].sum()
    total_marketing_cost = data["total_marketing_cost"].sum()

    average_order_value = (
        gross_revenue / total_orders
        if total_orders > 0
        else 0
    )

    platform_cost_rate = (
        total_platform_cost / gross_revenue
        if gross_revenue > 0
        else 0
    )

    marketing_cost_rate = (
        total_marketing_cost / gross_revenue
        if gross_revenue > 0
        else 0
    )

    st.success(
        f"Welcome {restaurant}! "
        "KitchenIQ has consolidated your Toters invoice report "
        "into one row per restaurant order."
    )

    st.caption(
        f"Toters report · "
        f"{total_orders:,} consolidated orders · "
        f"{data.shape[1]} analytical columns"
    )

    st.subheader("Toters Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Orders",
        f"{total_orders:,}",
    )

    col2.metric(
        "Gross Revenue",
        f"{gross_revenue:,.0f} LBP",
    )

    col3.metric(
        "Net Order Revenue",
        f"{net_revenue:,.0f} LBP",
    )

    col4.metric(
        "Total Platform Cost",
        f"{total_platform_cost:,.0f} LBP",
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Average Order Value",
        f"{average_order_value:,.0f} LBP",
    )

    col6.metric(
        "Platform Cost Rate",
        f"{platform_cost_rate:.1%}",
    )

    col7.metric(
        "Marketing Cost",
        f"{total_marketing_cost:,.0f} LBP",
    )

    col8.metric(
        "Marketing Cost Rate",
        f"{marketing_cost_rate:.1%}",
    )

    st.subheader("Toters Processing Status")

    st.success(
        "The Toters invoice ledger has been validated and successfully "
        "converted into a consolidated order-level dataset."
    )

    st.info(
        "The next development step is to connect these Toters KPIs "
        "to dedicated diagnostic rules and recommendations."
    )

    st.subheader("Consolidated Toters Orders")

    st.dataframe(
        data,
        width="stretch",
        hide_index=True,
    )


if st.button("Analyse Restaurant"):
    valid, message = validate_restaurant_name(
        restaurant_name
    )

    if not valid:
        st.error(message)

    elif uploaded_file is None:
        st.error("Please upload a restaurant report.")

    else:
        try:
            raw_data = load_file(uploaded_file)

        except Exception as error:
            st.error(
                f"KitchenIQ could not read this file: {error}"
            )
            st.stop()

        if raw_data is None:
            st.error("KitchenIQ could not read this file.")
            st.stop()

        # ---------------------------------------------------------
        # UBER EATS
        # ---------------------------------------------------------
        if platform == "Uber Eats":
            try:
                data = map_uber_eats(raw_data)

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
                st.error(column_message)
                st.stop()

            try:
                analysis = analyse_delivery_platform(data)

            except Exception as error:
                st.error(
                    "KitchenIQ could not analyse this Uber Eats "
                    f"report: {error}"
                )
                st.stop()

            display_uber_analysis(
                restaurant=restaurant_name,
                platform_name=platform,
                data=data,
                analysis=analysis,
            )

        # ---------------------------------------------------------
        # TOTERS
        # ---------------------------------------------------------
        elif platform == "Toters":
            # Validate the raw Toters export before transforming it.
            valid_columns, column_message = (
                validate_required_columns(
                    raw_data,
                    TOTERS_REQUIRED_COLUMNS,
                )
            )

            if not valid_columns:
                st.error(column_message)
                st.stop()

            try:
                data = map_toters(raw_data)

            except ValueError as error:
                st.error(str(error))
                st.stop()

            except Exception as error:
                st.error(
                    "KitchenIQ could not map this Toters "
                    f"report: {error}"
                )
                st.stop()

            display_toters_results(
                restaurant=restaurant_name,
                data=data,
            )

        # ---------------------------------------------------------
        # NOT YET SUPPORTED
        # ---------------------------------------------------------
        else:
            st.warning(
                f"{platform} is listed in KitchenIQ, "
                "but its connector has not been built yet."
            )

            st.info(
                "Please select Uber Eats or Toters "
                "for the current version."
            )