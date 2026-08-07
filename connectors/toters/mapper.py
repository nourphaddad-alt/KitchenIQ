from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMapping:
    event_type: str
    mapping_status: str
    confidence: str


CATEGORY_MAP: dict[str, CategoryMapping] = {
    "Gross App Revenue": CategoryMapping(
        event_type="gross_revenue",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Store Listing Fee": CategoryMapping(
        event_type="platform_commission",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Value Added Tax": CategoryMapping(
        event_type="vat",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Immediate Discount": CategoryMapping(
        event_type="marketing_discount",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Item Fixed Price": CategoryMapping(
        event_type="marketing_fixed_price",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Free Delivery": CategoryMapping(
        event_type="marketing_free_delivery",
        mapping_status="supported_unobserved",
        confidence="provisional",
    ),
    "Marketing Punch Card": CategoryMapping(
        event_type="marketing_punch_card",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Highlight": CategoryMapping(
        event_type="marketing_highlight",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Credit Note": CategoryMapping(
        event_type="marketing_credit_note",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Marketing Highlights Credit Note": CategoryMapping(
        event_type="marketing_highlight_credit_note",
        mapping_status="supported_unobserved",
        confidence="provisional",
    ),
    "Courier On Demand": CategoryMapping(
        event_type="courier_cost",
        mapping_status="validated",
        confidence="confirmed",
    ),
    "Balance Settlement": CategoryMapping(
        event_type="settlement",
        mapping_status="validated",
        confidence="confirmed",
    ),
}


def map_category(category: object) -> CategoryMapping | None:
    """
    Map a Toters invoice category to a canonical KitchenIQ event type.

    Returns None when the category is not recognised.
    """

    normalized_category = str(category).strip()

    if not normalized_category:
        return None

    return CATEGORY_MAP.get(normalized_category)