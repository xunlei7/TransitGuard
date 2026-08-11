from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Intent(str, Enum):
    SERVICE_STATUS = "service_status"
    NEXT_ARRIVAL = "next_arrival"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParsedQuestion:
    raw: str
    intent: Intent
    route_id: str | None = None
    stop_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class Alert:
    route_id: str
    header: str
    description: str = ""


@dataclass(frozen=True)
class Arrival:
    route_id: str
    stop_id: str
    arrival_time: datetime
    trip_id: str = ""


@dataclass(frozen=True)
class FeedSnapshot:
    source: str
    observed_at: datetime
    alerts: tuple[Alert, ...] = field(default_factory=tuple)
    arrivals: tuple[Arrival, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Answer:
    text: str
    abstained: bool
    reason: str
    source: str | None = None
    observed_at: datetime | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "answer": self.text,
            "abstained": self.abstained,
            "reason": self.reason,
            "source": self.source,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
        }

