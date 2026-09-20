from __future__ import annotations

import pytest

from application.registry.metric_registry import (
    get_metric,
    list_metrics,
    load_metric_registry,
    load_programmes,
)
from domain.metric_definition import MetricDefinition


PHASE_1 = "Phase 1: MVP, auditing & consulting"
PHASE_2 = "Phase 2: Most Valuable Promotion"


def test_catalogue_contains_every_excel_metric() -> None:
    metrics = load_metric_registry()

    assert len(metrics) == 33
    assert len(list_metrics(phase=PHASE_1)) == 15
    assert len(list_metrics(phase=PHASE_2)) == 18


def test_metric_identifiers_are_unique() -> None:
    identifiers = [metric.metric_id for metric in load_metric_registry()]

    assert len(identifiers) == len(set(identifiers))


def test_phase_two_fill_down_keeps_section_context() -> None:
    promotion_parameters = list_metrics(
        phase=PHASE_2,
        section="C. Promotion Parameters",
    )

    assert [metric.element for metric in promotion_parameters] == [
        "C.1 Discount Depth",
        "C.2 Minimum Spend Threshold",
        "C.3 Timing",
        "C.4 Duration / Frequency",
    ]


def test_repricing_definition_preserves_excel_formula() -> None:
    repricing = get_metric("p1_c_3_repricing")

    assert repricing.key_metric == (
        "Price coverage ratio = Item price ÷ "
        "(COGS + platform fee + VAT)"
    )
    assert repricing.healthy_benchmark == "Ratio ≥ 1.4 (40%+ buffer over true cost)"
    assert repricing.red_flag == "Ratio < 1.15 (item barely covers cost after fees)"
    assert repricing.automation == (
        "Pricing formula built into KitchenIQ: price = "
        "(COGS + target margin) ÷ (1 − platform fee %)"
    )


def test_promotion_economics_preserves_profit_definition() -> None:
    promotion_economics = get_metric("p2_a_2_promotion_economics")

    assert promotion_economics.key_metric == "Incremental contribution margin"
    assert promotion_economics.data_needed == (
        "Price, COGS, commission, discount, ad spend"
    )
    assert promotion_economics.problem_solved == (
        "Revenue uplift can hide margin destruction"
    )


def test_profit_target_and_phase_three_objective_are_preserved() -> None:
    margin_gap = get_metric("p2_g_1_margin_gap")
    programmes = load_programmes()

    assert margin_gap.healthy_benchmark == "17% target"
    assert margin_gap.data_needed == "Full P&L + Kitchen IQ outputs"
    assert programmes[1]["phase"] == (
        "Phase 3: Kitchen optimization / new brand creation"
    )
    assert programmes[1]["target"] == "get to 30% profit margin"


def test_get_metric_rejects_unknown_identifier() -> None:
    with pytest.raises(KeyError, match="Unknown KitchenIQ metric"):
        get_metric("not-a-real-metric")


def test_metric_definition_rejects_missing_required_content() -> None:
    valid_values = {
        "metric_id": "example",
        "phase": PHASE_1,
        "section": "Example",
        "element": "A.1 Example",
        "definition": "Definition",
        "benefit": "Benefit",
        "problem_solved": "Problem",
        "key_metric": "Metric",
        "healthy_benchmark": "Benchmark",
        "red_flag": "Red flag",
        "recommended_action": "Action",
        "data_needed": "Data",
        "outcome_delivered": "Outcome",
        "automation": "Automation",
        "source_line": 1,
    }

    with pytest.raises(ValueError, match="healthy_benchmark"):
        MetricDefinition(**{**valid_values, "healthy_benchmark": ""})
