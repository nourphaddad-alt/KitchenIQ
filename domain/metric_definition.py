from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """One auditable business metric from the KitchenIQ specification."""

    metric_id: str
    phase: str
    section: str
    element: str
    definition: str
    benefit: str
    problem_solved: str
    key_metric: str
    healthy_benchmark: str
    red_flag: str
    recommended_action: str
    data_needed: str
    outcome_delivered: str
    automation: str
    source_line: int

    def __post_init__(self) -> None:
        required_values = {
            "metric_id": self.metric_id,
            "phase": self.phase,
            "section": self.section,
            "element": self.element,
            "definition": self.definition,
            "benefit": self.benefit,
            "problem_solved": self.problem_solved,
            "key_metric": self.key_metric,
            "healthy_benchmark": self.healthy_benchmark,
            "red_flag": self.red_flag,
            "recommended_action": self.recommended_action,
            "data_needed": self.data_needed,
            "outcome_delivered": self.outcome_delivered,
            "automation": self.automation,
        }

        missing = [
            field_name
            for field_name, value in required_values.items()
            if not value.strip()
        ]

        if missing:
            raise ValueError(
                f"Metric {self.metric_id!r} has empty required fields: "
                + ", ".join(missing)
            )

        if self.source_line < 1:
            raise ValueError("source_line must be a positive integer")
