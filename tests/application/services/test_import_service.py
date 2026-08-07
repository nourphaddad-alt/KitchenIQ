from __future__ import annotations

import pandas as pd
import pytest

from application.dto.analysis_result import AnalysisResult
from application.services.import_service import ImportService
from connectors.base.import_result import ImportOutcome
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
            "Order Code": "order-1001",
            "Transaction Date": "2026-03-01 12:30:00",
            "Category": "Store Listing Fee",
            "Details": "Listing fee",
            "Amount": "-15000",
        },
    ])


def _make_row(**overrides: object) -> dict[str, object]:
    row = {
        "ID": "activity-1",
        "Order Code": "order-1001",
        "Transaction Date": "2026-03-01 12:30:00",
        "Category": "Gross App Revenue",
        "Details": "Payment for order",
        "Amount": "150000",
    }
    row.update(overrides)
    return row


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
    assert result.outcome is ImportOutcome.SUCCESS
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
    assert result.metrics["total_orders"] == 1
    assert result.metrics["gross_revenue"] == 150000.0
    assert result.metrics["total_listing_fee"] == 15000.0


def test_import_service_raises_for_missing_required_columns() -> None:
    """RULE 2: blocking schema validation immediately fails the import."""
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

    with pytest.raises(ValueError, match="schema validation"):
        service.run_toters_import(
            dataframe=dataframe,
            restaurant_name="Saffron",
            platform="Toters",
        )


def test_import_service_failed_import_produces_no_analysis_result() -> None:
    """
    A failed import must never produce an AnalysisResult, which means it
    can never reach executive summary or KPI rendering downstream.
    """
    service = ImportService()
    dataframe = pd.DataFrame([_make_row()]).drop(columns=["Amount"])

    with pytest.raises(ValueError):
        service.run_toters_import(
            dataframe=dataframe,
            restaurant_name="Saffron",
            platform="Toters",
        )


def test_import_service_partial_success_when_some_rows_fail() -> None:
    """RULE 1/PARTIAL_SUCCESS: valid rows are kept when some rows error."""
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(
            ID="activity-2",
            Category="Not A Real Category",
            **{"Order Code": "order-1002"},
        ),
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.outcome is ImportOutcome.PARTIAL_SUCCESS
    assert len(result.records) == 1
    assert result.metrics["total_orders"] == 1
    assert any(
        issue.code == "UNKNOWN_CATEGORY"
        for issue in result.import_result.issues
    )


def test_import_service_raises_when_zero_financial_events_created() -> None:
    """RULE 3: rows received but zero FinancialEvents must fail loudly."""
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(Category="Not A Real Category"),
        _make_row(
            ID="activity-2",
            Category="Also Not Real",
            **{"Order Code": "order-1002"},
        ),
    ])

    with pytest.raises(ValueError, match="0 could be converted"):
        service.run_toters_import(
            dataframe=dataframe,
            restaurant_name="Saffron",
            platform="Toters",
        )


def test_import_service_invalid_amount_becomes_validation_issue() -> None:
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(
            ID="activity-2",
            Amount="not-a-number",
            **{"Order Code": "order-1002"},
        ),
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.outcome is ImportOutcome.PARTIAL_SUCCESS
    assert len(result.records) == 1
    assert any(
        issue.code == "ROW_PARSE_ERROR"
        for issue in result.import_result.issues
    )


def test_import_service_invalid_date_becomes_validation_issue() -> None:
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(
            ID="activity-2",
            **{
                "Order Code": "order-1002",
                "Transaction Date": "not-a-date",
            },
        ),
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.outcome is ImportOutcome.PARTIAL_SUCCESS
    assert len(result.records) == 1
    assert any(
        issue.code == "ROW_PARSE_ERROR"
        for issue in result.import_result.issues
    )


def test_import_service_multiple_events_per_order_consolidate_into_one_order() -> None:
    """RULE 5: multiple events for one order_reference produce one order."""
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(
            ID="activity-2",
            Category="Store Listing Fee",
            Amount="-15000",
        ),
        _make_row(
            ID="activity-3",
            Category="Value Added Tax",
            Amount="-5000",
        ),
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.metrics["total_orders"] == 1
    assert result.metrics["gross_revenue"] == 150000.0
    assert result.metrics["total_listing_fee"] == 15000.0
    assert result.metrics["total_vat"] == 5000.0
    assert result.metrics["total_platform_cost"] == 20000.0
    assert result.metrics["net_order_revenue"] == 130000.0


def test_import_service_settlement_event_does_not_increase_order_count() -> None:
    """RULE 5: settlement events must never increase order count."""
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(
            ID="activity-2",
            Category="Balance Settlement",
            Amount="130000",
            **{"Order Code": None},
        ),
    ])

    result = service.run_toters_import(
        dataframe=dataframe,
        restaurant_name="Saffron",
        platform="Toters",
    )

    assert result.metrics["total_orders"] == 1
    assert result.metrics["gross_revenue"] == 150000.0


def test_import_service_raises_when_only_settlement_events_exist() -> None:
    """Rows are received and parsed, but no order can be consolidated."""
    service = ImportService()
    dataframe = pd.DataFrame([
        _make_row(
            Category="Balance Settlement",
            Amount="130000",
            **{"Order Code": None},
        ),
    ])

    with pytest.raises(ValueError, match="none could be consolidated"):
        service.run_toters_import(
            dataframe=dataframe,
            restaurant_name="Saffron",
            platform="Toters",
        )


def test_import_service_does_not_import_streamlit() -> None:
    import application.services.import_service as module

    assert "streamlit" not in module.__dict__
