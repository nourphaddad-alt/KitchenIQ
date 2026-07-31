from __future__ import annotations

import pandas as pd

from connectors.toters.invoice_schema import (
    CANONICAL_COLUMNS,
    normalize_column_names,
    validate_invoice_schema,
)


def test_normalize_column_names_accepts_real_toters_header() -> None:
    raw_columns = [
        "ID",
        "Order code",
        "Amount(LBP)",
        "Details",
        "Date",
        "Category",
    ]

    normalized = normalize_column_names(raw_columns)

    assert normalized == [
        "transaction_id",
        "order_reference",
        "amount",
        "details",
        "transaction_date",
        "category",
    ]
    assert set(normalized) == set(CANONICAL_COLUMNS)


def test_validate_invoice_schema_accepts_real_toters_header() -> None:
    dataframe = pd.DataFrame(
        columns=normalize_column_names(
            ["ID", "Order code", "Amount(LBP)", "Details", "Date", "Category"]
        )
    )

    result = validate_invoice_schema(dataframe)

    assert result.is_valid is True
    assert result.missing_columns == []


def test_normalize_column_names_accepts_capitalization_and_whitespace_variants() -> None:
    raw_columns = [
        "  id  ",
        "ORDER   CODE",
        "amount (lbp)",
        "  DETAILS",
        "date  ",
        "  category  ",
    ]

    normalized = normalize_column_names(raw_columns)

    assert normalized == [
        "transaction_id",
        "order_reference",
        "amount",
        "details",
        "transaction_date",
        "category",
    ]


def test_normalize_column_names_accepts_order_code_snake_case_alias() -> None:
    assert normalize_column_names(["order_code"]) == ["order_reference"]


def test_normalize_column_names_accepts_legacy_toters_header() -> None:
    """Older Toters exports use Order Code / Transaction Date / Amount."""
    raw_columns = [
        "ID",
        "Order Code",
        "Transaction Date",
        "Category",
        "Details",
        "Amount",
    ]

    normalized = normalize_column_names(raw_columns)

    assert normalized == [
        "transaction_id",
        "order_reference",
        "transaction_date",
        "category",
        "details",
        "amount",
    ]


def test_validate_invoice_schema_fails_when_semantic_field_missing() -> None:
    """Real header, but the amount column itself is absent."""
    dataframe = pd.DataFrame(
        columns=normalize_column_names(
            ["ID", "Order code", "Details", "Date", "Category"]
        )
    )

    result = validate_invoice_schema(dataframe)

    assert result.is_valid is False
    assert "amount" in result.missing_columns


def test_unsupported_columns_do_not_replace_required_fields() -> None:
    """An unrecognised column must never be coerced into a canonical name."""
    raw_columns = [
        "ID",
        "Order code",
        "Amount(LBP)",
        "Details",
        "Date",
        "Category",
        "Amount Paid To Courier",
    ]

    normalized = normalize_column_names(raw_columns)

    assert normalized.count("amount") == 1
    assert "Amount Paid To Courier" in normalized

    dataframe = pd.DataFrame(columns=normalized)
    result = validate_invoice_schema(dataframe)

    assert result.is_valid is True
    assert result.extra_columns == ["Amount Paid To Courier"]
