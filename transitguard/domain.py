from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 系统里的数据分别长什么样，各模块之间应该传递什么对象

# 它限定系统目前只理解三种情况：
    # 查询线路状态
    # 查询下一班车
    # 不支持的问题

class Intent(str, Enum):
    SERVICE_STATUS = "service_status"
    NEXT_ARRIVAL = "next_arrival"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParsedQuestion:
    # raw：源数据
    raw: str
    intent: Intent
    route_id: str | None = None
    stop_id: str | None = None
    reason: str = ""

# frozen=True：让对象变成不可变对象（类似只读）
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

# 一次 MTA 查询的证据包
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

