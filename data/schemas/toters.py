# Raw columns expected in the Toters invoice report
TOTERS_REQUIRED_COLUMNS = [
    "ID",
    "Order code",
    "Amount(LBP)",
    "Details",
    "Date",
    "Category",
]


# Canonical KitchenIQ columns produced after Toters transformation
TOTERS_CANONICAL_COLUMNS = [
    "order_id",
    "order_date",
    "gross_revenue",
    "store_listing_fee",
    "marketing_fixed_price",
    "marketing_immediate_discount",
    "vat",
    "total_marketing_cost",
    "total_platform_cost",
    "net_order_revenue",
]


# Mapping between Toters transaction categories
# and KitchenIQ canonical financial fields
TOTERS_CATEGORY_MAPPING = {
    "Gross App Revenue": "gross_revenue",
    "Store Listing Fee": "store_listing_fee",
    "Marketing Item Fixed Price": "marketing_fixed_price",
    "Marketing Immediate Discount": "marketing_immediate_discount",
    "Value Added Tax": "vat",
}