from __future__ import annotations

import pytest

from application.registry.metric_registry import load_metric_registry
from application.registry.operating_system import (
    ImplementationStatus,
    PRODUCT_MODULES,
    get_product_module,
    implementation_status,
    mapped_metric_ids,
    metrics_for_module,
)


def test_every_excel_metric_is_mapped_exactly_once() -> None:
    registered_ids = {
        metric.metric_id
        for metric in load_metric_registry()
    }
    mapped_ids = mapped_metric_ids()

    assert len(mapped_ids) == 33
    assert len(mapped_ids) == len(set(mapped_ids))
    assert set(mapped_ids) == registered_ids


def test_product_modules_have_expected_metric_counts() -> None:
    expected_counts = {
        "concept": 2,
        "operations": 6,
        "profit": 6,
        "menu_iq": 5,
        "promotions": 11,
        "marketing": 3,
    }

    assert {
        product_module.key: len(metrics_for_module(product_module.key))
        for product_module in PRODUCT_MODULES
    } == expected_counts


def test_current_implementation_status_is_not_overstated() -> None:
    assert (
        implementation_status("p1_c_1_platform_fees")
        is ImplementationStatus.LIVE
    )
    assert (
        implementation_status("p2_a_2_promotion_economics")
        is ImplementationStatus.PARTIAL
    )
    assert (
        implementation_status("p1_c_2_cogs_packaging_cost")
        is ImplementationStatus.SPECIFICATION_READY
    )


def test_unknown_module_is_rejected() -> None:
    with pytest.raises(KeyError, match="Unknown KitchenIQ product module"):
        get_product_module("not-a-module")
