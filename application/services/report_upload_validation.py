from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from connectors.toters.invoice_schema import (
    normalize_column_names,
    validate_invoice_schema,
)


TOTERS_SOURCE_COLUMNS = (
    "ID",
    "Order Code",
    "Amount(LBP)",
    "Details",
    "Date",
    "Category",
)

TOTERS_TEMPLATE_CSV = ",".join(TOTERS_SOURCE_COLUMNS) + "\n"


class UploadKind(str, Enum):
    TOTERS_REPORT = "toters_report"
    KITCHENIQ_SPECIFICATION = "kitcheniq_specification"
    UNSUPPORTED_REPORT = "unsupported_report"


@dataclass(frozen=True, slots=True)
class UploadAssessment:
    kind: UploadKind
    message: str
    received_columns: tuple[str, ...]


def _header_key(value: object) -> str:
    text = str(value).strip().casefold()
    return " ".join(text.replace("_", " ").split())


def assess_toters_upload(
    dataframe: pd.DataFrame,
    *,
    filename: str = "",
) -> UploadAssessment:
    """Identify valid Toters exports and common wrong-workbook uploads."""
    received_columns = tuple(str(column).strip() for column in dataframe.columns)
    normalized = dataframe.copy()
    normalized.columns = normalize_column_names(normalized.columns)
    schema = validate_invoice_schema(normalized)
    if schema.is_valid:
        return UploadAssessment(
            kind=UploadKind.TOTERS_REPORT,
            message="Compatible Toters transaction report.",
            received_columns=received_columns,
        )

    header_keys = {_header_key(column) for column in dataframe.columns}
    specification_headers = {
        "phase",
        "section",
        "element",
        "definition",
        "benefit",
        "problem solved",
        "key metric",
        "healthy benchmark",
        "red flag",
        "recommended action",
        "data needed",
        "outcome delivered",
        "automation",
    }
    filename_key = _header_key(filename)
    filename_looks_like_specification = any(
        hint in filename_key
        for hint in (
            "dictionary",
            "functional specification",
            "feature catalogue",
            "feature catalog",
        )
    )
    headers_look_like_specification = (
        len(header_keys & specification_headers) >= 3
    )

    if filename_looks_like_specification or headers_look_like_specification:
        return UploadAssessment(
            kind=UploadKind.KITCHENIQ_SPECIFICATION,
            message=(
                "This is a KitchenIQ feature/specification workbook, not a "
                "Toters transaction report. Its Phase 1 and Phase 2 features "
                "are already built into the workspaces above."
            ),
            received_columns=received_columns,
        )

    return UploadAssessment(
        kind=UploadKind.UNSUPPORTED_REPORT,
        message=(
            "This file is not a compatible Toters transaction report. "
            "Export the Activity or Invoice report from Toters and upload "
            "the file without renaming or restructuring its columns."
        ),
        received_columns=received_columns,
    )
