"""FraudSense: flag transactions worth a closer look, and explain why.

    python fraudsense.py score data/sample_transactions.csv
    python fraudsense.py explain --id T00231
"""

import argparse
import sys
import time

from fraudsense_core.explain import ExplainError, find_transaction, format_explanation
from fraudsense_core.ingest import IngestError
from fraudsense_core.pipeline import score_file
from fraudsense_core.report import REPORT_PATH, format_summary, write_report

DEFAULT_FILE = "data/sample_transactions.csv"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="fraudsense",
        description="Score transactions for fraud risk and explain the scores.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    score = commands.add_parser(
        "score", help=f"score a transaction CSV and write {REPORT_PATH.as_posix()}"
    )
    score.add_argument("csv", help="transaction CSV to score")

    explain = commands.add_parser(
        "explain", help="show the features and rules behind one transaction's score"
    )
    explain.add_argument("--id", required=True, help="transaction_id to explain")
    explain.add_argument(
        "--file", default=DEFAULT_FILE, help=f"transaction CSV (default: {DEFAULT_FILE})"
    )
    return parser


def run_score(csv_path):
    start = time.perf_counter()
    scored, skipped = score_file(csv_path)
    flagged = write_report(scored, REPORT_PATH)
    elapsed = time.perf_counter() - start
    print(format_summary(len(scored), elapsed, skipped, len(flagged), REPORT_PATH))


def run_explain(transaction_id, csv_path):
    scored, _ = score_file(csv_path)
    print(format_explanation(find_transaction(scored, transaction_id)))


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "score":
            run_score(args.csv)
        else:
            run_explain(args.id, args.file)
    except (IngestError, ExplainError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
