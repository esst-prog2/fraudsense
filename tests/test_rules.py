import unittest

from fraudsense_core.rules import (
    AMOUNT_RULE,
    FLAG_THRESHOLD,
    VELOCITY_RULE,
    amount_fires,
    amount_reason,
    amount_subscore,
    format_money,
    score_transaction,
    velocity_fires,
    velocity_reason,
    velocity_subscore,
)
from tests.helpers import txn

RATIOS = [None] + [r / 10 for r in range(0, 151)]  # 0.0x .. 15.0x
COUNTS = list(range(1, 16))


class ThresholdTest(unittest.TestCase):
    def test_amount_at_threshold_fires(self):
        self.assertTrue(amount_fires(500 / 100))

    def test_amount_below_threshold_does_not_fire(self):
        self.assertFalse(amount_fires(490 / 100))

    def test_amount_not_evaluated_does_not_fire(self):
        self.assertFalse(amount_fires(None))
        self.assertEqual(amount_subscore(None), 0.0)

    def test_velocity_threshold(self):
        self.assertFalse(velocity_fires(4))
        self.assertTrue(velocity_fires(5))


class ScoreTest(unittest.TestCase):
    def test_score_above_flag_threshold_iff_a_rule_fires(self):
        for ratio in RATIOS:
            for count in COUNTS:
                s = score_transaction(txn("T1", amount=100), 100, ratio, count)
                with self.subTest(ratio=ratio, count=count):
                    self.assertTrue(0.0 <= s.score <= 1.0)
                    self.assertEqual(s.score > FLAG_THRESHOLD, bool(s.fired))

    def test_subscores_never_decrease(self):
        ratios = RATIOS[1:]
        amount_scores = [amount_subscore(r) for r in ratios]
        velocity_scores = [velocity_subscore(c) for c in COUNTS]
        self.assertEqual(amount_scores, sorted(amount_scores))
        self.assertEqual(velocity_scores, sorted(velocity_scores))

    def test_subscore_anchor_points(self):
        self.assertEqual(amount_subscore(1.0), 0.0)
        self.assertAlmostEqual(amount_subscore(5.0), 0.80)
        self.assertAlmostEqual(amount_subscore(10.0), 1.00)
        self.assertAlmostEqual(amount_subscore(40.0), 1.00)
        self.assertEqual(velocity_subscore(1), 0.0)
        self.assertAlmostEqual(velocity_subscore(4), 0.5625)
        self.assertAlmostEqual(velocity_subscore(5), 0.80)
        self.assertAlmostEqual(velocity_subscore(10), 1.00)

    def test_score_is_the_stronger_rule(self):
        s = score_transaction(txn("T1", amount=800), 100, 8.0, 5)
        self.assertAlmostEqual(s.score, amount_subscore(8.0))

    def test_no_rule_fires(self):
        s = score_transaction(txn("T1", amount=120), 100, 1.2, 2)
        self.assertEqual(s.fired, ())
        self.assertEqual(s.reasons, ())
        self.assertLessEqual(s.score, FLAG_THRESHOLD)


class ReasonTest(unittest.TestCase):
    def test_money_format(self):
        self.assertEqual(format_money(4200), "$4,200")
        self.assertEqual(format_money(4200.5), "$4,200.50")
        self.assertEqual(format_money(12.004), "$12")

    def test_amount_reason_text(self):
        self.assertEqual(
            amount_reason(4200, 525, 8.0),
            "amount $4,200 is 8.0x this customer's average ($525)",
        )

    def test_amount_reason_rounds_the_average(self):
        self.assertEqual(
            amount_reason(4200, 524.8, 8.003),
            "amount $4,200 is 8.0x this customer's average ($525)",
        )

    def test_velocity_reason_text(self):
        self.assertEqual(velocity_reason(6), "6 transactions in the last 10 minutes (rule fires at 5)")

    def test_both_rules_fire(self):
        s = score_transaction(txn("T1", amount=4200), 525, 8.0, 6)
        self.assertEqual(s.fired, (AMOUNT_RULE, VELOCITY_RULE))
        self.assertEqual(
            s.reasons,
            (
                "amount $4,200 is 8.0x this customer's average ($525)",
                "6 transactions in the last 10 minutes (rule fires at 5)",
            ),
        )


if __name__ == "__main__":
    unittest.main()
