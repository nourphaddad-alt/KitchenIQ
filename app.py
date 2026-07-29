import streamlit as st

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

st.title("🍽️ KitchenIQ")
st.subheader("AI Operational Intelligence for Restaurants")
st.divider()

restaurant_name = st.text_input("Restaurant Name")

platform = st.selectbox(
    "Delivery Platform",
    [
        "Uber Eats",
        "Deliveroo",
        "Just Eat",
    ],
)

uploaded_file = st.file_uploader(
    "Upload Restaurant Report",
    type=["csv", "xlsx"],
)

if st.button("Analyse Restaurant"):
    valid, message = validate_restaurant_name(restaurant_name)

    if not valid:
        st.error(message)

    elif uploaded_file is None:
        st.error("Please upload a restaurant report.")

    else:
        data = load_file(uploaded_file)

        if data is None:
            st.error("KitchenIQ could not read this file.")

        else:
            if platform == "Uber Eats":
                data = map_uber_eats(data)

                valid_columns, column_message = validate_required_columns(
                    data,
                    UBER_EATS_REQUIRED_COLUMNS,
                )

                if not valid_columns:
                    st.error(column_message)
                    st.stop()

            analysis = analyse_delivery_platform(data)

            kpis = analysis["kpis"]
            problems = analysis["problems"]
            recommendations = analysis["recommendations"]

            st.success(
                f"Welcome {restaurant_name}! "
                "KitchenIQ has analysed your restaurant report."
            )

            st.caption(
                f"{platform} report · "
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

            col8.metric(
                "Analysis Period",
                (
                    f"{kpis.get('period_days')} days"
                    if kpis.get("period_days") is not None
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
                    message = problem.get("message", "")
                    evidence = problem.get("evidence", {})

                    if severity == "high":
                        st.error(f"High Priority — {title}")
                    elif severity == "medium":
                        st.warning(f"Medium Priority — {title}")
                    else:
                        st.info(f"Low Priority — {title}")

                    st.write(message)

                    with st.expander("View supporting evidence"):
                        for key, value in evidence.items():
                            label = key.replace("_", " ").title()

                            if "rate" in key and isinstance(
                                value,
                                (int, float),
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
                    st.markdown(
                        f"### {recommendation.get('title', 'Recommendation')}"
                    )

                    st.write(
                        "**Priority:** "
                        f"{recommendation.get('priority', 'Not specified').title()}"
                    )

                    st.write(
                        "**Expected impact:** "
                        f"{recommendation.get('expected_impact', 'Not specified')}"
                    )

                    actions = recommendation.get("actions", [])

                    if actions:
                        st.write("**Actions:**")

                        for action in actions:
                            st.markdown(f"- {action}")

                    metric_to_monitor = recommendation.get(
                        "metric_to_monitor"
                    )

                    if metric_to_monitor:
                        st.caption(
                            "Metric to monitor: "
                            + metric_to_monitor.replace(
                                "_",
                                " ",
                            ).title()
                        )

                    st.divider()

            with st.expander("View normalised report data"):
                st.dataframe(
                    data,
                    use_container_width=True,
                )