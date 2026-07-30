def generate_toters_recommendations(
    problems: list[dict],
) -> list[dict]:
    """
    Generate structured recommendations from Toters problems.
    """

    recommendations = []

    for problem in problems:
        code = problem.get("code")

        if code in {
            "TOTERS_PLATFORM_COST_CRITICAL",
            "TOTERS_PLATFORM_COST_HIGH",
        }:
            recommendations.append(
                {
                    "code": "REDUCE_TOTAL_PLATFORM_COST",
                    "title": "Reduce Total Platform Cost",
                    "priority": "high",
                    "expected_impact": (
                        "Improve retained revenue by reducing avoidable "
                        "platform and campaign deductions."
                    ),
                    "actions": [
                        (
                            "Separate listing fees, marketing deductions "
                            "and VAT in a weekly profitability review."
                        ),
                        (
                            "Identify which deduction category contributes "
                            "most to total platform cost."
                        ),
                        (
                            "Suspend or revise campaigns that generate "
                            "insufficient net revenue."
                        ),
                        (
                            "Review Toters commercial terms and prepare "
                            "evidence for a fee renegotiation."
                        ),
                    ],
                    "metric_to_monitor": "platform_cost_rate",
                }
            )

        elif code in {
            "TOTERS_MARKETING_DEPENDENCY_CRITICAL",
            "TOTERS_MARKETING_DEPENDENCY_HIGH",
        }:
            recommendations.append(
                {
                    "code": "REDUCE_MARKETING_DEPENDENCY",
                    "title": "Reduce Marketing Dependency",
                    "priority": "high",
                    "expected_impact": (
                        "Lower promotional deductions while preserving "
                        "the most profitable order volume."
                    ),
                    "actions": [
                        (
                            "Analyse Marketing Immediate Discount and "
                            "Marketing Item Fixed Price separately."
                        ),
                        (
                            "Measure net order revenue for promoted versus "
                            "non-promoted orders."
                        ),
                        (
                            "Pause the lowest-retention campaign and compare "
                            "order volume before and after the change."
                        ),
                        (
                            "Replace broad discounts with targeted offers "
                            "on selected products or order thresholds."
                        ),
                    ],
                    "metric_to_monitor": "marketing_cost_rate",
                }
            )

        elif code in {
            "TOTERS_LOW_RETAINED_REVENUE_CRITICAL",
            "TOTERS_LOW_RETAINED_REVENUE",
        }:
            recommendations.append(
                {
                    "code": "IMPROVE_RETAINED_REVENUE",
                    "title": "Improve Retained Revenue",
                    "priority": "high",
                    "expected_impact": (
                        "Increase the revenue remaining after platform "
                        "fees, marketing costs and VAT."
                    ),
                    "actions": [
                        (
                            "Set a minimum retained-revenue target for "
                            "every Toters order."
                        ),
                        (
                            "Identify orders with the lowest net order "
                            "revenue percentage."
                        ),
                        (
                            "Review menu pricing for products frequently "
                            "sold under promotional deductions."
                        ),
                        (
                            "Test minimum basket thresholds or bundles "
                            "that increase net revenue per order."
                        ),
                    ],
                    "metric_to_monitor": "retained_revenue_rate",
                }
            )

        elif code in {
            "TOTERS_PROMOTION_COVERAGE_CRITICAL",
            "TOTERS_PROMOTION_COVERAGE_HIGH",
        }:
            recommendations.append(
                {
                    "code": "REDUCE_PROMOTED_ORDER_SHARE",
                    "title": "Reduce the Share of Promoted Orders",
                    "priority": "medium",
                    "expected_impact": (
                        "Decrease dependence on paid incentives and improve "
                        "organic order profitability."
                    ),
                    "actions": [
                        (
                            "Calculate the margin difference between "
                            "promoted and non-promoted orders."
                        ),
                        (
                            "Limit campaigns to low-demand periods rather "
                            "than applying them broadly."
                        ),
                        (
                            "Exclude high-demand products from automatic "
                            "discount campaigns."
                        ),
                        (
                            "Track whether organic orders recover after "
                            "reducing promotion coverage."
                        ),
                    ],
                    "metric_to_monitor": "marketing_order_share",
                }
            )

        elif code in {
            "TOTERS_LISTING_FEE_CRITICAL",
            "TOTERS_LISTING_FEE_HIGH",
        }:
            recommendations.append(
                {
                    "code": "REVIEW_LISTING_FEE",
                    "title": "Review the Store Listing Fee",
                    "priority": "medium",
                    "expected_impact": (
                        "Reduce the fixed platform deduction applied to "
                        "gross order revenue."
                    ),
                    "actions": [
                        (
                            "Confirm the contractual listing-fee percentage "
                            "against the actual rate calculated by KitchenIQ."
                        ),
                        (
                            "Document monthly order volume and gross revenue "
                            "to support a commercial renegotiation."
                        ),
                        (
                            "Request volume-based or performance-based "
                            "commercial terms from Toters."
                        ),
                        (
                            "Model the retained-revenue impact of a lower "
                            "listing-fee rate."
                        ),
                    ],
                    "metric_to_monitor": "listing_fee_rate",
                }
            )

    # Prevent duplicate recommendations when related rules trigger.
    unique_recommendations = {}

    for recommendation in recommendations:
        unique_recommendations[
            recommendation["code"]
        ] = recommendation

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    result = list(
        unique_recommendations.values()
    )

    result.sort(
        key=lambda recommendation: priority_order.get(
            recommendation.get("priority", "low"),
            3,
        )
    )

    return result