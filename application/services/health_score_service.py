from __future__ import annotations

from application.dto.analysis_result import AnalysisResult
from application.dto.health_score import HealthScore
from connectors.base.import_result import ImportOutcome


class HealthScoreService:
    def calculate(self, analysis_result: AnalysisResult) -> HealthScore:
        if analysis_result.outcome is ImportOutcome.FAILED:
            raise ValueError(
                "Health Score cannot be calculated for a failed Toters "
                "import."
            )

        metrics = analysis_result.metrics

        score = 100
        score -= self._deduction_for_platform_cost_rate(metrics.get("platform_cost_rate"))
        score -= self._deduction_for_marketing_cost_rate(metrics.get("marketing_cost_rate"))
        score -= self._deduction_for_marketing_order_share(metrics.get("marketing_order_share"))
        score -= self._deduction_for_retained_revenue_rate(metrics.get("retained_revenue_rate"))
        score = self._clamp_score(score)

        label = self._label_for_score(score)
        interpretation = self._interpretation_for_label(label)

        return HealthScore(score=score, label=label, interpretation=interpretation)

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(0, min(100, score))

    @staticmethod
    def _deduction_for_platform_cost_rate(value: object) -> int:
        if not isinstance(value, (int, float)):
            return 0
        if value > 0.50:
            return 30
        if 0.40 < value <= 0.50:
            return 22
        if 0.30 < value <= 0.40:
            return 12
        return 0

    @staticmethod
    def _deduction_for_marketing_cost_rate(value: object) -> int:
        if not isinstance(value, (int, float)):
            return 0
        if value > 0.25:
            return 20
        if 0.15 < value <= 0.25:
            return 12
        if 0.08 < value <= 0.15:
            return 6
        return 0

    @staticmethod
    def _deduction_for_marketing_order_share(value: object) -> int:
        if not isinstance(value, (int, float)):
            return 0
        if value > 0.80:
            return 15
        if 0.60 < value <= 0.80:
            return 10
        if 0.40 < value <= 0.60:
            return 5
        return 0

    @staticmethod
    def _deduction_for_retained_revenue_rate(value: object) -> int:
        if not isinstance(value, (int, float)):
            return 0
        if value < 0.45:
            return 20
        if 0.45 <= value < 0.55:
            return 12
        if 0.55 <= value < 0.65:
            return 6
        return 0

    @staticmethod
    def _label_for_score(score: int) -> str:
        if score >= 80:
            return "Strong"
        if score >= 65:
            return "Stable"
        if score >= 45:
            return "At Risk"
        return "Critical"

    @staticmethod
    def _interpretation_for_label(label: str) -> str:
        if label == "Strong":
            return "The business remains resilient under the current Toters mix."
        if label == "Stable":
            return "The business is performing within a manageable but watchful range."
        if label == "At Risk":
            return "The business is showing meaningful pressure that should be addressed promptly."
        return "The business is under significant strain and needs immediate attention."
