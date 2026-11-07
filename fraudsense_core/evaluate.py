"""Check the program's flags against the is_fraud labels in the scored file."""

import csv
from pathlib import Path

from fraudsense_core.ingest import REQUIRED_COLUMNS, _parse_row

LABEL_COLUMN = "is_fraud"
CUTOFFS = (0.75, 0.80, 0.85, 0.90, 0.95)
TABLE_COLUMNS = ("cutoff", "flagged", "TP", "FP", "FN", "precision", "recall", "F1")


class EvaluateError(Exception):
    """The labels can't be used to evaluate the file."""


def load_labels(path):
    """Map transaction_id to its raw is_fraud text.

    The label comes from the row ingest keeps for that id: the first row
    that parses. Ingest has already checked the file opens and has the
    scoring columns, so only the label column is checked here.
    """
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = [name.strip() for name in next(reader, [])]
        if LABEL_COLUMN not in header:
            raise EvaluateError(f"missing required column: {LABEL_COLUMN}")
        index = {column: header.index(column) for column in REQUIRED_COLUMNS}
        label_index = header.index(LABEL_COLUMN)

        labels = {}
        for row in reader:
            txn = _parse_row(row, index)
            if txn is None or txn.transaction_id in labels:
                continue
            labels[txn.transaction_id] = (
                row[label_index].strip() if label_index < len(row) else ""
            )
    return labels


def labels_for(scored, labels):
    """Return True (fraud) or False for each scored transaction, in order."""
    result = []
    for s in scored:
        transaction_id = s.transaction.transaction_id
        value = labels[transaction_id]
        if value not in ("0", "1"):
            raise EvaluateError(
                f"transaction {transaction_id} has {LABEL_COLUMN} value "
                f"'{value}' (expected 0 or 1)"
            )
        result.append(value == "1")
    return result


def confusion_at(scored, is_fraud, cutoff):
    """Return (TP, FP, FN) when a transaction is flagged at score > cutoff."""
    tp = fp = fn = 0
    for s, fraud in zip(scored, is_fraud):
        flagged = s.score > cutoff
        if flagged and fraud:
            tp += 1
        elif flagged:
            fp += 1
        elif fraud:
            fn += 1
    return tp, fp, fn


def ratios(tp, fp, fn):
    """Return (precision, recall, F1), each None when undefined."""
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None:
        f1 = None
    elif precision == recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def _ratio(value):
    return "n/a" if value is None else f"{value:.3f}"


def _count(n, noun):
    return f"{n} {noun}" + ("" if n == 1 else "s")


def _table(rows):
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "\n".join(
        "  ".join(cell.rjust(width) for cell, width in zip(row, widths)) for row in rows
    )


def format_evaluation(scored, labels, skipped):
    is_fraud = labels_for(scored, labels)
    fraud = sum(is_fraud)
    lines = [
        f"Evaluated {_count(len(scored), 'transaction')} against the "
        f"{LABEL_COLUMN} labels: {fraud} fraud, {len(scored) - fraud} not fraud."
    ]
    if skipped:
        lines.append(f"Skipped {_count(skipped, 'malformed row')}.")

    rows = [TABLE_COLUMNS]
    for cutoff in CUTOFFS:
        tp, fp, fn = confusion_at(scored, is_fraud, cutoff)
        rows.append(
            (f"{cutoff:.2f}", str(tp + fp), str(tp), str(fp), str(fn))
            + tuple(_ratio(r) for r in ratios(tp, fp, fn))
        )
    lines.append("")
    lines.append(_table(rows))
    return "\n".join(lines)
