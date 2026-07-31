from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


# Canonical internal column names used everywhere downstream of the
# Toters connector (row_parser.py reads only these names).
CANONICAL_COLUMNS = [
    "transaction_id",
    "order_reference",
    "amount",
    "details",
    "transaction_date",
    "category",
]

REQUIRED_COLUMNS = set(CANONICAL_COLUMNS)

# Known Toters source aliases, keyed by a case/whitespace-normalized form
# of the raw header. Add new source labels here only, never outside the
# Toters connector.
_SOURCE_ALIASES: dict[str, str] = {
    "id": "transaction_id",
    "order code": "order_reference",
    "order_code": "order_reference",
    "amount(lbp)": "amount",
    "amount (lbp)": "amount",
    "amount": "amount",
    "details": "details",
    "date": "transaction_date",
    "transaction date": "transaction_date",
    "category": "category",
}


@dataclass(frozen=True)
class SchemaValidationResult:
    is_valid: bool
    missing_columns: list[str]
    extra_columns: list[str]


def _normalized_alias_key(column: object) -> str:
    """
    Fold a raw column name into the lookup key used by _SOURCE_ALIASES:
    trimmed, internal whitespace collapsed, case-insensitive.
    """

    text = " ".join(str(column).strip().split())

    return text.lower()


def normalize_column_names(
    columns: Iterable[object],
) -> list[str]:
    """
    Map raw Toters source column names to canonical internal names.

    Columns that do not match a known Toters alias are kept as their
    stripped original name so they are still reported as extra columns
    instead of silently replacing a required field.
    """

    normalized = []

    for column in columns:
        alias_key = _normalized_alias_key(column)
        normalized.append(
            _SOURCE_ALIASES.get(alias_key, str(column).strip())
        )

    return normalized


def validate_invoice_schema(
    dataframe: pd.DataFrame,
) -> SchemaValidationResult:
    """
    Validate that a Toters invoice report contains all canonical columns.

    Must be called after normalize_column_names() has already mapped
    source aliases into canonical internal names.

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
