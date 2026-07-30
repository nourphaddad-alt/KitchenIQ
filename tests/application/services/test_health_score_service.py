from __future__ import annotations

import pandas as pd

from application.dto.analysis_result import AnalysisResult
from application.dto.health_score import HealthScore
from application.services.health_score_service import HealthScoreService
from application.services.import_service import ImportService


def _make_analysis_result() -> AnalysisResult:
    service = ImportService()
    dataframe = pd.DataFrame([
        {
            "ID": "activity-1",
            "Order Code": "order-1001",
            "Transaction Date": "2026-03-01 12:30:00",
            "Category": "Gross App Revenue",
            "Details": "Payment for order",
            "Amount": "150000",
        },
        {
            "ID": "activity-2",
            "Order Code": "order-1002",
            "Transaction Date": "2026-03-02 12:30:00",
            "Category": "Store Listing Fee",
            "Details": "Listing fee",
            "Amount": "15000",
        },
    ])
    return service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Potlee",
        platform="Toters",
    )


def test_health_score_service_strong_metrics() -> None:
    analysis = AnalysisResult(
        restaurant_name="Test",
        platform="Toters",
        import_result=None,
        metrics={
            "platform_cost_rate": 0.20,
            "marketing_cost_rate": 0.05,
            "marketing_order_share": 0.20,
            "retained_revenue_rate": 0.80,
        },
        diagnostics=[],
        recommendations=[],
    )

    score = HealthScoreService().calculate(analysis)

    assert isinstance(score, HealthScore)
    assert score.score == 100
    assert score.label == "Strong"


def test_health_score_service_current_potlee_profile() -> None:
    analysis = AnalysisResult(
        restaurant_name="Potlee",
        platform="Toters",
        import_result=None,
        metrics={
            "platform_cost_rate": 0.486,
            "marketing_cost_rate": 0.209,
            "marketing_order_share": 0.828,
            "retained_revenue_rate": 0.514,
        },
        diagnostics=[],
        recommendations=[],
    )
    score = HealthScoreService().calculate(analysis)

    assert score.score == 39
    assert score.label == "Critical"


def test_health_score_service_extremely_poor_metrics() -> None:
    analysis = AnalysisResult(
        restaurant_name="Test",
        platform="Toters",
        import_result=None,
        metrics={
            "platform_cost_rate": 0.60,
            "marketing_cost_rate": 0.35,
            "marketing_order_share": 0.90,
            "retained_revenue_rate": 0.20,
        },
        diagnostics=[],
        recommendations=[],
    )

    score = HealthScoreService().calculate(analysis)

    assert score.score == 15
    assert score.label == "Critical"


def test_health_score_service_clamps_bounds() -> None:
    assert HealthScoreService()._clamp_score(-10) == 0
    assert HealthScoreService()._clamp_score(120) == 100


def test_health_score_service_label_boundaries() -> None:
    assert HealthScoreService()._label_for_score(80) == "Strong"
    assert HealthScoreService()._label_for_score(79) == "Stable"
    assert HealthScoreService()._label_for_score(65) == "Stable"
    assert HealthScoreService()._label_for_score(64) == "At Risk"
    assert HealthScoreService()._label_for_score(45) == "At Risk"
    assert HealthScoreService()._label_for_score(44) == "Critical"
    assert HealthScoreService()._label_for_score(0) == "Critical"
