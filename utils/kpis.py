import pandas as pd


def calculate_basic_kpis(dataframe):
    kpis = {}

    # Total orders
    if "order_id" in dataframe.columns:
        kpis["total_orders"] = int(dataframe["order_id"].nunique())

    # Convert financial columns to numbers safely
    financial_columns = [
        "gross_sales",
        "net_sales",
        "commission",
        "delivery_fee",
    ]

    for column in financial_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            ).fillna(0)

    # Gross sales
    if "gross_sales" in dataframe.columns:
        gross_sales = float(dataframe["gross_sales"].sum())
        kpis["gross_sales"] = round(gross_sales, 2)

    # Net sales
    if "net_sales" in dataframe.columns:
        net_sales = float(dataframe["net_sales"].sum())
        kpis["net_sales"] = round(net_sales, 2)

    # Total commission
    if "commission" in dataframe.columns:
        total_commission = float(dataframe["commission"].sum())
        kpis["total_commission"] = round(total_commission, 2)

    # Total delivery fees
    if "delivery_fee" in dataframe.columns:
        total_delivery_fees = float(dataframe["delivery_fee"].sum())
        kpis["total_delivery_fees"] = round(total_delivery_fees, 2)

    # Average order value
    total_orders = kpis.get("total_orders", 0)
    gross_sales = kpis.get("gross_sales", 0)

    if total_orders > 0:
        kpis["average_order_value"] = round(
            gross_sales / total_orders,
            2,
        )

    # Commission rate
    total_commission = kpis.get("total_commission", 0)

    if gross_sales > 0:
        kpis["commission_rate"] = round(
            total_commission / gross_sales,
            4,
        )

    # Average customer rating
    if "customer_rating" in dataframe.columns:
        ratings = pd.to_numeric(
            dataframe["customer_rating"],
            errors="coerce",
        )

        if ratings.notna().any():
            kpis["average_customer_rating"] = round(
                float(ratings.mean()),
                2,
            )

    # Analysis period
    if "order_date" in dataframe.columns:
        dates = pd.to_datetime(
            dataframe["order_date"],
            errors="coerce",
        ).dropna()

        if not dates.empty:
            kpis["period_start"] = dates.min().strftime("%Y-%m-%d")
            kpis["period_end"] = dates.max().strftime("%Y-%m-%d")
            kpis["period_days"] = int(
                (dates.max() - dates.min()).days + 1
            )

    return kpis