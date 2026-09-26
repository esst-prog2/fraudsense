import tempfile
import unittest
from pathlib import Path

from fraudsense_core.pipeline import score_file, score_transactions
from fraudsense_core.rules import FLAG_THRESHOLD
from tests.helpers import customer_history, write_transactions


class PipelineTest(unittest.TestCase):
    def test_unusual_transaction_outranks_normal_ones(self):
        history = customer_history("C1", [95, 105, 100, 98, 102, 800])
        scored = {s.transaction.transaction_id: s for s in score_transactions(history)}
        unusual = scored.pop("C1-5")
        self.assertGreater(unusual.score, FLAG_THRESHOLD)
        for normal in scored.values():
            self.assertGreater(unusual.score, normal.score)

    def test_score_file_reads_and_scores_in_file_order(self):
        history = customer_history("C1", [100, 100, 100, 800])
        with tempfile.TemporaryDirectory() as d:
            path = write_transactions(Path(d) / "in.csv", history)
            scored, skipped = score_file(path)
        self.assertEqual([s.transaction.transaction_id for s in scored], ["C1-0", "C1-1", "C1-2", "C1-3"])
        self.assertEqual(skipped, 0)
        self.assertEqual(scored[3].amount_ratio, 8)


if __name__ == "__main__":
    unittest.main()
