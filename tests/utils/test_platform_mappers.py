from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.schemas.deliveroo import DELIVEROO_REQUIRED_COLUMNS
from data.schemas.uber_eats import UBER_EATS_REQUIRED_COLUMNS
from utils.mapper import map_deliveroo, map_uber_eats
from utils.analyser import analyse_delivery_platform
from utils.validation import validate_required_columns


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_uber_eats_mock_headers_map_to_required_schema() -> None:
    raw = pd.DataFrame(
        columns=[
            "Order ID",
            "Restaurant Name",
            "Date",
            "Net Sales",
            "Gross Sales",
            "Commission",
            "Delivery Fee",
            "Customer Rating",
        ]
    )

    mapped = map_uber_eats(raw)

    assert validate_required_columns(mapped, UBER_EATS_REQUIRED_COLUMNS)[0]


def test_deliveroo_mock_headers_map_to_required_schema() -> None:
    raw = pd.DataFrame(
        columns=[
            "Order number",
            "Restaurant name",
            "Order date",
            "Gross order value",
            "Net earnings",
            "Commission amount",
            "Delivery fee",
            "Customer rating",
        ]
    )

    mapped = map_deliveroo(raw)

    assert validate_required_columns(mapped, DELIVEROO_REQUIRED_COLUMNS)[0]


def test_downloadable_uber_eats_mock_runs_end_to_end() -> None:
    raw = pd.read_excel(
        REPOSITORY_ROOT / "examples" / "kitcheniq_mock_uber_eats_report.xlsx"
    )
    mapped = map_uber_eats(raw)

    assert validate_required_columns(mapped, UBER_EATS_REQUIRED_COLUMNS)[0]
    analysis = analyse_delivery_platform(mapped)
    assert analysis["kpis"]["total_orders"] == 28
    assert analysis["kpis"]["gross_sales"] > analysis["kpis"]["net_sales"]


def test_downloadable_deliveroo_mock_runs_end_to_end() -> None:
    raw = pd.read_excel(
        REPOSITORY_ROOT / "examples" / "kitcheniq_mock_deliveroo_report.xlsx"
    )
    mapped = map_deliveroo(raw)

    assert validate_required_columns(mapped, DELIVEROO_REQUIRED_COLUMNS)[0]
    analysis = analyse_delivery_platform(mapped)
    assert analysis["kpis"]["total_orders"] == 28
    assert analysis["kpis"]["gross_sales"] > analysis["kpis"]["net_sales"]
