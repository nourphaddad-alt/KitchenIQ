import pandas as pd


def calculate_toters_kpis(data: pd.DataFrame) -> dict:
    """
    Calculate order-level KPIs from a consolidated Toters dataset.

    Expected columns:
    - order_id
    - order_date
    - gross_revenue
    - store_listing_fee
    - total_marketing_cost
    - vat
    - total_platform_cost
    - net_order_revenue
    """

    required_columns = [
        "order_id",
        "order_date",
        "gross_revenue",
        "store_listing_fee",
        "total_marketing_cost",
        "vat",
        "total_platform_cost",
        "net_order_revenue",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Cannot calculate Toters KPIs. Missing columns: "
            + ", ".join(missing_columns)
        )

    if data.empty:
        return {
            "total_orders": 0,
            "gross_revenue": 0.0,
            "net_order_revenue": 0.0,
            "total_platform_cost": 0.0,
            "total_listing_fee": 0.0,
            "total_marketing_cost": 0.0,
            "total_vat": 0.0,
            "average_order_value": 0.0,
            "average_net_order_value": 0.0,
            "platform_cost_rate": None,
            "listing_fee_rate": None,
            "marketing_cost_rate": None,
            "vat_rate": None,
            "retained_revenue_rate": None,
            "orders_with_marketing": 0,
            "marketing_order_share": None,
            "median_order_value": 0.0,
            "minimum_order_value": 0.0,
            "maximum_order_value": 0.0,
            "period_days": None,
        }

    working = data.copy()

    numeric_columns = [
        "gross_revenue",
        "store_listing_fee",
        "total_marketing_cost",
        "vat",
        "total_platform_cost",
        "net_order_revenue",
    ]

    for column in numeric_columns:
        working[column] = pd.to_numeric(
            working[column],
            errors="coerce",
        ).fillna(0.0)

    working["order_date"] = pd.to_datetime(
        working["order_date"],
        errors="coerce",
    )

    # Every unique order ID remains part of the total order count.
    total_orders = working["order_id"].nunique()

    # Revenue-based order statistics exclude records with no gross revenue.
    revenue_orders = working.loc[
        working["gross_revenue"] > 0
    ].copy()

    gross_revenue = working["gross_revenue"].sum()
    net_order_revenue = working["net_order_revenue"].sum()
    total_platform_cost = working["total_platform_cost"].sum()
    total_listing_fee = working["store_listing_fee"].sum()
    total_marketing_cost = working["total_marketing_cost"].sum()
    total_vat = working["vat"].sum()

    average_order_value = (
        gross_revenue / total_orders
        if total_orders > 0
        else 0.0
    )

    average_net_order_value = (
        net_order_revenue / total_orders
        if total_orders > 0
        else 0.0
    )

    platform_cost_rate = (
        total_platform_cost / gross_revenue
        if gross_revenue > 0
        else None
    )

    listing_fee_rate = (
        total_listing_fee / gross_revenue
        if gross_revenue > 0
        else None
    )

    marketing_cost_rate = (
        total_marketing_cost / gross_revenue
        if gross_revenue > 0
        else None
    )

    vat_rate = (
        total_vat / gross_revenue
        if gross_revenue > 0
        else None
    )

    retained_revenue_rate = (
        net_order_revenue / gross_revenue
        if gross_revenue > 0
        else None
    )

    orders_with_marketing = int(
        working.loc[
            working["total_marketing_cost"] > 0,
            "order_id",
        ].nunique()
    )

    marketing_order_share = (
        orders_with_marketing / total_orders
        if total_orders > 0
        else None
    )

    if revenue_orders.empty:
        median_order_value = 0.0
        minimum_order_value = 0.0
        maximum_order_value = 0.0
    else:
        gross_order_values = revenue_orders["gross_revenue"]

        median_order_value = gross_order_values.median()
        minimum_order_value = gross_order_values.min()
        maximum_order_value = gross_order_values.max()

    valid_dates = working["order_date"].dropna()

    if valid_dates.empty:
        period_days = None
    else:
        period_days = (
            valid_dates.max().normalize()
            - valid_dates.min().normalize()
        ).days + 1

    return {
        "total_orders": int(total_orders),
        "gross_revenue": float(gross_revenue),
        "net_order_revenue": float(net_order_revenue),
        "total_platform_cost": float(total_platform_cost),
        "total_listing_fee": float(total_listing_fee),
        "total_marketing_cost": float(total_marketing_cost),
        "total_vat": float(total_vat),
        "average_order_value": float(average_order_value),
        "average_net_order_value": float(
            average_net_order_value
        ),
        "platform_cost_rate": platform_cost_rate,
        "listing_fee_rate": listing_fee_rate,
        "marketing_cost_rate": marketing_cost_rate,
        "vat_rate": vat_rate,
        "retained_revenue_rate": retained_revenue_rate,
        "orders_with_marketing": orders_with_marketing,
        "marketing_order_share": marketing_order_share,
        "median_order_value": float(median_order_value),
        "minimum_order_value": float(minimum_order_value),
        "maximum_order_value": float(maximum_order_value),
        "period_days": period_days,
    }