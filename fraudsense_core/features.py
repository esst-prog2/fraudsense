"""Per-customer behavioural features, computed from the scored file only."""

import math
from collections import defaultdict
from datetime import timedelta

MIN_OTHER_TRANSACTIONS = 3
VELOCITY_WINDOW = timedelta(minutes=10)


def _by_customer(transactions):
    groups = defaultdict(list)
    for txn in transactions:
        groups[txn.customer_id].append(txn)
    return groups.values()


def average_spend(transactions):
    """Map transaction_id to the mean amount of the customer's *other* transactions.

    The value is None when the customer has fewer than MIN_OTHER_TRANSACTIONS
    other transactions, or when that mean is 0 (no meaningful ratio).
    """
    result = {}
    for txns in _by_customer(transactions):
        total = math.fsum(t.amount for t in txns)
        others = len(txns) - 1
        for txn in txns:
            if others < MIN_OTHER_TRANSACTIONS:
                result[txn.transaction_id] = None
                continue
            average = (total - txn.amount) / others
            result[txn.transaction_id] = average if average > 0 else None
    return result


def amount_ratio(amount, average):
    if average is None:
        return None
    # Rounding absorbs float noise so 500 / 100.00000000001 still counts as 5x.
    return round(amount / average, 9)


def window_counts(transactions):
    """Map transaction_id to how many of the customer's transactions fall in
    [timestamp - VELOCITY_WINDOW, timestamp], itself and same-time ties included."""
    result = {}
    for txns in _by_customer(transactions):
        ordered = sorted(txns, key=lambda t: t.timestamp)
        times = [t.timestamp for t in ordered]
        left = right = 0
        for txn in ordered:
            while times[left] < txn.timestamp - VELOCITY_WINDOW:
                left += 1
            while right < len(times) and times[right] <= txn.timestamp:
                right += 1
            result[txn.transaction_id] = right - left
    return result
