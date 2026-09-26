import tempfile
import unittest
from pathlib import Path

from fraudsense_core.ingest import IngestError, load_transactions
from tests.helpers import write_csv

GOOD_ROW = ["T1", "C1", "100", "2026-09-01T12:00:00"]


class IngestTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.dir = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()


class RequiredColumnsTest(IngestTestCase):
    def test_missing_amount_is_named(self):
        path = write_csv(
            self.dir / "in.csv",
            [["T1", "C1", "2026-09-01T12:00:00"]],
            columns=["transaction_id", "customer_id", "timestamp"],
        )
        with self.assertRaises(IngestError) as ctx:
            load_transactions(path)
        self.assertIn("amount", str(ctx.exception))

    def test_several_missing_columns_are_all_named(self):
        path = write_csv(
            self.dir / "in.csv",
            [["T1", "2026-09-01T12:00:00"]],
            columns=["transaction_id", "timestamp"],
        )
        with self.assertRaises(IngestError) as ctx:
            load_transactions(path)
        self.assertIn("amount", str(ctx.exception))
        self.assertIn("customer_id", str(ctx.exception))

    def test_extra_columns_are_allowed(self):
        path = write_csv(
            self.dir / "in.csv",
            [["Paris", "T1", "C1", "100", "2026-09-01T12:00:00", "card"]],
            columns=["location", "transaction_id", "customer_id", "amount", "timestamp", "payment_method"],
        )
        transactions, skipped = load_transactions(path)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].amount, 100.0)
        self.assertEqual(skipped, 0)


class FileErrorsTest(IngestTestCase):
    def test_file_not_found_names_the_path(self):
        missing = self.dir / "nope.csv"
        with self.assertRaises(IngestError) as ctx:
            load_transactions(missing)
        self.assertIn(str(missing), str(ctx.exception))

    def test_empty_file(self):
        path = self.dir / "empty.csv"
        path.write_text("")
        with self.assertRaises(IngestError) as ctx:
            load_transactions(path)
        self.assertIn("empty", str(ctx.exception))

    def test_header_only_file(self):
        path = write_csv(self.dir / "in.csv", [])
        with self.assertRaises(IngestError) as ctx:
            load_transactions(path)
        self.assertIn("no valid transactions", str(ctx.exception))


class MalformedRowsTest(IngestTestCase):
    def load(self, rows):
        return load_transactions(write_csv(self.dir / "in.csv", rows))

    def test_unparseable_amount_is_skipped_and_counted(self):
        transactions, skipped = self.load([GOOD_ROW, ["T2", "C1", "abc", "2026-09-01T12:05:00"]])
        self.assertEqual([t.transaction_id for t in transactions], ["T1"])
        self.assertEqual(skipped, 1)

    def test_negative_amount_is_skipped(self):
        _, skipped = self.load([GOOD_ROW, ["T2", "C1", "-5", "2026-09-01T12:05:00"]])
        self.assertEqual(skipped, 1)

    def test_bad_timestamp_is_skipped(self):
        _, skipped = self.load([GOOD_ROW, ["T2", "C1", "10", "yesterday"]])
        self.assertEqual(skipped, 1)

    def test_empty_ids_are_skipped(self):
        _, skipped = self.load([
            GOOD_ROW,
            ["", "C1", "10", "2026-09-01T12:05:00"],
            ["T3", " ", "10", "2026-09-01T12:05:00"],
        ])
        self.assertEqual(skipped, 2)

    def test_duplicate_transaction_id_keeps_the_first(self):
        transactions, skipped = self.load([
            ["T00001", "C1", "100", "2026-09-01T12:00:00"],
            ["T00001", "C2", "999", "2026-09-01T12:05:00"],
        ])
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].customer_id, "C1")
        self.assertEqual(skipped, 1)

    def test_minority_timezone_kind_is_skipped(self):
        transactions, skipped = self.load([
            GOOD_ROW,
            ["T2", "C1", "10", "2026-09-01T12:05:00"],
            ["T3", "C1", "10", "2026-09-01T12:10:00+02:00"],
        ])
        self.assertEqual([t.transaction_id for t in transactions], ["T1", "T2"])
        self.assertEqual(skipped, 1)

    def test_no_valid_rows_is_an_error(self):
        with self.assertRaises(IngestError) as ctx:
            self.load([["T1", "C1", "abc", "2026-09-01T12:00:00"], ["T2", "C1", "10", "never"]])
        self.assertIn("no valid transactions", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
