import unittest
from datetime import datetime, timedelta, timezone

from transitguard.domain import Alert, Arrival, FeedSnapshot, Intent, ParsedQuestion
from transitguard.gate import EvidenceGate


NOW = datetime(2026, 8, 11, 14, 0, tzinfo=timezone.utc)


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = EvidenceGate(max_feed_age_seconds=90)

    def test_abstains_on_stale_feed(self):
        question = ParsedQuestion("Is the A train delayed?", Intent.SERVICE_STATUS, "A")
        snapshot = FeedSnapshot("fixture", NOW - timedelta(minutes=3))
        answer = self.gate.evaluate(question, snapshot, now=NOW)
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.reason, "stale_evidence")

    def test_returns_relevant_alert(self):
        question = ParsedQuestion("Is the A train delayed?", Intent.SERVICE_STATUS, "A")
        snapshot = FeedSnapshot(
            "fixture",
            NOW - timedelta(seconds=20),
            alerts=(Alert("A", "A trains are delayed."), Alert("L", "L trains are suspended.")),
        )
        answer = self.gate.evaluate(question, snapshot, now=NOW)
        self.assertFalse(answer.abstained)
        self.assertEqual(answer.text, "A trains are delayed.")

    def test_returns_next_matching_arrival(self):
        question = ParsedQuestion("When is the next 7 train?", Intent.NEXT_ARRIVAL, "7", "725N")
        snapshot = FeedSnapshot(
            "fixture",
            NOW - timedelta(seconds=15),
            arrivals=(
                Arrival("7", "725S", NOW + timedelta(minutes=2)),
                Arrival("7", "725N", NOW + timedelta(minutes=6)),
            ),
        )
        answer = self.gate.evaluate(question, snapshot, now=NOW)
        self.assertFalse(answer.abstained)
        self.assertIn("6 minutes", answer.text)

    def test_abstains_without_stop_id(self):
        question = ParsedQuestion("When is the next 7 train?", Intent.NEXT_ARRIVAL, "7")
        answer = self.gate.evaluate(question, None, now=NOW)
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.reason, "missing_stop_id")


if __name__ == "__main__":
    unittest.main()

