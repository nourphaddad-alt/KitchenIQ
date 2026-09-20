from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from domain.metric_definition import MetricDefinition


CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "kitchen_iq_metric_catalog.json"
)


class MetricRegistryError(ValueError):
    """Raised when the functional specification catalogue is invalid."""


def _normalise_filter(value: str) -> str:
    return " ".join(value.casefold().split())


@lru_cache(maxsize=1)
def load_metric_registry() -> tuple[MetricDefinition, ...]:
    """Load and validate the canonical KitchenIQ metric catalogue."""
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MetricRegistryError(
            f"Unable to load metric catalogue at {CATALOG_PATH}: {exc}"
        ) from exc

    if payload.get("schema_version") != 1:
        raise MetricRegistryError("Unsupported metric catalogue schema version")

    raw_metrics = payload.get("metrics")
    if not isinstance(raw_metrics, list):
        raise MetricRegistryError("Metric catalogue must contain a metrics list")

    try:
        metrics = tuple(MetricDefinition(**item) for item in raw_metrics)
    except (TypeError, ValueError) as exc:
        raise MetricRegistryError(f"Invalid metric definition: {exc}") from exc

    identifiers = [metric.metric_id for metric in metrics]
    duplicate_identifiers = sorted(
        identifier
        for identifier in set(identifiers)
        if identifiers.count(identifier) > 1
    )

    if duplicate_identifiers:
        raise MetricRegistryError(
            "Duplicate metric identifiers: "
            + ", ".join(duplicate_identifiers)
        )

    return metrics


def list_metrics(
    *,
    phase: str | None = None,
    section: str | None = None,
) -> tuple[MetricDefinition, ...]:
    """Return metrics, optionally filtered by exact phase or section name."""
    metrics: Iterable[MetricDefinition] = load_metric_registry()

    if phase is not None:
        expected_phase = _normalise_filter(phase)
        metrics = (
            metric
            for metric in metrics
            if _normalise_filter(metric.phase) == expected_phase
        )

    if section is not None:
        expected_section = _normalise_filter(section)
        metrics = (
            metric
            for metric in metrics
            if _normalise_filter(metric.section) == expected_section
        )

    return tuple(metrics)


def get_metric(metric_id: str) -> MetricDefinition:
    """Return one metric by stable identifier."""
    for metric in load_metric_registry():
        if metric.metric_id == metric_id:
            return metric

    raise KeyError(f"Unknown KitchenIQ metric: {metric_id}")


@lru_cache(maxsize=1)
def load_programmes() -> tuple[dict[str, object], ...]:
    """Return the source programme objectives that frame the metric set."""
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MetricRegistryError(
            f"Unable to load metric catalogue at {CATALOG_PATH}: {exc}"
        ) from exc

    programmes = payload.get("programmes")
    if not isinstance(programmes, list):
        raise MetricRegistryError("Metric catalogue must contain programmes")

    return tuple(dict(programme) for programme in programmes)
