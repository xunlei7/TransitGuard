from __future__ import annotations

import urllib.error
import urllib.request
from datetime import datetime, timezone

from .cache import FeedCache
from .domain import Alert, Arrival, FeedSnapshot, Intent, ParsedQuestion


BASE_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds"
ALERTS_URL = f"{BASE_URL}/camsys%2Fall-alerts"
ROUTE_FEEDS = {
    **{route: f"{BASE_URL}/nyct%2Fgtfs" for route in "1234567"},
    **{route: f"{BASE_URL}/nyct%2Fgtfs-ace" for route in "ACE"},
    **{route: f"{BASE_URL}/nyct%2Fgtfs-bdfm" for route in "BDFM"},
    "G": f"{BASE_URL}/nyct%2Fgtfs-g",
    **{route: f"{BASE_URL}/nyct%2Fgtfs-jz" for route in "JZ"},
    "L": f"{BASE_URL}/nyct%2Fgtfs-l",
    **{route: f"{BASE_URL}/nyct%2Fgtfs-nqrw" for route in "NQRW"},
}


class MTAError(RuntimeError):
    pass


def _translated_text(value: object) -> str:
    translations = getattr(value, "translation", ())
    if not translations:
        return ""
    english = next((item for item in translations if getattr(item, "language", "") == "en"), None)
    return getattr(english or translations[0], "text", "")


class MTAClient:
    def __init__(self, *, cache: FeedCache | None = None, timeout_seconds: int = 10):
        self.cache = cache or FeedCache()
        self.timeout_seconds = timeout_seconds

    def snapshot_for(self, question: ParsedQuestion) -> FeedSnapshot:
        if question.intent is Intent.SERVICE_STATUS:
            return self._parse(self._fetch(ALERTS_URL), ALERTS_URL)
        if not question.route_id or question.route_id not in ROUTE_FEEDS:
            raise MTAError("No MTA feed is configured for this route.")
        url = ROUTE_FEEDS[question.route_id]
        return self._parse(self._fetch(url), url)

    def _fetch(self, url: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": "TransitGuard/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            cached = self.cache.get(url)
            if cached:
                return cached.payload
            raise MTAError(f"Could not retrieve MTA evidence: {exc}") from exc
        self.cache.put(url, payload)
        return payload

    @staticmethod
    def _parse(payload: bytes, source: str) -> FeedSnapshot:
        try:
            from google.transit import gtfs_realtime_pb2
        except ImportError as exc:
            raise MTAError("Install the project dependencies before using live MTA feeds.") from exc

        feed = gtfs_realtime_pb2.FeedMessage()
        try:
            feed.ParseFromString(payload)
        except Exception as exc:
            raise MTAError("The MTA response was not valid GTFS-Realtime data.") from exc

        timestamp = int(getattr(feed.header, "timestamp", 0))
        observed_at = datetime.fromtimestamp(timestamp, timezone.utc) if timestamp else datetime.now(timezone.utc)
        alerts: list[Alert] = []
        arrivals: list[Arrival] = []

        for entity in feed.entity:
            if entity.HasField("alert"):
                route_ids = {
                    item.route_id for item in entity.alert.informed_entity if item.route_id
                } or {"*"}
                header = _translated_text(entity.alert.header_text)
                description = _translated_text(entity.alert.description_text)
                alerts.extend(Alert(route_id, header, description) for route_id in route_ids)

            if entity.HasField("trip_update"):
                trip = entity.trip_update.trip
                route_id = trip.route_id
                for update in entity.trip_update.stop_time_update:
                    epoch = update.arrival.time or update.departure.time
                    if route_id and update.stop_id and epoch:
                        arrivals.append(
                            Arrival(
                                route_id=route_id,
                                stop_id=update.stop_id,
                                arrival_time=datetime.fromtimestamp(epoch, timezone.utc),
                                trip_id=trip.trip_id,
                            )
                        )

        return FeedSnapshot(source, observed_at, tuple(alerts), tuple(arrivals))

