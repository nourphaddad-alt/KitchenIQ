from __future__ import annotations

import pandas as pd

from application.dto.analysis_result import AnalysisResult
from connectors.base.import_result import ImportResult
from connectors.toters.parser import parse_invoice
from domain.financial_event import FinancialEvent
from utils.toters_kpis import calculate_toters_kpis
from utils.toters_problems import detect_toters_problems
from utils.toters_recommendations import generate_toters_recommendations


class ImportService:
    def run_toters_import(
        self,
        dataframe: pd.DataFrame,
        restaurant_name: str,
        platform: str = "Toters",
        currency: str = "LBP",
    ) -> AnalysisResult:
        import_result = parse_invoice(dataframe, currency=currency)

        records: list[FinancialEvent] = list(import_result.records)

        metrics: dict[str, object] = {}
        diagnostics: list[dict[str, object]] = []
        recommendations: list[dict[str, object]] = []

        if records:
            aggregated_rows: list[dict[str, object]] = []

            for record in records:
                row: dict[str, object] = {
                    "order_id": record.order_reference,
                    "order_date": record.occurred_at,
                    "gross_revenue": 0.0,
                    "store_listing_fee": 0.0,
                    "marketing_fixed_price": 0.0,
                    "marketing_immediate_discount": 0.0,
                    "vat": 0.0,
                }

                amount = float(abs(record.signed_amount))

                if record.event_type == "gross_revenue":
                    row["gross_revenue"] = amount
                elif record.event_type == "platform_commission":
                    row["store_listing_fee"] = amount
                elif record.event_type == "marketing_fixed_price":
                    row["marketing_fixed_price"] = amount
                elif record.event_type == "marketing_discount":
                    row["marketing_immediate_discount"] = amount
                elif record.event_type == "vat":
                    row["vat"] = amount

                row["total_marketing_cost"] = (
                    float(row["marketing_fixed_price"])
                    + float(row["marketing_immediate_discount"])
                )
                row["total_platform_cost"] = (
                    float(row["store_listing_fee"])
                    + float(row["total_marketing_cost"])
                    + float(row["vat"])
                )
                row["net_order_revenue"] = (
                    float(row["gross_revenue"])
                    - float(row["total_platform_cost"])
                )
                aggregated_rows.append(row)

            consolidated = pd.DataFrame(aggregated_rows)

            metrics = calculate_toters_kpis(consolidated)
            diagnostics = detect_toters_problems(metrics)
            recommendations = generate_toters_recommendations(diagnostics)

        return AnalysisResult(
            restaurant_name=restaurant_name,
            platform=platform,
            import_result=import_result,
            records=records,
            metrics=metrics,
            diagnostics=diagnostics,
            recommendations=recommendations,
        )
