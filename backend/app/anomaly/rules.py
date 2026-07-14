"""Pure, testable anomaly-detection rule functions.

Every function here is a *pure* function — it takes plain Python values (floats,
lists) and returns an ``AnomalyResult`` or ``None``.  No database, no FastAPI,
no mocking required to unit-test. thing in this project.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AnomalyResult:
    reason: str
    rule_triggered: str
    severity: str = "medium"


# ---------------------------------------------------------------------------
# Hard-cap defaults per category (placeholder numbers — configurable later)
# ---------------------------------------------------------------------------

HARD_CAPS: dict[str, float] = {
    "groceries": 5_000,
    "travel": 15_000,
    "rent": 12_000,        # used only as an upper sanity bound
    "student_loan": 10_000,
    "shopping": 8_000,
    "food": 2_000,
    "misc": 3_000,
}

Z_SCORE_THRESHOLD = 2.0
MIN_HISTORY_FOR_ZSCORE = 5
DAILY_SPIKE_MULTIPLIER = 3.0
RENT_DEVIATION_PCT = 0.10   # 10 %
LOAN_DEVIATION_PCT = 0.10   # 10 %


# ---------------------------------------------------------------------------
# Rule 1 — Category Z-score
# ---------------------------------------------------------------------------

def check_category_zscore(
    amount: float,
    category_history: list[float],
    threshold: float = Z_SCORE_THRESHOLD,
    min_history: int = MIN_HISTORY_FOR_ZSCORE,
) -> Optional[AnomalyResult]:
    """Flag if *amount* exceeds ``mean + threshold * stddev`` of past history."""
    if len(category_history) < min_history:
        return None
    mean = statistics.fmean(category_history)
    stdev = statistics.pstdev(category_history)
    if stdev == 0:
        # All prior amounts identical — any deviation above them is suspicious.
        if amount > mean:
            ratio = amount / mean if mean else float("inf")
            return AnomalyResult(
                reason=f"{ratio:.1f}x category average (all-history identical)",
                rule_triggered="z_score",
                severity="high" if ratio >= 2 else "medium",
            )
        return None
    z = (amount - mean) / stdev
    if z > threshold:
        avg = mean if mean else 1
        ratio = amount / avg
        return AnomalyResult(
            reason=f"{ratio:.1f}x category average (z={z:.2f})",
            rule_triggered="z_score",
            severity="high" if z >= 3 else "medium",
        )
    return None


# ---------------------------------------------------------------------------
# Rule 2 — Hard-cap
# ---------------------------------------------------------------------------

def check_hard_cap(
    amount: float,
    category: str,
    caps: Optional[dict[str, float]] = None,
) -> Optional[AnomalyResult]:
    """Simple upper-bound check per category — good cold-start fallback."""
    caps = caps or HARD_CAPS
    cap = caps.get(category)
    if cap is None:
        return None
    if amount > cap:
        return AnomalyResult(
            reason=f"{category} expense {amount:.2f} exceeds cap of {cap:.2f}",
            rule_triggered="hard_cap",
            severity="high" if amount > cap * 2 else "medium",
        )
    return None


def check_rent_deviation(
    amount: float,
    last_rent: Optional[float],
    deviation_pct: float = RENT_DEVIATION_PCT,
) -> Optional[AnomalyResult]:
    """Rent should be near-constant — flag > 10 % deviation from last payment."""
    if last_rent is None or last_rent == 0:
        return None
    diff = abs(amount - last_rent) / last_rent
    if diff > deviation_pct:
        direction = "up" if amount > last_rent else "down"
        return AnomalyResult(
            reason=f"Rent {direction} {diff*100:.1f}% from last payment ({last_rent:.2f})",
            rule_triggered="rent_mismatch",
            severity="high" if diff > 0.25 else "medium",
        )
    return None


def check_loan_deviation(
    amount: float,
    last_loan: Optional[float],
    deviation_pct: float = LOAN_DEVIATION_PCT,
) -> Optional[AnomalyResult]:
    """Student loan amounts also should be stable — flag deviations > 10 %."""
    if last_loan is None or last_loan == 0:
        return None
    diff = abs(amount - last_loan) / last_loan
    if diff > deviation_pct:
        direction = "up" if amount > last_loan else "down"
        return AnomalyResult(
            reason=f"Student loan {direction} {diff*100:.1f}% from last payment ({last_loan:.2f})",
            rule_triggered="loan_mismatch",
            severity="medium",
        )
    return None


# ---------------------------------------------------------------------------
# Rule 3 — Daily total spike
# ---------------------------------------------------------------------------

def check_daily_spike(
    today_total: float,
    avg_daily: float,
    multiplier: float = DAILY_SPIKE_MULTIPLIER,
) -> Optional[AnomalyResult]:
    """Flag if today's cumulative spend is > 3× the 30-day daily average."""
    if avg_daily <= 0:
        return None
    if today_total > avg_daily * multiplier:
        ratio = today_total / avg_daily
        return AnomalyResult(
            reason=f"Daily total {today_total:.2f} is {ratio:.1f}x the 30-day average",
            rule_triggered="daily_spike",
            severity="high" if ratio >= 5 else "medium",
        )
    return None


# ---------------------------------------------------------------------------
# Rule 4 — Frequency (optional)
# ---------------------------------------------------------------------------

def check_frequency(
    count_today: int,
    threshold: int = 3,
) -> Optional[AnomalyResult]:
    """Flag if the same category has ``threshold``+ expenses in one day."""
    if count_today >= threshold:
        return AnomalyResult(
            reason=f"{count_today} expenses in this category logged today (possible duplicate)",
            rule_triggered="frequency",
            severity="low",
        )
    return None