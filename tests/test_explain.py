import unittest

from fraudsense_core.explain import ExplainError, find_transaction, format_explanation
from fraudsense_core.pipeline import score_transactions
from fraudsense_core.rules import score_transaction
from tests.helpers import customer_history, txn


class ExplainTest(unittest.TestCase):
    def test_flagged_transaction_lists_fired_rules(self):
        s = score_transaction(txn("T00231", amount=4200), 525, 8.0, 6)
        self.assertEqual(
            format_explanation(s),
            "Transaction T00231 - risk score 0.92\n"
            "  amount $4,200 is 8.0x this customer's average ($525)\n"
            "  6 transactions in the last 10 minutes (rule fires at 5)",
        )

    def test_normal_transaction_shows_values_against_thresholds(self):
        s = score_transaction(txn("T5", amount=120), 100, 1.2, 2)
        self.assertEqual(
            format_explanation(s),
            "Transaction T5 - risk score 0.19\n"
            "  no rule fired\n"
            "  amount $120 is 1.2x this customer's average ($100) (rule fires at 5x)\n"
            "  2 transactions in the last 10 minutes (rule fires at 5)",
        )

    def test_amount_rule_not_evaluated(self):
        scored = score_transactions(customer_history("C1", [50, 5000]))
        text = format_explanation(scored[1])
        self.assertIn("no rule fired", text)
        self.assertIn("amount rule not evaluated", text)
        self.assertIn("1 transactions in the last 10 minutes", text)

    def test_find_transaction(self):
        scored = score_transactions(customer_history("C1", [10, 20]))
        self.assertEqual(find_transaction(scored, "C1-1").transaction.amount, 20)

    def test_unknown_id_is_named(self):
        scored = score_transactions(customer_history("C1", [10, 20]))
        with self.assertRaises(ExplainError) as ctx:
            find_transaction(scored, "T99999")
        self.assertIn("T99999", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
