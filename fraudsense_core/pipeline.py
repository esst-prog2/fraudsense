"""The one scoring path shared by `score` and `explain`."""

from fraudsense_core.features import amount_ratio, average_spend, window_counts
from fraudsense_core.ingest import load_transactions
from fraudsense_core.rules import score_transaction


def score_transactions(transactions):
    averages = average_spend(transactions)
    counts = window_counts(transactions)
    scored = []
    for txn in transactions:
        average = averages[txn.transaction_id]
        ratio = amount_ratio(txn.amount, average)
        scored.append(score_transaction(txn, average, ratio, counts[txn.transaction_id]))
    return scored


def score_file(path):
    """Return (scored transactions in file order, number of skipped rows)."""
    transactions, skipped = load_transactions(path)
    return score_transactions(transactions), skipped
