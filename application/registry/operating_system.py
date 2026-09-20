from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.registry.metric_registry import load_metric_registry
from domain.metric_definition import MetricDefinition


class ImplementationStatus(str, Enum):
    LIVE = "Live"
    PARTIAL = "Partial"
    SPECIFICATION_READY = "Specification ready"


@dataclass(frozen=True, slots=True)
class ProductModule:
    key: str
    label: str
    description: str
    sections: tuple[tuple[str, str], ...]


PRODUCT_MODULES = (
    ProductModule(
        key="concept",
        label="Concept & Discovery",
        description=(
            "Improve how customers discover the brand and how listings "
            "convert views into orders."
        ),
        sections=(("Phase 1: MVP, auditing & consulting", "A. Concept & Discovery"),),
    ),
    ProductModule(
        key="operations",
        label="Operations",
        description=(
            "Protect revenue by controlling cancellations, timing, uptime, "
            "refunds and packing accuracy."
        ),
        sections=(("Phase 1: MVP, auditing & consulting", "B. Operations"),),
    ),
    ProductModule(
        key="profit",
        label="Profit",
        description=(
            "Calculate the complete cost base, price correctly and measure "
            "progress toward the 17% net-profit target."
        ),
        sections=(
            ("Phase 1: MVP, auditing & consulting", "C. Cost & Base Formula"),
            ("Phase 2: Most Valuable Promotion", "G. 17% Profit Target"),
        ),
    ),
    ProductModule(
        key="menu_iq",
        label="Menu IQ",
        description=(
            "Optimize item mix, bundles and product selection using margin, "
            "velocity and basket behavior."
        ),
        sections=(
            ("Phase 1: MVP, auditing & consulting", "D. Menu Matrix"),
            ("Phase 1: MVP, auditing & consulting", "E. Combos/Bundles"),
            ("Phase 2: Most Valuable Promotion", "B. Offer Architecture"),
        ),
    ),
    ProductModule(
        key="promotions",
        label="Promotions",
        description=(
            "Measure true incrementality, prevent cannibalization and rank "
            "offers by incremental contribution rather than headline sales."
        ),
        sections=(
            ("Phase 2: Most Valuable Promotion", "A. Promotion Baseline"),
            ("Phase 2: Most Valuable Promotion", "C. Promotion Parameters"),
            ("Phase 2: Most Valuable Promotion", "D. Incrementality"),
            (
                "Phase 2: Most Valuable Promotion",
                "F. Most Valuable Promotion Engine",
            ),
        ),
    ),
    ProductModule(
        key="marketing",
        label="Marketing",
        description=(
            "Connect discounts and paid visibility to contribution after "
            "platform fees, COGS and advertising spend."
        ),
        sections=(
            (
                "Phase 1: MVP, auditing & consulting",
                "F. Marketing Formula & Ads",
            ),
            ("Phase 2: Most Valuable Promotion", "E. Marketing Spend"),
        ),
    ),
)


LIVE_METRIC_IDS = {
    "p1_c_1_platform_fees",
}


PARTIAL_METRIC_IDS = {
    "p1_f_1_marketing_formula_ads",
    "p2_a_1_current_promotions",
    "p2_a_2_promotion_economics",
    "p2_e_1_paid_promotion_ads",
    "p2_e_2_promo_ads_combination",
}


def get_product_module(module_key: str) -> ProductModule:
    for product_module in PRODUCT_MODULES:
        if product_module.key == module_key:
            return product_module

    raise KeyError(f"Unknown KitchenIQ product module: {module_key}")


def metrics_for_module(module_key: str) -> tuple[MetricDefinition, ...]:
    product_module = get_product_module(module_key)
    section_order = {
        section: index
        for index, section in enumerate(product_module.sections)
    }
    metrics = [
        metric
        for metric in load_metric_registry()
        if (metric.phase, metric.section) in section_order
    ]

    return tuple(
        sorted(
            metrics,
            key=lambda metric: (
                section_order[(metric.phase, metric.section)],
                metric.source_line,
            ),
        )
    )


def implementation_status(metric_id: str) -> ImplementationStatus:
    if metric_id in LIVE_METRIC_IDS:
        return ImplementationStatus.LIVE

    if metric_id in PARTIAL_METRIC_IDS:
        return ImplementationStatus.PARTIAL

    return ImplementationStatus.SPECIFICATION_READY


def mapped_metric_ids() -> tuple[str, ...]:
    return tuple(
        metric.metric_id
        for product_module in PRODUCT_MODULES
        for metric in metrics_for_module(product_module.key)
    )
