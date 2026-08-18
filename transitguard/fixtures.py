# Fixture 是：为演示或测试准备的固定输入数据。
# data/demo_snapshot.json 不是实时 MTA 数据，而是一份人为保存的 FeedSnapshot 示例

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .domain import Alert, Arrival, FeedSnapshot, ParsedQuestion


class FixtureSource:
    def __init__(self, snapshot: FeedSnapshot):
        self.snapshot = snapshot

    def snapshot_for(self, question: ParsedQuestion) -> FeedSnapshot:
        return self.snapshot


def load_snapshot(path: str | Path) -> FeedSnapshot:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FeedSnapshot(
        source=data["source"],
        observed_at=datetime.fromisoformat(data["observed_at"]),
        alerts=tuple(Alert(**item) for item in data.get("alerts", [])),
        arrivals=tuple(
            Arrival(
                route_id=item["route_id"],
                stop_id=item["stop_id"],
                arrival_time=datetime.fromisoformat(item["arrival_time"]),
                trip_id=item.get("trip_id", ""),
            )
            for item in data.get("arrivals", [])
        ),
    )

