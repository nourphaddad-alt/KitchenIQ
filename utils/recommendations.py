def generate_recommendations(problems):
    recommendations = []

    for problem in problems:
        code = problem.get("code")

        if code == "high_commission_rate":
            recommendations.append(
                {
                    "code": "reduce_platform_commission",
                    "title": "Reduce platform commission impact",
                    "priority": "high",
                    "expected_impact": (
                        "Improve net margin and reduce dependence "
                        "on platform-funded sales."
                    ),
                    "actions": [
                        "Review whether delivery menu prices fully absorb commission.",
                        "Remove or reprice low-margin items.",
                        "Measure the profitability of active promotions.",
                        "Increase direct-order conversion through packaging inserts.",
                    ],
                    "metric_to_monitor": "commission_rate",
                }
            )

        elif code == "low_average_order_value":
            recommendations.append(
                {
                    "code": "increase_average_order_value",
                    "title": "Increase average order value",
                    "priority": "medium",
                    "expected_impact": (
                        "Improve contribution margin per order and absorb "
                        "fixed platform costs more effectively."
                    ),
                    "actions": [
                        "Create profitable meal bundles.",
                        "Add high-margin sides, drinks and desserts.",
                        "Set free-delivery or promotion thresholds above the current basket.",
                        "Improve add-on placement in the delivery menu.",
                    ],
                    "metric_to_monitor": "average_order_value",
                }
            )

        elif code == "low_customer_rating":
            recommendations.append(
                {
                    "code": "improve_customer_rating",
                    "title": "Improve customer rating",
                    "priority": "high",
                    "expected_impact": (
                        "Protect platform visibility, conversion "
                        "and repeat-order performance."
                    ),
                    "actions": [
                        "Review recent negative feedback by recurring issue.",
                        "Audit packaging quality and food temperature.",
                        "Check preparation-time consistency during peak hours.",
                        "Temporarily remove items generating repeated complaints.",
                    ],
                    "metric_to_monitor": "average_customer_rating",
                }
            )

    return recommendations