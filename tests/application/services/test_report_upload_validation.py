from __future__ import annotations

import pandas as pd

from application.services.report_upload_validation import (
    TOTERS_TEMPLATE_CSV,
    UploadKind,
    assess_toters_upload,
)


def test_accepts_real_toters_export_headers() -> None:
    dataframe = pd.DataFrame(
        columns=["ID", "Order Code", "Amount(LBP)", "Details", "Date", "Category"]
    )

    assessment = assess_toters_upload(dataframe, filename="activity.xlsx")

    assert assessment.kind is UploadKind.TOTERS_REPORT


def test_identifies_kitcheniq_dictionary_by_filename() -> None:
    dataframe = pd.DataFrame(columns=["A", "B", "C"])

    assessment = assess_toters_upload(
        dataframe,
        filename="KitchenIQ Functionality Dictionary.xlsx",
    )

    assert assessment.kind is UploadKind.KITCHENIQ_SPECIFICATION
    assert "already built" in assessment.message


def test_identifies_specification_by_headers() -> None:
    dataframe = pd.DataFrame(
        columns=["Phase", "Element", "Definition", "Key Metric", "Data Needed"]
    )

    assessment = assess_toters_upload(dataframe, filename="workbook.xlsx")

    assert assessment.kind is UploadKind.KITCHENIQ_SPECIFICATION


def test_unknown_schema_gets_report_guidance() -> None:
    dataframe = pd.DataFrame(columns=["Product", "Quantity", "Sales"])

    assessment = assess_toters_upload(dataframe, filename="sales.xlsx")

    assert assessment.kind is UploadKind.UNSUPPORTED_REPORT
    assert "Activity or Invoice report" in assessment.message
    assert assessment.received_columns == ("Product", "Quantity", "Sales")


def test_download_template_contains_expected_source_headers() -> None:
    assert TOTERS_TEMPLATE_CSV == (
        "ID,Order Code,Amount(LBP),Details,Date,Category\n"
    )
