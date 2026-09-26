import unittest

from fraudsense_core.features import amount_ratio, average_spend, window_counts
from tests.helpers import customer_history, txn


class AverageSpendTest(unittest.TestCase):
    def test_transaction_is_excluded_from_its_own_average(self):
        history = customer_history("C1", [100, 100, 100, 800])
        averages = average_spend(history)
        big = history[3]
        self.assertEqual(averages[big.transaction_id], 100)
        self.assertEqual(amount_ratio(big.amount, averages[big.transaction_id]), 8)

    def test_customer_with_two_transactions_is_not_evaluated(self):
        history = customer_history("C1", [50, 5000])
        averages = average_spend(history)
        self.assertEqual(set(averages.values()), {None})
        self.assertIsNone(amount_ratio(5000, None))

    def test_exactly_three_other_transactions_is_enough(self):
        history = customer_history("C1", [100, 100, 100, 100])
        self.assertEqual(average_spend(history)[history[0].transaction_id], 100)

    def test_customers_do_not_mix(self):
        history = customer_history("C1", [100] * 4) + customer_history("C2", [10] * 4)
        averages = average_spend(history)
        self.assertEqual(averages["C1-0"], 100)
        self.assertEqual(averages["C2-0"], 10)

    def test_zero_average_is_not_evaluated(self):
        history = customer_history("C1", [0, 0, 0, 50])
        self.assertIsNone(average_spend(history)["C1-3"])


class WindowCountsTest(unittest.TestCase):
    def test_burst_of_six_within_eight_minutes(self):
        burst = [txn(f"T{i}", minutes=m) for i, m in enumerate([0, 1, 3, 5, 6, 8])]
        counts = window_counts(burst)
        self.assertEqual([counts[t.transaction_id] for t in burst], [1, 2, 3, 4, 5, 6])

    def test_transactions_fifteen_minutes_apart(self):
        spread = [txn(f"T{i}", minutes=15 * i) for i in range(6)]
        counts = window_counts(spread)
        self.assertEqual(set(counts.values()), {1})

    def test_window_includes_its_start_boundary(self):
        pair = [txn("T0", minutes=0), txn("T1", minutes=10)]
        self.assertEqual(window_counts(pair)["T1"], 2)

    def test_same_timestamp_ties_all_count(self):
        ties = [txn(f"T{i}", minutes=0) for i in range(3)]
        self.assertEqual(set(window_counts(ties).values()), {3})

    def test_file_order_does_not_matter(self):
        burst = [txn(f"T{i}", minutes=m) for i, m in enumerate([8, 0, 5, 1, 6, 3])]
        counts = window_counts(burst)
        self.assertEqual(counts["T0"], 6)
        self.assertEqual(counts["T1"], 1)

    def test_other_customers_are_not_counted(self):
        mixed = [txn(f"T{i}", customer_id=f"C{i}", minutes=0) for i in range(6)]
        self.assertEqual(set(window_counts(mixed).values()), {1})


if __name__ == "__main__":
    unittest.main()
