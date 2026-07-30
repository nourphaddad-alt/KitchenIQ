from __future__ import annotations

import pandas as pd

from connectors.base.import_result import ImportResult
from connectors.base.validation_issue import ValidationIssue
from .invoice_schema import normalize_column_names, validate_invoice_schema
from .row_parser import parse_invoice_row


def parse_invoice(
    dataframe: pd.DataFrame,
    currency: str = "LBP",
) -> ImportResult:
    """
    Parse a Toters invoice dataframe into canonical financial events.

    Schema failures stop the import.
    Row-level failures are collected without stopping valid rows.
    """

    result = ImportResult(
        connector_code="toters_invoice",
        connector_version="1.0",
        mapping_version="toters_invoice_1.0",
    )

    working_dataframe = dataframe.copy()
    working_dataframe.columns = normalize_column_names(
        working_dataframe.columns
    )

    schema_result = validate_invoice_schema(working_dataframe)

    if not schema_result.is_valid:
        result.issues.append(
            ValidationIssue(
                code="MISSING_REQUIRED_COLUMNS",
                message="Missing required columns: "
                + ", ".join(schema_result.missing_columns),
                severity="blocking",
            )
        )
        return result

    if schema_result.extra_columns:
        result.issues.append(
            ValidationIssue(
                code="EXTRA_COLUMNS",
                message="Extra columns detected: "
                + ", ".join(schema_result.extra_columns),
                severity="warning",
            )
        )

    for dataframe_index, row in working_dataframe.iterrows():
        source_row_number = int(dataframe_index) + 2
        result.rows_received += 1

        try:
            record = parse_invoice_row(
                row=row,
                source_row_number=source_row_number,
                currency=currency,
            )
        except ValueError as exc:
            if "Unknown category:" in str(exc):
                result.issues.append(
                    ValidationIssue(
                        code="UNKNOWN_CATEGORY",
                        message=f"Row {source_row_number}: {exc}",
                        severity="error",
                        source_row_number=source_row_number,
                        source_field="Category",
                        source_value=str(exc).split("Unknown category:", maxsplit=1)[1].strip().strip("'\""),
                    )
                )
            else:
                result.issues.append(
                    ValidationIssue(
                        code="ROW_PARSE_ERROR",
                        message=f"Row {source_row_number}: {exc}",
                        severity="error",
                        source_row_number=source_row_number,
                    )
                )
            continue

        result.records.append(record)
        result.rows_parsed += 1

    return result