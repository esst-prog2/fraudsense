"""The evaluate command: labels, confusion counts, n/a ratios and the CLI."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fraudsense_core.evaluate import (
    CUTOFFS,
    EvaluateError,
    confusion_at,
    format_evaluation,
    labels_for,
    load_labels,
    ratios,
)
from fraudsense_core.pipeline import score_file
from tests.helpers import write_csv

SCRIPT = Path(__file__).resolve().parent.parent / "fraudsense.py"
COLUMNS = ["transaction_id", "customer_id", "amount", "timestamp", "is_fraud"]


def day(n):
    return f"2026-09-{n:02d}T12:00:00"


def fixture_rows():
    """15 rows, scores worked out by hand from rules.py, one row per day so velocity never fires.

    A7: 800 / mean(100 x 6) = 8x   -> 0.80 + 0.20 * (8 - 5) / 5 = 0.92, fraud
    B7: 600 / mean(50 x 6)  = 12x  -> capped at 1.00, not fraud
    C1: only transaction of C, no average -> 0.00, fraud (missed)
    A1-A6: 100 / mean(5 x 100 + 800) = 0.46x -> 0.00;  B1-B6 likewise 0.00
    """
    rows = [[f"A{i}", "A", "100.00", day(i), "0"] for i in range(1, 7)]
    rows.append(["A7", "A", "800.00", day(7), "1"])
    rows += [[f"B{i}", "B", "50.00", day(i), "0"] for i in range(1, 7)]
    rows.append(["B7", "B", "600.00", day(7), "0"])
    rows.append(["C1", "C", "30.00", day(1), "1"])
    return rows


def quiet_rows(fraud_label):
    """Five ordinary rows for one customer; none scores above 0.75."""
    return [[f"Q{i}", "Q", "20.00", day(i), fraud_label] for i in range(1, 6)]


class EvaluateTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.dir = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def write(self, rows, columns=COLUMNS, name="labelled.csv"):
        return write_csv(self.dir / name, rows, columns)

    def evaluate(self, rows, **kwargs):
        path = self.write(rows, **kwargs)
        scored, skipped = score_file(path)
        return scored, load_labels(path), skipped

    def table(self, rows):
        """{cutoff text: {column: cell}} parsed from the printed table."""
        output = format_evaluation(*self.evaluate(rows))
        lines = output.split("\n\n", 1)[1].splitlines()
        header = lines[0].split()
        return {line.split()[0]: dict(zip(header, line.split())) for line in lines[1:]}


class FixtureTest(EvaluateTestCase):
    def test_hand_computed_scores(self):
        scored, _, _ = self.evaluate(fixture_rows())
        self.assertEqual(len(scored), 15)
        above = {s.transaction.transaction_id for s in scored if s.score > 0.75}
        self.assertEqual(above, {"A7", "B7"})

    def test_counts_at_075(self):
        row = self.table(fixture_rows())["0.75"]
        self.assertEqual(
            [row[c] for c in ("flagged", "TP", "FP", "FN", "precision", "recall", "F1")],
            ["2", "1", "1", "1", "0.500", "0.500", "0.500"],
        )

    def test_only_the_1_00_row_stays_flagged_at_095(self):
        row = self.table(fixture_rows())["0.95"]
        self.assertEqual(
            [row[c] for c in ("flagged", "TP", "FP", "FN", "precision", "recall", "F1")],
            ["1", "0", "1", "2", "0.000", "0.000", "0.000"],
        )

    def test_one_row_per_cutoff_in_order(self):
        self.assertEqual(list(self.table(fixture_rows())), ["0.75", "0.80", "0.85", "0.90", "0.95"])

    def test_summary_line(self):
        output = format_evaluation(*self.evaluate(fixture_rows()))
        self.assertEqual(
            output.splitlines()[0],
            "Evaluated 15 transactions against the is_fraud labels: 2 fraud, 13 not fraud.",
        )
        self.assertNotIn("Skipped", output)

    def test_skipped_line_only_when_rows_were_skipped(self):
        rows = fixture_rows() + [["X1", "X", "lots", day(1), "0"]]
        lines = format_evaluation(*self.evaluate(rows)).splitlines()
        self.assertEqual(lines[1], "Skipped 1 malformed row.")

    def test_flag_test_is_strictly_greater(self):
        scored, labels, _ = self.evaluate(fixture_rows())
        is_fraud = labels_for(scored, labels)
        a7 = next(s for s in scored if s.transaction.transaction_id == "A7")
        tp, _, _ = confusion_at(scored, is_fraud, a7.score)
        self.assertEqual(tp, 0)  # a score equal to the cutoff is not flagged


class NotApplicableTest(EvaluateTestCase):
    def test_nothing_flagged(self):
        for row in self.table(quiet_rows("1")).values():
            self.assertEqual((row["precision"], row["recall"], row["F1"]), ("n/a", "0.000", "n/a"))

    def test_no_fraud_in_file(self):
        rows = [r[:4] + ["0"] for r in fixture_rows()]
        row = self.table(rows)["0.75"]
        self.assertEqual((row["precision"], row["recall"], row["F1"]), ("0.000", "n/a", "n/a"))

    def test_neither_defined(self):
        for row in self.table(quiet_rows("0")).values():
            self.assertEqual((row["precision"], row["recall"], row["F1"]), ("n/a", "n/a", "n/a"))

    def test_ratios_directly(self):
        self.assertEqual(ratios(0, 0, 3), (None, 0.0, None))
        self.assertEqual(ratios(0, 2, 0), (0.0, None, None))
        self.assertEqual(ratios(0, 0, 0), (None, None, None))
        self.assertEqual(ratios(0, 1, 2), (0.0, 0.0, 0.0))


class LabelTest(EvaluateTestCase):
    def test_missing_column(self):
        path = self.write([r[:4] for r in fixture_rows()], columns=COLUMNS[:4])
        with self.assertRaises(EvaluateError) as caught:
            load_labels(path)
        self.assertEqual(str(caught.exception), "missing required column: is_fraud")

    def test_header_matched_like_ingest(self):
        path = self.dir / "bom.csv"
        lines = ["﻿transaction_id, customer_id ,amount,timestamp, is_fraud "]
        lines += [",".join(r) for r in fixture_rows()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertEqual(load_labels(path)["A7"], "1")

    def test_bad_label_on_scored_row(self):
        for bad in ("2", "", "1.0", "yes"):
            with self.subTest(label=bad):
                rows = fixture_rows()
                rows[4][4] = bad  # A5
                scored, labels, _ = self.evaluate(rows)
                with self.assertRaises(EvaluateError) as caught:
                    labels_for(scored, labels)
                self.assertIn("A5", str(caught.exception))
                self.assertIn(f"'{bad}'", str(caught.exception))

    def test_spaces_around_label_are_trimmed(self):
        rows = fixture_rows()
        rows[6][4] = " 1 "
        scored, labels, _ = self.evaluate(rows)
        self.assertEqual(sum(labels_for(scored, labels)), 2)

    def test_bad_label_on_skipped_row_is_ignored(self):
        rows = fixture_rows() + [["X1", "X", "lots", day(1), "yes"]]
        output = format_evaluation(*self.evaluate(rows))
        self.assertIn("Evaluated 15 transactions", output)
        self.assertIn("Skipped 1 malformed row.", output)

    def test_repeated_id_uses_first_row(self):
        rows = fixture_rows() + [["C1", "C", "30.00", day(2), "maybe"]]
        scored, labels, skipped = self.evaluate(rows)
        self.assertEqual(skipped, 1)
        self.assertEqual(labels["C1"], "1")
        self.assertEqual(sum(labels_for(scored, labels)), 2)

    def test_repeated_id_after_malformed_row_uses_the_scored_row(self):
        rows = fixture_rows()[:-1] + [
            ["C1", "C", "lots", day(1), "1"],
            ["C1", "C", "30.00", day(2), "0"],
        ]
        scored, labels, _ = self.evaluate(rows)
        c1 = next(s for s in scored if s.transaction.transaction_id == "C1")
        self.assertEqual(c1.transaction.amount, 30.0)
        self.assertEqual(labels["C1"], "0")


class CliTest(EvaluateTestCase):
    def run_cli(self, path):
        cwd = self.dir / "cwd"
        cwd.mkdir(exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "evaluate", str(path)],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result, cwd

    def test_success_prints_summary_and_table_and_writes_nothing(self):
        result, cwd = self.run_cli(self.write(fixture_rows()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("Evaluated 15 transactions"))
        self.assertEqual(lines[1], "")
        self.assertEqual(lines[2].split(), ["cutoff", "flagged", "TP", "FP", "FN", "precision", "recall", "F1"])
        self.assertEqual(len(lines), 3 + len(CUTOFFS))
        self.assertEqual(os.listdir(cwd), [])
        self.assertEqual(sorted(os.listdir(self.dir)), ["cwd", "labelled.csv"])

    def test_missing_column_exit_1(self):
        result, cwd = self.run_cli(self.write([r[:4] for r in fixture_rows()], columns=COLUMNS[:4]))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.strip(), "error: missing required column: is_fraud")
        self.assertEqual(result.stdout, "")
        self.assertEqual(os.listdir(cwd), [])

    def test_bad_label_exit_1(self):
        rows = fixture_rows()
        rows[0][4] = "2"
        result, _ = self.run_cli(self.write(rows))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr.strip(),
            "error: transaction A1 has is_fraud value '2' (expected 0 or 1)",
        )

    def test_ingest_error_exit_1(self):
        result, _ = self.run_cli(self.dir / "missing.csv")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith("error: input file not found"))


if __name__ == "__main__":
    unittest.main()
