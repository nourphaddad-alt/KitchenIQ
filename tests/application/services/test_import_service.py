from __future__ import annotations

import pandas as pd

from application.dto.analysis_result import AnalysisResult
from application.services.import_service import ImportService
from connectors.base.validation_issue import ValidationIssue
from domain.financial_event import FinancialEvent


def _make_dataframe() -> pd.DataFrame:
    return pd.DataFrame([
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


def test_import_service_returns_analysis_result() -> None:
    service = ImportService()

    result = service.run_toters_import(
        dataframe=_make_dataframe(),
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert isinstance(result, AnalysisResult)
    assert result.restaurant_name == "Saffron"
    assert result.platform == "Toters"
    assert isinstance(result.import_result, object)
    assert result.records
    assert result.metrics
    assert result.diagnostics is not None
    assert result.recommendations is not None
    assert isinstance(result.diagnostics, list)
    assert isinstance(result.recommendations, list)


def test_import_service_preserves_records_and_metrics() -> None:
    service = ImportService()

    result = service.run_toters_import(
        dataframe=_make_dataframe(),
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert all(isinstance(record, FinancialEvent) for record in result.records)
    assert result.metrics["total_orders"] == 2
    assert result.metrics["gross_revenue"] == 150000.0
    assert result.metrics["total_listing_fee"] == 15000.0


def test_import_service_preserves_blocking_validation_issues() -> None:
    service = ImportService()
    dataframe = pd.DataFrame([
        {
            "ID": "activity-1",
            "Order Code": "order-1001",
            "Transaction Date": "2026-03-01 12:30:00",
            "Category": "Gross App Revenue",
            "Details": "Payment for order",
        }
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.import_result.has_blocking_issues is True
    assert result.import_result.is_successful is False
    assert result.records == []
    assert any(issue.code == "MISSING_REQUIRED_COLUMNS" for issue in result.import_result.issues)
    assert all(isinstance(issue, ValidationIssue) for issue in result.import_result.issues)


def test_import_service_does_not_import_streamlit() -> None:
    import application.services.import_service as module

    assert "streamlit" not in module.__dict__
