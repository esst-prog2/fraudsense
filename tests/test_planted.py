import csv
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPlantedTransaction(unittest.TestCase):
    def test_planted_transaction_is_flagged_and_ranked_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "reports"))
            subprocess.run(
                [
                    sys.executable,
                    os.path.join(ROOT, "fraudsense.py"),
                    "score",
                    os.path.join(ROOT, "tests", "data", "planted.csv"),
                ],
                cwd=tmp,
                check=True,
                capture_output=True,
            )
            with open(
                os.path.join(tmp, "reports", "fraud_report.csv"), newline=""
            ) as f:
                rows = list(csv.DictReader(f))

        ids = [row["transaction_id"] for row in rows]
        self.assertIn("T9001", ids)        # flagged: only high-risk rows are reported
        self.assertEqual(ids[0], "T9001")  # scores above every other flagged row