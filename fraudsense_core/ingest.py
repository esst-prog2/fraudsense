"""Load a transaction CSV, check its columns and drop rows that can't be scored."""

import csv
import math
from datetime import datetime
from pathlib import Path

from fraudsense_core.models import Transaction

REQUIRED_COLUMNS = ("transaction_id", "customer_id", "amount", "timestamp")


class IngestError(Exception):
    """The input file can't be scored at all."""


def load_transactions(path):
    """Return (valid transactions in file order, number of skipped rows)."""
    path = Path(path)
    if not path.is_file():
        raise IngestError(f"input file not found: {path}")
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            transactions, skipped = _read_rows(csv.reader(f), path)
    except UnicodeDecodeError:
        raise IngestError(f"input file is not valid UTF-8 text: {path}") from None

    transactions, dropped = _drop_minority_timezone_kind(transactions)
    skipped += dropped
    if not transactions:
        raise IngestError(
            f"no valid transactions found in {path} ({skipped} rows skipped)"
        )
    return transactions, skipped


def _read_rows(reader, path):
    header = next(reader, None)
    if header is None:
        raise IngestError(f"input file is empty: {path}")
    header = [name.strip() for name in header]
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise IngestError("missing required column(s): " + ", ".join(missing))
    index = {column: header.index(column) for column in REQUIRED_COLUMNS}

    transactions, skipped, seen_ids = [], 0, set()
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue  # blank line, not a row
        txn = _parse_row(row, index)
        if txn is None or txn.transaction_id in seen_ids:
            skipped += 1
            continue
        seen_ids.add(txn.transaction_id)
        transactions.append(txn)
    return transactions, skipped


def _parse_row(row, index):
    def cell(column):
        i = index[column]
        return row[i].strip() if i < len(row) else ""

    transaction_id, customer_id = cell("transaction_id"), cell("customer_id")
    if not transaction_id or not customer_id:
        return None
    try:
        amount = float(cell("amount"))
        timestamp = datetime.fromisoformat(cell("timestamp"))
    except ValueError:
        return None
    if not math.isfinite(amount) or amount < 0:
        return None
    return Transaction(transaction_id, customer_id, amount, timestamp)


def _drop_minority_timezone_kind(transactions):
    """Naive and timezone-aware timestamps can't be compared, so keep the majority kind."""
    aware = sum(1 for t in transactions if t.timestamp.tzinfo is not None)
    naive = len(transactions) - aware
    if not aware or not naive:
        return transactions, 0
    keep_aware = aware > naive
    kept = [t for t in transactions if (t.timestamp.tzinfo is not None) == keep_aware]
    return kept, len(transactions) - len(kept)
