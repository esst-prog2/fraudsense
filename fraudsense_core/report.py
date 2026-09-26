"""The run summary and the flagged-transaction CSV."""

import csv
from pathlib import Path

from fraudsense_core.rules import FLAG_THRESHOLD

REPORT_PATH = Path("reports") / "fraud_report.csv"
REPORT_COLUMNS = (
    "transaction_id",
    "customer_id",
    "amount",
    "timestamp",
    "risk_score",
    "reasons",
)


def flagged_transactions(scored):
    """Transactions above FLAG_THRESHOLD, highest score first."""
    return sorted(
        (s for s in scored if s.score > FLAG_THRESHOLD),
        key=lambda s: (-s.score, s.transaction.transaction_id),
    )


def write_report(scored, path=REPORT_PATH):
    """Write the flagged transactions to `path`, replacing any earlier report."""
    flagged = flagged_transactions(scored)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REPORT_COLUMNS)
        for s in flagged:
            txn = s.transaction
            writer.writerow([
                txn.transaction_id,
                txn.customer_id,
                f"{txn.amount:.2f}",
                txn.timestamp.isoformat(),
                f"{s.score:.2f}",
                "; ".join(s.reasons),
            ])
    return flagged


def _count(n, noun):
    return f"{n} {noun}" + ("" if n == 1 else "s")


def format_summary(scored_count, seconds, skipped, flagged_count, report_path):
    lines = [f"Scored {_count(scored_count, 'transaction')} in {seconds:.2f}s."]
    if skipped:
        lines.append(f"Skipped {_count(skipped, 'malformed row')}.")
    lines.append(f"{flagged_count} flagged as high-risk (score > {FLAG_THRESHOLD:.2f}).")
    lines.append(f"Report written to {Path(report_path).as_posix()}.")
    return "\n".join(lines)
