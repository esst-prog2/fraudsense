"""End-to-end: run fraudsense.py as a subprocess, the way a user would."""

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import customer_history, txn, write_csv, write_transactions

SCRIPT = Path(__file__).resolve().parent.parent / "fraudsense.py"


def fixture_transactions():
    spike = customer_history("C1", [95, 105, 100, 98, 102, 800], prefix="A")
    burst = [txn(f"B{i}", "C2", 40, 600 + m) for i, m in enumerate([0, 1, 3, 5, 6, 8])]
    quiet = customer_history("C3", [20, 25, 22, 21], prefix="Q")
    return spike + burst + quiet


class CliTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.dir = Path(self._dir.name)
        self.csv = write_transactions(self.dir / "tx.csv", fixture_transactions())

    def tearDown(self):
        self._dir.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.dir, capture_output=True, text=True,
        )

    def read_report(self):
        with (self.dir / "reports" / "fraud_report.csv").open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_help_lists_both_subcommands(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("score", result.stdout)
        self.assertIn("explain", result.stdout)

    def test_score_writes_report_and_summary(self):
        result = self.run_cli("score", str(self.csv))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Scored 16 transactions", result.stdout)
        self.assertIn("3 flagged as high-risk (score > 0.75)", result.stdout)
        self.assertIn("reports/fraud_report.csv", result.stdout)
        ids = [row["transaction_id"] for row in self.read_report()]
        self.assertEqual(sorted(ids), ["A5", "B4", "B5"])

    def test_explain_matches_report(self):
        self.run_cli("score", str(self.csv))
        for row in self.read_report():
            result = self.run_cli("explain", "--id", row["transaction_id"], "--file", str(self.csv))
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertEqual(lines[0], f"Transaction {row['transaction_id']} - risk score {row['risk_score']}")
            self.assertEqual("; ".join(line.strip() for line in lines[1:]), row["reasons"])

    def test_explain_defaults_to_the_sample_file(self):
        (self.dir / "data").mkdir()
        write_transactions(self.dir / "data" / "sample_transactions.csv", fixture_transactions())
        result = self.run_cli("explain", "--id", "A5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Transaction A5", result.stdout)

    def test_explain_unknown_id(self):
        result = self.run_cli("explain", "--id", "T99999", "--file", str(self.csv))
        self.assertEqual(result.returncode, 1)
        self.assertIn("T99999", result.stderr)

    def test_missing_column_exits_without_report(self):
        bad = write_csv(self.dir / "bad.csv", [["T1", "C1", "2026-09-01T12:00:00"]],
                        columns=["transaction_id", "customer_id", "timestamp"])
        result = self.run_cli("score", str(bad))
        self.assertEqual(result.returncode, 1)
        self.assertIn("amount", result.stderr)
        self.assertFalse((self.dir / "reports").exists())


if __name__ == "__main__":
    unittest.main()
