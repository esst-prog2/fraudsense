import os
import unittest

from fraudsense_core.pipeline import score_file

PLANTED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "planted.csv")


class TestPlantedScores(unittest.TestCase):
    def test_planted_transaction_is_high_risk_and_scores_highest(self):
        scored, _ = score_file(PLANTED)
        scores = {s.transaction.transaction_id: s.score for s in scored}

        planted = scores.pop("T9001")
        self.assertGreater(planted, 0.75)
        for transaction_id, score in scores.items():
            self.assertGreater(planted, score, transaction_id)


if __name__ == "__main__":
    unittest.main()
