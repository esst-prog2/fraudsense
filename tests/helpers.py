"""Small builders for test transactions and CSV files."""

import csv
from datetime import datetime, timedelta
from pathlib import Path

from fraudsense_core.models import Transaction

BASE_TIME = datetime(2026, 9, 1, 12, 0, 0)
COLUMNS = ["transaction_id", "customer_id", "amount", "timestamp"]


def txn(transaction_id, customer_id="C1", amount=100.0, minutes=0):
    return Transaction(transaction_id, customer_id, amount, BASE_TIME + timedelta(minutes=minutes))


def customer_history(customer_id, amounts, start_minutes=0, gap_minutes=60, prefix=None):
    """One transaction per amount, spaced far enough apart that velocity never fires."""
    prefix = prefix or f"{customer_id}-"
    return [
        txn(f"{prefix}{i}", customer_id, amount, start_minutes + i * gap_minutes)
        for i, amount in enumerate(amounts)
    ]


def write_csv(path, rows, columns=COLUMNS):
    """Write raw rows (lists of strings) under a header."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return path


def write_transactions(path, transactions):
    return write_csv(
        path,
        [[t.transaction_id, t.customer_id, f"{t.amount}", t.timestamp.isoformat()] for t in transactions],
    )
