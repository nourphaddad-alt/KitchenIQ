import pandas as pd

from data.schemas.toters import (
    TOTERS_REQUIRED_COLUMNS,
    TOTERS_CATEGORY_MAPPING,
)


def _validate_toters_columns(df: pd.DataFrame) -> None:
    """
    Verify that the uploaded dataframe contains the required
    Toters invoice-report columns.
    """
    missing_columns = [
        column
        for column in TOTERS_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing Toters columns: "
            + ", ".join(missing_columns)
        )


def _clean_amounts(series: pd.Series) -> pd.Series:
    """
    Convert Toters LBP amounts into numeric values.

    Handles:
    - commas
    - spaces
    - empty values
    - values already stored as numbers
    """
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0.0)


def _clean_order_codes(series: pd.Series) -> pd.Series:
    """
    Clean order codes without converting them into numeric values.
    """
    return (
        series.astype("string")
        .str.strip()
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
            }
        )
    )


def map_toters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a raw Toters invoice report into one consolidated
    KitchenIQ row per restaurant order.

    Non-order financial movements such as settlements, opening
    balances, closing balances and general marketing top-ups are
    excluded from the order-level dataset.
    """
    _validate_toters_columns(df)

    working = df.copy()

    working["Amount(LBP)"] = _clean_amounts(
        working["Amount(LBP)"]
    )

    working["Order code"] = _clean_order_codes(
        working["Order code"]
    )

    working["Date"] = pd.to_datetime(
        working["Date"],
        format="%d-%m-%Y %H:%M",
        errors="coerce",
    )

    working["Category"] = (
        working["Category"]
        .astype("string")
        .str.strip()
    )

    # Keep only rows connected to an order code.
    order_transactions = working[
        working["Order code"].notna()
    ].copy()

    if order_transactions.empty:
        raise ValueError(
            "No Toters order transactions were found in this report."
        )

    # Keep restaurant orders only.
    # Courier On Demand is a separate service and must not be
    # counted as restaurant sales.
    valid_order_codes = order_transactions.loc[
        order_transactions["Category"] == "Gross App Revenue",
        "Order code",
    ].dropna().unique()

    order_transactions = order_transactions[
        order_transactions["Order code"].isin(
            valid_order_codes
        )
    ].copy()

    if order_transactions.empty:
        raise ValueError(
            "No Gross App Revenue orders were found in this report."
        )

    # Create one financial column per Toters category.
    category_table = order_transactions.pivot_table(
        index="Order code",
        columns="Category",
        values="Amount(LBP)",
        aggfunc="sum",
        fill_value=0.0,
    )

    # Ensure all expected categories exist, even when absent
    # from a particular report.
    for raw_category in TOTERS_CATEGORY_MAPPING:
        if raw_category not in category_table.columns:
            category_table[raw_category] = 0.0

    category_table = category_table.rename(
        columns=TOTERS_CATEGORY_MAPPING
    )

    category_table = category_table.reset_index()

    # Extract one representative date per order.
    order_dates = (
        order_transactions.groupby(
            "Order code",
            as_index=False,
        )["Date"]
        .min()
        .rename(
            columns={
                "Date": "order_date",
            }
        )
    )

    orders = category_table.merge(
        order_dates,
        on="Order code",
        how="left",
    )

    orders = orders.rename(
        columns={
            "Order code": "order_id",
        }
    )

    financial_columns = [
        "gross_revenue",
        "store_listing_fee",
        "marketing_fixed_price",
        "marketing_immediate_discount",
        "vat",
    ]

    for column in financial_columns:
        if column not in orders.columns:
            orders[column] = 0.0

        orders[column] = pd.to_numeric(
            orders[column],
            errors="coerce",
        ).fillna(0.0)

    # Toters records fees and marketing deductions as negative
    # accounting values. KitchenIQ stores costs as positive values.
    orders["store_listing_fee"] = (
        orders["store_listing_fee"].abs()
    )

    orders["marketing_fixed_price"] = (
        orders["marketing_fixed_price"].abs()
    )

    orders["marketing_immediate_discount"] = (
        orders["marketing_immediate_discount"].abs()
    )

    orders["vat"] = orders["vat"].abs()

    orders["total_marketing_cost"] = (
        orders["marketing_fixed_price"]
        + orders["marketing_immediate_discount"]
    )

    orders["total_platform_cost"] = (
        orders["store_listing_fee"]
        + orders["total_marketing_cost"]
        + orders["vat"]
    )

    orders["net_order_revenue"] = (
        orders["gross_revenue"]
        - orders["total_platform_cost"]
    )

    orders["listing_fee_rate"] = (
        orders["store_listing_fee"]
        / orders["gross_revenue"].replace(0, pd.NA)
    )

    orders["marketing_cost_rate"] = (
        orders["total_marketing_cost"]
        / orders["gross_revenue"].replace(0, pd.NA)
    )

    orders["platform_cost_rate"] = (
        orders["total_platform_cost"]
        / orders["gross_revenue"].replace(0, pd.NA)
    )

    output_columns = [
        "order_id",
        "order_date",
        "gross_revenue",
        "store_listing_fee",
        "marketing_fixed_price",
        "marketing_immediate_discount",
        "total_marketing_cost",
        "vat",
        "total_platform_cost",
        "net_order_revenue",
        "listing_fee_rate",
        "marketing_cost_rate",
        "platform_cost_rate",
    ]

    orders = orders[output_columns]

    orders = orders.sort_values(
        by=["order_date", "order_id"],
        ascending=True,
    ).reset_index(drop=True)

    return orders