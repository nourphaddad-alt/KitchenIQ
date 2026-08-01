from __future__ import annotations


def commission_on(
    amount: float,
    effective_rate: float | None,
) -> float:
    """
    Calculate the commission paid on a given revenue amount.

    If the effective commission rate is unavailable,
    return zero instead of failing.
    """

    if effective_rate is None:
        return 0.0

    return float(amount) * float(effective_rate)