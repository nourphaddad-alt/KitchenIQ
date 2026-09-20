from __future__ import annotations

from application.registry.metric_registry import load_metric_registry
from application.registry.phase_feature_coverage import PHASE_FEATURE_COVERAGE


def test_every_phase_one_and_two_requirement_has_a_functional_workflow() -> None:
    registered_ids = {metric.metric_id for metric in load_metric_registry()}

    assert len(PHASE_FEATURE_COVERAGE) == 33
    assert set(PHASE_FEATURE_COVERAGE) == registered_ids
    assert all(PHASE_FEATURE_COVERAGE.values())


def test_coverage_is_limited_to_phase_one_and_phase_two() -> None:
    assert all(metric_id.startswith(("p1_", "p2_")) for metric_id in PHASE_FEATURE_COVERAGE)
