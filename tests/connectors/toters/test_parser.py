from __future__ import annotations

from decimal import Decimal

import pandas as pd

from connectors.toters.parser import parse_invoice
from domain.financial_event import FinancialEvent


REQUIRED_COLUMNS = [
    "ID",
    "Order Code",
    "Transaction Date",
    "Category",
    "Details",
    "Amount",
]


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


def test_valid_row_produces_financial_event() -> None:
    dataframe = pd.DataFrame([_make_row()])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.rows_received == 1
    assert result.rows_parsed == 1
    assert len(result.records) == 1
    assert result.issues == []

    event = result.records[0]
    assert isinstance(event, FinancialEvent)
    assert event.event_type == "gross_revenue"
    assert event.signed_amount == Decimal("150000")
    assert event.order_reference == "order-1001"


def test_unknown_category_creates_error_and_continues() -> None:
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(Category="Unknown Category"),
    ])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.rows_received == 2
    assert result.rows_parsed == 1
    assert len(result.records) == 1
    assert len(result.issues) == 1

    issue = result.issues[0]
    assert issue.code == "UNKNOWN_CATEGORY"
    assert issue.severity == "error"
    assert issue.source_row_number == 3
    assert issue.source_field == "Category"
    assert issue.source_value == "Unknown Category"


def test_invalid_amount_creates_row_parse_error_and_continues() -> None:
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(Amount="not-a-number"),
    ])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.rows_received == 2
    assert result.rows_parsed == 1
    assert len(result.records) == 1

    issue = result.issues[0]
    assert issue.code == "ROW_PARSE_ERROR"
    assert issue.severity == "error"
    assert issue.source_row_number == 3


def test_invalid_date_creates_row_parse_error_and_continues() -> None:
    dataframe = pd.DataFrame([
        _make_row(),
        _make_row(**{"Transaction Date": "not-a-date"}),
    ])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.rows_received == 2
    assert result.rows_parsed == 1
    assert len(result.records) == 1

    issue = result.issues[0]
    assert issue.code == "ROW_PARSE_ERROR"
    assert issue.severity == "error"
    assert issue.source_row_number == 3


def test_missing_required_columns_creates_blocking_issue() -> None:
    dataframe = pd.DataFrame([_make_row()]).drop(columns=["Amount"])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.rows_received == 0
    assert result.rows_parsed == 0
    assert result.records == []
    assert len(result.issues) == 1

    issue = result.issues[0]
    assert issue.code == "MISSING_REQUIRED_COLUMNS"
    assert issue.severity == "blocking"
    assert result.has_blocking_issues is True
    assert result.is_successful is False


def test_extra_columns_create_warning_without_blocking() -> None:
    dataframe = pd.DataFrame([_make_row(Unexpected="extra")])

    result = parse_invoice(dataframe, currency="LBP")

    assert len(result.records) == 1
    assert any(
        issue.code == "EXTRA_COLUMNS" and issue.severity == "warning"
        for issue in result.issues
    )
    assert result.has_blocking_issues is False
    assert result.is_successful is True


def test_real_toters_header_format_is_accepted() -> None:
    """The real Toters export uses Order code / Amount(LBP) / Date."""
    dataframe = pd.DataFrame([
        {
            "ID": "activity-1",
            "Order code": "order-1001",
            "Amount(LBP)": "150000",
            "Details": "Payment for order",
            "Date": "2026-03-01 12:30:00",
            "Category": "Gross App Revenue",
        }
    ])

    result = parse_invoice(dataframe, currency="LBP")

    assert result.issues == []
    assert result.rows_parsed == 1
    assert len(result.records) == 1

    event = result.records[0]
    assert event.source_activity_id == "activity-1"
    assert event.order_reference == "order-1001"
    assert event.signed_amount == Decimal("150000")
    assert event.event_type == "gross_revenue"
