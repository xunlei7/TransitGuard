import unittest
from datetime import datetime, timezone

from transitguard.domain import Alert, FeedSnapshot
from transitguard.fixtures import FixtureSource
from transitguard.pipeline import TransitGuard


class PipelineTests(unittest.TestCase):
    def test_end_to_end_offline(self):
        now = datetime(2026, 8, 11, 14, 0, 30, tzinfo=timezone.utc)
        snapshot = FeedSnapshot(
            "fixture://test",
            datetime(2026, 8, 11, 14, 0, tzinfo=timezone.utc),
            alerts=(Alert("A", "A trains are delayed."),),
        )
        answer = TransitGuard(source=FixtureSource(snapshot)).ask(
            "Is the A train delayed?",
            now=now,
        )
        self.assertFalse(answer.abstained)
        self.assertEqual(answer.reason, "active_service_alert")


if __name__ == "__main__":
    unittest.main()

