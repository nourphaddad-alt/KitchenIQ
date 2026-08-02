from __future__ import annotations

import pandas as pd

from application.dto.analysis_result import AnalysisResult
from application.services.account_level_costs import (
    aggregate_account_level_costs,
)
from application.services.order_consolidation import consolidate_orders
from connectors.base.import_result import ImportOutcome, ImportResult
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
        outcome = import_result.outcome

        if outcome is ImportOutcome.FAILED:
            raise ValueError(self._build_failure_message(import_result))

        records: list[FinancialEvent] = list(import_result.records)

        consolidated_orders = consolidate_orders(records)

        account_level_costs = aggregate_account_level_costs(
            records
        )

        if consolidated_orders.empty:
            raise ValueError(
                "Toters import failed: "
                f"{len(records)} financial event(s) were imported, but none "
                "could be consolidated into a valid order. Every event was "
                "either a settlement entry or missing an order reference."
            )

        metrics = calculate_toters_kpis(
            consolidated_orders,
            account_level_costs=account_level_costs,
        )
        diagnostics = detect_toters_problems(metrics)
        recommendations = generate_toters_recommendations(diagnostics)

        return AnalysisResult(
            restaurant_name=restaurant_name,
            platform=platform,
            import_result=import_result,
            outcome=outcome,
            records=records,
            metrics=metrics,
            diagnostics=diagnostics,
            recommendations=recommendations,
        )

    @staticmethod
    def _build_failure_message(import_result: ImportResult) -> str:
        if import_result.has_blocking_issues:
            details = "; ".join(
                issue.message
                for issue in import_result.issues
                if issue.severity == "blocking"
            )
            return f"Toters import failed schema validation: {details}"

        if import_result.rows_received == 0:
            return (
                "Toters import failed: the uploaded report contains no "
                "data rows to import."
            )

        details = "; ".join(
            issue.message
            for issue in import_result.issues
            if issue.severity == "error"
        )
        message = (
            "Toters import failed: "
            f"{import_result.rows_received} row(s) were received, but 0 "
            "could be converted into financial events."
        )

        if details:
            message += f" Reasons: {details}"

        return message
