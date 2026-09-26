import unittest
from datetime import datetime

from fraudsense_core.models import ScoredTransaction, Transaction


class ModelsTest(unittest.TestCase):
    def test_build_transaction_and_scored_transaction(self):
        txn = Transaction("T1", "C1", 42.5, datetime(2026, 9, 1, 12, 0))
        scored = ScoredTransaction(
            transaction=txn,
            average_spend=40.0,
            amount_ratio=1.0625,
            window_count=1,
            fired=(),
            reasons=(),
            score=0.01,
        )
        self.assertEqual(scored.transaction.transaction_id, "T1")
        self.assertEqual(scored.window_count, 1)

    def test_transactions_are_immutable(self):
        txn = Transaction("T1", "C1", 42.5, datetime(2026, 9, 1, 12, 0))
        with self.assertRaises(AttributeError):
            txn.amount = 1.0


if __name__ == "__main__":
    unittest.main()
