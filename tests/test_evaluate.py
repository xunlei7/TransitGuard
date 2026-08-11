import unittest

from transitguard.evaluate import evaluate


class EvaluationTests(unittest.TestCase):
    def test_bundled_evaluation(self):
        metrics = evaluate("data/evaluation.jsonl")
        self.assertEqual(metrics["total"], 6)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["abstention_precision"], 1.0)
        self.assertEqual(metrics["abstention_recall"], 1.0)


if __name__ == "__main__":
    unittest.main()

