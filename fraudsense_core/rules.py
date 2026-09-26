"""The amount and velocity rules, their sub-scores and reason text."""

from fraudsense_core.features import VELOCITY_WINDOW
from fraudsense_core.models import ScoredTransaction

AMOUNT_RULE = "amount"
VELOCITY_RULE = "velocity"

AMOUNT_RATIO_THRESHOLD = 5.0
VELOCITY_COUNT_THRESHOLD = 5
FLAG_THRESHOLD = 0.75

# A fired rule scores FIRED_BASE, rising to FIRED_MAX at the *_FOR_MAX values.
# Below its threshold a rule scales from 0 up to FLAG_THRESHOLD, so a
# transaction is flagged exactly when at least one rule fires.
FIRED_BASE = 0.80
FIRED_MAX = 1.00
AMOUNT_RATIO_FOR_MAX = 10.0
VELOCITY_COUNT_FOR_MAX = 10


def _clamp(value):
    return max(0.0, min(1.0, value))


def _subscore(value, threshold, value_for_max):
    if value >= threshold:
        progress = _clamp((value - threshold) / (value_for_max - threshold))
        return FIRED_BASE + (FIRED_MAX - FIRED_BASE) * progress
    return FLAG_THRESHOLD * _clamp((value - 1) / (threshold - 1))


def amount_fires(ratio):
    return ratio is not None and ratio >= AMOUNT_RATIO_THRESHOLD


def velocity_fires(count):
    return count >= VELOCITY_COUNT_THRESHOLD


def amount_subscore(ratio):
    if ratio is None:
        return 0.0
    return _subscore(ratio, AMOUNT_RATIO_THRESHOLD, AMOUNT_RATIO_FOR_MAX)


def velocity_subscore(count):
    return _subscore(count, VELOCITY_COUNT_THRESHOLD, VELOCITY_COUNT_FOR_MAX)


def format_money(value):
    """$4,200 for whole-dollar values, $4,200.50 otherwise."""
    if round(value, 2) == round(value):
        return f"${round(value):,}"
    return f"${value:,.2f}"


def amount_reason(amount, average, ratio):
    return (
        f"amount {format_money(amount)} is {ratio:.1f}x "
        f"this customer's average ({format_money(round(average))})"
    )


def velocity_reason(count):
    minutes = int(VELOCITY_WINDOW.total_seconds() // 60)
    return (
        f"{count} transactions in the last {minutes} minutes "
        f"(rule fires at {VELOCITY_COUNT_THRESHOLD})"
    )


def score_transaction(txn, average, ratio, window_count):
    fired, reasons = [], []
    if amount_fires(ratio):
        fired.append(AMOUNT_RULE)
        reasons.append(amount_reason(txn.amount, average, ratio))
    if velocity_fires(window_count):
        fired.append(VELOCITY_RULE)
        reasons.append(velocity_reason(window_count))
    score = max(amount_subscore(ratio), velocity_subscore(window_count))
    return ScoredTransaction(
        transaction=txn,
        average_spend=average,
        amount_ratio=ratio,
        window_count=window_count,
        fired=tuple(fired),
        reasons=tuple(reasons),
        score=score,
    )
