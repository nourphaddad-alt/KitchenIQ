import pandas as pd

from utils.financial import commission_on


_MARKETING_DETAIL_COLUMNS = [
    "marketing_discount",
    "marketing_fixed_price",
    "marketing_free_delivery",
    "marketing_punch_card",
    "marketing_highlight",
    "marketing_credit_note",
    "marketing_highlight_credit_note",
]


_DISCOUNT_PROMOTION_CHARGE_COLUMNS = [
    "marketing_discount",
    "marketing_fixed_price",
    "marketing_free_delivery",
    "marketing_punch_card",
]


def _empty_kpis() -> dict:
    """
    Return the complete zero-value Toters KPI contract.
    """
    return {
        "total_orders": 0,
        "gross_revenue": 0.0,
        "net_order_revenue": 0.0,
        "total_platform_cost": 0.0,
        "total_listing_fee": 0.0,
        "total_marketing_cost": 0.0,
        "total_vat": 0.0,
        "vat_on_listing_fees": 0.0,
        "vat_on_courier": 0.0,
        "vat_on_marketing_highlight": 0.0,
        "vat_on_marketing_credit_note": 0.0,
        "vat_on_marketing": 0.0,
        "total_courier_cost": 0.0,
        "average_order_value": 0.0,
        "average_net_order_value": 0.0,
        "platform_cost_rate": None,
        "listing_fee_rate": None,
        "marketing_cost_rate": None,
        "vat_rate": None,
        "retained_revenue_rate": None,
        "orders_with_marketing": 0,
        "marketing_order_share": None,
        "minimum_order_value": 0.0,
        "maximum_order_value": 0.0,
        "period_days": None,
        "total_marketing_discount": 0.0,
        "total_marketing_fixed_price": 0.0,
        "total_marketing_free_delivery": 0.0,
        "total_marketing_punch_card": 0.0,
        "total_marketing_highlight": 0.0,
        "total_marketing_credit_note": 0.0,
        "total_marketing_highlight_credit_note": 0.0,
        "net_marketing_highlight": 0.0,
        "discount_promotion_spend": 0.0,
        "commission_on_marketing_discount": 0.0,
        "commission_on_marketing_fixed_price": 0.0,
        "total_commission_on_promotions": 0.0,
        "fully_loaded_promotion_cost": 0.0,
    }


def _ensure_optional_marketing_columns(
    working: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add missing detailed marketing columns as zeros.

    This keeps the KPI engine compatible with older consolidated
    datasets that only contain total_marketing_cost.
    """
    for column in _MARKETING_DETAIL_COLUMNS:
        if column not in working.columns:
            working[column] = 0.0

    return working


def calculate_toters_kpis(
    data: pd.DataFrame,
    account_level_costs: dict[str, float] | None = None,
) -> dict:
    """
    Calculate order-level KPIs from a consolidated Toters dataset.

    Required legacy columns:
    - order_id
    - order_date
    - gross_revenue
    - store_listing_fee
    - total_marketing_cost
    - vat
    - total_platform_cost
    - net_order_revenue

    Detailed marketing columns are optional and default to zero when
    importing an older consolidated dataset.
    """
    account_level_costs = account_level_costs or {}

    required_columns = [
        "order_id",
        "order_date",
        "gross_revenue",
        "store_listing_fee",
        "total_marketing_cost",
        "vat",
        "courier_cost",
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
        return _empty_kpis()

    working = _ensure_optional_marketing_columns(
        data.copy()
    )

    numeric_columns = [
        "gross_revenue",
        "store_listing_fee",
        "total_marketing_cost",
        "vat",
        "courier_cost",
        "total_platform_cost",
        "net_order_revenue",
        *_MARKETING_DETAIL_COLUMNS,
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

    # Only rows with positive gross revenue are genuine customer orders.
    # Cost-only references, including standalone Courier On Demand events,
    # remain in financial totals but do not increase the order count.
    revenue_orders = working.loc[
        working["gross_revenue"] > 0
    ].copy()

    total_orders = revenue_orders["order_id"].nunique()

    gross_revenue = working["gross_revenue"].sum()
    total_listing_fee = working["store_listing_fee"].sum()

    order_marketing_cost = working[
        "total_marketing_cost"
    ].sum()

    account_marketing_highlight = float(
        account_level_costs.get(
            "marketing_highlight",
            0.0,
        )
    )

    account_marketing_credit = float(
        account_level_costs.get(
            "marketing_credit_note",
            0.0,
        )
    )

    account_highlight_credit = float(
        account_level_costs.get(
            "marketing_highlight_credit_note",
            0.0,
        )
    )

    total_marketing_cost = (
        order_marketing_cost
        + account_marketing_highlight
        - account_marketing_credit
        - account_highlight_credit
    )

    total_courier_cost = working[
        "courier_cost"
    ].sum()

    # Courier On Demand can appear as a cost-only ledger activity.
    # VAT attached to such a row belongs to the courier charge,
    # not to the restaurant's listing-fee VAT.
    courier_only_mask = (
        (working["gross_revenue"] <= 0)
        & (working["store_listing_fee"] == 0)
        & (working["total_marketing_cost"] == 0)
        & (working["courier_cost"] > 0)
    )

    vat_on_courier = working.loc[
        courier_only_mask,
        "vat",
    ].sum()

    referenced_vat = working["vat"].sum()

    vat_on_listing_fees = (
        referenced_vat
        - vat_on_courier
    )

    vat_on_marketing_highlight = float(
        account_level_costs.get(
            "vat_marketing_highlight",
            0.0,
        )
    )

    vat_on_marketing_credit_note = float(
        account_level_costs.get(
            "vat_marketing_credit_note",
            0.0,
        )
    )

    vat_on_marketing = (
        vat_on_marketing_highlight
        - vat_on_marketing_credit_note
    )

    total_vat = (
        vat_on_listing_fees
        + vat_on_courier
        + vat_on_marketing
    )

    total_platform_cost = (
        total_listing_fee
        + total_marketing_cost
        + total_vat
        + total_courier_cost
    )

    net_order_revenue = (
        gross_revenue
        - total_platform_cost
    )

    total_marketing_discount = working[
        "marketing_discount"
    ].sum()

    total_marketing_fixed_price = working[
        "marketing_fixed_price"
    ].sum()

    total_marketing_free_delivery = working[
        "marketing_free_delivery"
    ].sum()

    total_marketing_punch_card = working[
        "marketing_punch_card"
    ].sum()

    order_marketing_highlight = working[
        "marketing_highlight"
    ].sum()

    total_marketing_highlight = (
        order_marketing_highlight
        + account_marketing_highlight
    )

    order_marketing_credit_note = -working[
        "marketing_credit_note"
    ].sum()

    total_marketing_credit_note = (
        order_marketing_credit_note
        + account_marketing_credit
    )

    order_marketing_highlight_credit_note = -working[
        "marketing_highlight_credit_note"
    ].sum()

    total_marketing_highlight_credit_note = (
        order_marketing_highlight_credit_note
        + account_highlight_credit
    )

    net_marketing_highlight = (
        total_marketing_highlight
        - total_marketing_highlight_credit_note
    )

    discount_promotion_spend = sum(
        working[column].sum()
        for column in _DISCOUNT_PROMOTION_CHARGE_COLUMNS
    )

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

    commission_on_marketing_discount = commission_on(
        total_marketing_discount,
        listing_fee_rate,
    )

    commission_on_marketing_fixed_price = commission_on(
        total_marketing_fixed_price,
        listing_fee_rate,
    )

    # Commission attribution applies only to promotions that reduce
    # the commissionable order revenue: immediate discounts and
    # fixed-price promotions. Highlight, free delivery and punch-card
    # costs are excluded from this attribution.
    total_commission_on_promotions = (
        commission_on_marketing_discount
        + commission_on_marketing_fixed_price
    )

    fully_loaded_promotion_cost = (
        discount_promotion_spend
        + total_commission_on_promotions
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
        revenue_orders.loc[
            revenue_orders["total_marketing_cost"] > 0,
            "order_id",
        ].nunique()
    )

    marketing_order_share = (
        orders_with_marketing / total_orders
        if total_orders > 0
        else None
    )

    if revenue_orders.empty:
        minimum_order_value = 0.0
        maximum_order_value = 0.0
    else:
        gross_order_values = revenue_orders[
            "gross_revenue"
        ]

        minimum_order_value = (
            gross_order_values.min()
        )
        maximum_order_value = (
            gross_order_values.max()
        )

    valid_dates = revenue_orders["order_date"].dropna()

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
        "vat_on_listing_fees": float(vat_on_listing_fees),
        "vat_on_courier": float(vat_on_courier),
        "vat_on_marketing_highlight": float(
            vat_on_marketing_highlight
        ),
        "vat_on_marketing_credit_note": float(
            vat_on_marketing_credit_note
        ),
        "vat_on_marketing": float(vat_on_marketing),
        "total_courier_cost": float(total_courier_cost),
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
        "minimum_order_value": float(
            minimum_order_value
        ),
        "maximum_order_value": float(
            maximum_order_value
        ),
        "period_days": period_days,
        "total_marketing_discount": float(
            total_marketing_discount
        ),
        "total_marketing_fixed_price": float(
            total_marketing_fixed_price
        ),
        "total_marketing_free_delivery": float(
            total_marketing_free_delivery
        ),
        "total_marketing_punch_card": float(
            total_marketing_punch_card
        ),
        "total_marketing_highlight": float(
            total_marketing_highlight
        ),
        "total_marketing_credit_note": float(
            total_marketing_credit_note
        ),
        "total_marketing_highlight_credit_note": float(
            total_marketing_highlight_credit_note
        ),
        "net_marketing_highlight": float(
            net_marketing_highlight
        ),
        "discount_promotion_spend": float(
            discount_promotion_spend
        ),
        "commission_on_marketing_discount": float(
            commission_on_marketing_discount
        ),
        "commission_on_marketing_fixed_price": float(
            commission_on_marketing_fixed_price
        ),
        "total_commission_on_promotions": float(
            total_commission_on_promotions
        ),
        "fully_loaded_promotion_cost": float(
            fully_loaded_promotion_cost
        ),
    }
