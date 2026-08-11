from __future__ import annotations

from datetime import datetime, timezone

from .domain import Answer, FeedSnapshot, Intent, ParsedQuestion


class EvidenceGate:
    """Turn retrieved evidence into an answer only when it passes explicit checks."""

    def __init__(self, *, max_feed_age_seconds: int = 90, arrival_horizon_minutes: int = 120):
        self.max_feed_age_seconds = max_feed_age_seconds
        self.arrival_horizon_minutes = arrival_horizon_minutes

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def evaluate(
        self,
        question: ParsedQuestion,
        snapshot: FeedSnapshot | None,
        *,
        now: datetime | None = None,
    ) -> Answer:
        now = self._utc(now or datetime.now(timezone.utc))

        if question.intent is Intent.UNSUPPORTED:
            return Answer("I don't know.", True, question.reason or "unsupported_intent")
        if not question.route_id:
            return Answer("I don't know.", True, "missing_route")
        if question.intent is Intent.NEXT_ARRIVAL and not question.stop_id:
            return Answer("I don't know.", True, "missing_stop_id")
        if snapshot is None:
            return Answer("I don't know.", True, "missing_evidence")

        observed_at = self._utc(snapshot.observed_at)
        age_seconds = (now - observed_at).total_seconds()
        if age_seconds < -30:
            return Answer("I don't know.", True, "future_feed_timestamp", snapshot.source, observed_at)
        if age_seconds > self.max_feed_age_seconds:
            return Answer("I don't know.", True, "stale_evidence", snapshot.source, observed_at)

        if question.intent is Intent.SERVICE_STATUS:
            return self._status_answer(question, snapshot, observed_at)
        return self._arrival_answer(question, snapshot, now, observed_at)

    @staticmethod
    def _status_answer(
        question: ParsedQuestion,
        snapshot: FeedSnapshot,
        observed_at: datetime,
    ) -> Answer:
        relevant = [
            alert for alert in snapshot.alerts
            if alert.route_id in {question.route_id, "*"}
        ]
        if not relevant:
            text = f"No active MTA service alerts for the {question.route_id} train."
            return Answer(text, False, "fresh_feed_no_active_alerts", snapshot.source, observed_at)

        summaries = []
        for alert in relevant[:3]:
            summary = " ".join(alert.header.split())
            if summary and summary not in summaries:
                summaries.append(summary)
        if not summaries:
            return Answer("I don't know.", True, "alert_missing_description", snapshot.source, observed_at)
        return Answer(" ".join(summaries), False, "active_service_alert", snapshot.source, observed_at)

    def _arrival_answer(
        self,
        question: ParsedQuestion,
        snapshot: FeedSnapshot,
        now: datetime,
        observed_at: datetime,
    ) -> Answer:
        arrivals = sorted(
            (
                arrival for arrival in snapshot.arrivals
                if arrival.route_id == question.route_id
                and arrival.stop_id == question.stop_id
                and self._utc(arrival.arrival_time) >= now
            ),
            key=lambda arrival: arrival.arrival_time,
        )
        horizon_seconds = self.arrival_horizon_minutes * 60
        arrivals = [
            arrival for arrival in arrivals
            if (self._utc(arrival.arrival_time) - now).total_seconds() <= horizon_seconds
        ]
        if not arrivals:
            return Answer("I don't know.", True, "no_matching_arrival", snapshot.source, observed_at)

        minutes = max(0, round((self._utc(arrivals[0].arrival_time) - now).total_seconds() / 60))
        text = f"The next {question.route_id} train at stop {question.stop_id} is due in about {minutes} minutes."
        return Answer(text, False, "fresh_matching_arrival", snapshot.source, observed_at)

