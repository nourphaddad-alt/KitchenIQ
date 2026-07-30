from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "ID",
    "Order Code",
    "Transaction Date",
    "Category",
    "Details",
    "Amount",
}


@dataclass(frozen=True)
class SchemaValidationResult:
    is_valid: bool
    missing_columns: list[str]
    extra_columns: list[str]


def validate_invoice_schema(
    dataframe: pd.DataFrame,
) -> SchemaValidationResult:
    """
    Validate that a Toters invoice report contains all required columns.

    Extra columns are allowed because Toters may add fields in future exports.
    """

    actual_columns = {
        str(column).strip()
        for column in dataframe.columns
    }

    missing_columns = sorted(REQUIRED_COLUMNS - actual_columns)
    extra_columns = sorted(actual_columns - REQUIRED_COLUMNS)

    return SchemaValidationResult(
        is_valid=not missing_columns,
        missing_columns=missing_columns,
        extra_columns=extra_columns,
    )


def normalize_column_names(
    columns: Iterable[object],
) -> list[str]:
    """
    Return clean column names without modifying the source dataframe.
    """

    return [
        str(column).strip()
        for column in columns
    ]