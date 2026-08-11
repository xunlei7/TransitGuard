import unittest
from datetime import datetime, timezone

from google.transit import gtfs_realtime_pb2

from transitguard.mta import MTAClient


class MTAParserTests(unittest.TestCase):
    def test_parses_alerts_and_arrivals(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        feed.header.timestamp = 1786456800

        alert_entity = feed.entity.add()
        alert_entity.id = "alert-1"
        informed = alert_entity.alert.informed_entity.add()
        informed.route_id = "A"
        translation = alert_entity.alert.header_text.translation.add()
        translation.text = "A trains are delayed."
        translation.language = "en"

        trip_entity = feed.entity.add()
        trip_entity.id = "trip-1"
        trip_entity.trip_update.trip.route_id = "A"
        trip_entity.trip_update.trip.trip_id = "trip-1"
        update = trip_entity.trip_update.stop_time_update.add()
        update.stop_id = "A24N"
        update.arrival.time = 1786457100

        snapshot = MTAClient._parse(feed.SerializeToString(), "fixture://protobuf")
        self.assertEqual(snapshot.observed_at, datetime.fromtimestamp(1786456800, timezone.utc))
        self.assertEqual(snapshot.alerts[0].route_id, "A")
        self.assertEqual(snapshot.arrivals[0].stop_id, "A24N")


if __name__ == "__main__":
    unittest.main()

