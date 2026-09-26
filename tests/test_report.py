import csv
import tempfile
import unittest
from pathlib import Path

from fraudsense_core.report import REPORT_COLUMNS, format_summary, write_report
from fraudsense_core.rules import score_transaction
from tests.helpers import txn


def scored_set():
    return [
        score_transaction(txn("LOW", amount=100), 100, 1.0, 1),        # 0.00, not flagged
        score_transaction(txn("MID", amount=600), 100, 6.0, 1),        # 0.84
        score_transaction(txn("TOP", amount=4200), 525, 8.0, 6),       # 0.92, both rules
        score_transaction(txn("NEAR", amount=490), 100, 4.9, 4),       # < 0.75, not flagged
    ]


def read_report(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


class WriteReportTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "reports" / "fraud_report.csv"

    def tearDown(self):
        self._dir.cleanup()

    def test_only_flagged_rows_sorted_highest_first(self):
        write_report(scored_set(), self.path)
        rows = read_report(self.path)
        self.assertEqual(tuple(rows[0]), REPORT_COLUMNS)
        self.assertEqual([r[0] for r in rows[1:]], ["TOP", "MID"])
        top = dict(zip(REPORT_COLUMNS, rows[1]))
        self.assertEqual(top["risk_score"], "0.92")
        self.assertEqual(top["amount"], "4200.00")
        self.assertEqual(top["timestamp"], "2026-09-01T12:00:00")
        self.assertEqual(
            top["reasons"],
            "amount $4,200 is 8.0x this customer's average ($525); "
            "6 transactions in the last 10 minutes (rule fires at 5)",
        )

    def test_nothing_flagged_writes_header_only(self):
        flagged = write_report(scored_set()[:1], self.path)
        self.assertEqual(flagged, [])
        self.assertEqual(read_report(self.path), [list(REPORT_COLUMNS)])

    def test_earlier_report_is_overwritten(self):
        write_report(scored_set(), self.path)
        write_report(scored_set()[:1], self.path)
        self.assertEqual(len(read_report(self.path)), 1)


class SummaryTest(unittest.TestCase):
    def test_summary_text(self):
        text = format_summary(500, 2.3, 0, 14, Path("reports") / "fraud_report.csv")
        self.assertEqual(
            text,
            "Scored 500 transactions in 2.30s.\n"
            "14 flagged as high-risk (score > 0.75).\n"
            "Report written to reports/fraud_report.csv.",
        )

    def test_summary_mentions_skipped_rows(self):
        text = format_summary(499, 0.1, 1, 0, "reports/fraud_report.csv")
        self.assertIn("Skipped 1 malformed row.", text)
        self.assertIn("0 flagged as high-risk (score > 0.75).", text)


if __name__ == "__main__":
    unittest.main()
