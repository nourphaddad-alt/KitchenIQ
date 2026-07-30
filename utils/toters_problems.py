from typing import Any


# Provisional KitchenIQ thresholds.
# These are internal diagnostic settings, not external market benchmarks.
TOTERS_DIAGNOSTIC_THRESHOLDS = {
    "platform_cost_rate_warning": 0.35,
    "platform_cost_rate_critical": 0.45,
    "marketing_cost_rate_warning": 0.15,
    "marketing_cost_rate_critical": 0.20,
    "retained_revenue_rate_warning": 0.65,
    "retained_revenue_rate_critical": 0.55,
    "marketing_order_share_warning": 0.50,
    "marketing_order_share_critical": 0.75,
    "listing_fee_rate_warning": 0.20,
    "listing_fee_rate_critical": 0.25,
}


def _rate_available(value: Any) -> bool:
    """
    Return True when a KPI rate is available and numeric.
    """
    return isinstance(value, (int, float))


def detect_toters_problems(kpis: dict) -> list[dict]:
    """
    Detect financial and commercial problems from Toters KPIs.

    Returns structured problem objects containing:
    - code
    - title
    - severity
    - business_area
    - message
    - evidence
    """

    problems = []

    platform_cost_rate = kpis.get("platform_cost_rate")

    if _rate_available(platform_cost_rate):
        if (
            platform_cost_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "platform_cost_rate_critical"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_PLATFORM_COST_CRITICAL",
                    "title": "Extremely High Platform Cost",
                    "severity": "high",
                    "business_area": "profitability",
                    "message": (
                        "A very large share of gross revenue is being "
                        "absorbed by listing fees, marketing deductions "
                        "and VAT before the restaurant receives its "
                        "net order revenue."
                    ),
                    "evidence": {
                        "platform_cost_rate": platform_cost_rate,
                        "total_platform_cost": kpis.get(
                            "total_platform_cost",
                            0.0,
                        ),
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                        "retained_revenue_rate": kpis.get(
                            "retained_revenue_rate"
                        ),
                    },
                }
            )

        elif (
            platform_cost_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "platform_cost_rate_warning"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_PLATFORM_COST_HIGH",
                    "title": "High Platform Cost",
                    "severity": "medium",
                    "business_area": "profitability",
                    "message": (
                        "Platform-related deductions are consuming a "
                        "material share of gross order revenue."
                    ),
                    "evidence": {
                        "platform_cost_rate": platform_cost_rate,
                        "total_platform_cost": kpis.get(
                            "total_platform_cost",
                            0.0,
                        ),
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                    },
                }
            )

    marketing_cost_rate = kpis.get("marketing_cost_rate")

    if _rate_available(marketing_cost_rate):
        if (
            marketing_cost_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "marketing_cost_rate_critical"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_MARKETING_DEPENDENCY_CRITICAL",
                    "title": "Very High Marketing Dependency",
                    "severity": "high",
                    "business_area": "marketing",
                    "message": (
                        "Marketing deductions represent a substantial "
                        "share of gross revenue. This can weaken retained "
                        "revenue and make sales dependent on discounts."
                    ),
                    "evidence": {
                        "marketing_cost_rate": marketing_cost_rate,
                        "total_marketing_cost": kpis.get(
                            "total_marketing_cost",
                            0.0,
                        ),
                        "orders_with_marketing": kpis.get(
                            "orders_with_marketing",
                            0,
                        ),
                        "marketing_order_share": kpis.get(
                            "marketing_order_share"
                        ),
                    },
                }
            )

        elif (
            marketing_cost_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "marketing_cost_rate_warning"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_MARKETING_DEPENDENCY_HIGH",
                    "title": "High Marketing Dependency",
                    "severity": "medium",
                    "business_area": "marketing",
                    "message": (
                        "Marketing deductions are taking a significant "
                        "share of revenue and should be reviewed by "
                        "campaign type."
                    ),
                    "evidence": {
                        "marketing_cost_rate": marketing_cost_rate,
                        "total_marketing_cost": kpis.get(
                            "total_marketing_cost",
                            0.0,
                        ),
                        "marketing_order_share": kpis.get(
                            "marketing_order_share"
                        ),
                    },
                }
            )

    retained_revenue_rate = kpis.get("retained_revenue_rate")

    if _rate_available(retained_revenue_rate):
        if (
            retained_revenue_rate
            <= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "retained_revenue_rate_critical"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_LOW_RETAINED_REVENUE_CRITICAL",
                    "title": "Critically Low Retained Revenue",
                    "severity": "high",
                    "business_area": "profitability",
                    "message": (
                        "The restaurant retains only a limited share of "
                        "gross platform revenue after recorded Toters "
                        "deductions."
                    ),
                    "evidence": {
                        "retained_revenue_rate": retained_revenue_rate,
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                        "net_order_revenue": kpis.get(
                            "net_order_revenue",
                            0.0,
                        ),
                    },
                }
            )

        elif (
            retained_revenue_rate
            <= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "retained_revenue_rate_warning"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_LOW_RETAINED_REVENUE",
                    "title": "Low Retained Revenue",
                    "severity": "medium",
                    "business_area": "profitability",
                    "message": (
                        "The restaurant is retaining a relatively low "
                        "share of gross platform revenue after deductions."
                    ),
                    "evidence": {
                        "retained_revenue_rate": retained_revenue_rate,
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                        "net_order_revenue": kpis.get(
                            "net_order_revenue",
                            0.0,
                        ),
                    },
                }
            )

    marketing_order_share = kpis.get("marketing_order_share")

    if _rate_available(marketing_order_share):
        if (
            marketing_order_share
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "marketing_order_share_critical"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_PROMOTION_COVERAGE_CRITICAL",
                    "title": "Most Orders Depend on Marketing",
                    "severity": "high",
                    "business_area": "marketing",
                    "message": (
                        "A very large proportion of orders carries a "
                        "marketing cost, indicating broad promotional "
                        "dependency."
                    ),
                    "evidence": {
                        "marketing_order_share": marketing_order_share,
                        "orders_with_marketing": kpis.get(
                            "orders_with_marketing",
                            0,
                        ),
                        "total_orders": kpis.get(
                            "total_orders",
                            0,
                        ),
                    },
                }
            )

        elif (
            marketing_order_share
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "marketing_order_share_warning"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_PROMOTION_COVERAGE_HIGH",
                    "title": "High Share of Promoted Orders",
                    "severity": "medium",
                    "business_area": "marketing",
                    "message": (
                        "A large proportion of orders includes a "
                        "marketing deduction. Campaign profitability "
                        "should be assessed separately."
                    ),
                    "evidence": {
                        "marketing_order_share": marketing_order_share,
                        "orders_with_marketing": kpis.get(
                            "orders_with_marketing",
                            0,
                        ),
                        "total_orders": kpis.get(
                            "total_orders",
                            0,
                        ),
                    },
                }
            )

    listing_fee_rate = kpis.get("listing_fee_rate")

    if _rate_available(listing_fee_rate):
        if (
            listing_fee_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "listing_fee_rate_critical"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_LISTING_FEE_CRITICAL",
                    "title": "Very High Listing Fee Burden",
                    "severity": "high",
                    "business_area": "platform_cost",
                    "message": (
                        "The store listing fee represents a large share "
                        "of gross revenue before marketing and tax costs."
                    ),
                    "evidence": {
                        "listing_fee_rate": listing_fee_rate,
                        "total_listing_fee": kpis.get(
                            "total_listing_fee",
                            0.0,
                        ),
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                    },
                }
            )

        elif (
            listing_fee_rate
            >= TOTERS_DIAGNOSTIC_THRESHOLDS[
                "listing_fee_rate_warning"
            ]
        ):
            problems.append(
                {
                    "code": "TOTERS_LISTING_FEE_HIGH",
                    "title": "High Listing Fee Burden",
                    "severity": "medium",
                    "business_area": "platform_cost",
                    "message": (
                        "Store listing fees represent a meaningful "
                        "portion of gross revenue."
                    ),
                    "evidence": {
                        "listing_fee_rate": listing_fee_rate,
                        "total_listing_fee": kpis.get(
                            "total_listing_fee",
                            0.0,
                        ),
                        "gross_revenue": kpis.get(
                            "gross_revenue",
                            0.0,
                        ),
                    },
                }
            )

    severity_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    problems.sort(
        key=lambda problem: severity_order.get(
            problem.get("severity", "low"),
            3,
        )
    )

    return problems