def detect_problems(kpis):
    problems = []

    commission_rate = kpis.get("commission_rate")
    average_order_value = kpis.get("average_order_value")
    average_customer_rating = kpis.get("average_customer_rating")

    if commission_rate is not None and commission_rate > 0.30:
        problems.append(
            {
                "code": "high_commission_rate",
                "title": "High commission rate",
                "severity": "high",
                "evidence": {
                    "commission_rate": commission_rate,
                    "threshold": 0.30,
                },
                "message": (
                    "Platform commission represents more than 30% "
                    "of gross sales."
                ),
            }
        )

    if average_order_value is not None and average_order_value < 25:
        problems.append(
            {
                "code": "low_average_order_value",
                "title": "Low average order value",
                "severity": "medium",
                "evidence": {
                    "average_order_value": average_order_value,
                    "threshold": 25,
                },
                "message": (
                    "The average order value is below €25, which may "
                    "limit profitability after commission and delivery costs."
                ),
            }
        )

    if average_customer_rating is not None and average_customer_rating < 4.3:
        problems.append(
            {
                "code": "low_customer_rating",
                "title": "Low customer rating",
                "severity": "high",
                "evidence": {
                    "average_customer_rating": average_customer_rating,
                    "threshold": 4.3,
                },
                "message": (
                    "The average customer rating is below 4.3, which may "
                    "reduce conversion, ranking and repeat orders."
                ),
            }
        )

    return problems