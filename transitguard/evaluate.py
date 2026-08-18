# 使用 evaluation.jsonl 中的固定案例，检查系统是否在应该回答时回答、在应该拒答时拒答。
# 它不访问实时 MTA，因此结果可复现

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .domain import Alert, Arrival, FeedSnapshot
from .gate import EvidenceGate
from .router import parse_question


def _snapshot(data: dict[str, object]) -> FeedSnapshot:
    return FeedSnapshot(
        source=str(data["source"]),
        observed_at=datetime.fromisoformat(str(data["observed_at"])),
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


def evaluate(path: str | Path) -> dict[str, float | int]:
    gate = EvidenceGate()
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    correct = 0
    correct_abstentions = 0
    expected_abstentions = 0
    actual_abstentions = 0

    for case in cases:
        parsed = parse_question(case["question"], stop_id=case.get("stop_id"))
        answer = gate.evaluate(parsed, _snapshot(case["snapshot"]), now=datetime.fromisoformat(case["now"]))
        expected_abstain = bool(case["expected_abstained"])
        expected_abstentions += int(expected_abstain)
        actual_abstentions += int(answer.abstained)
        correct_abstentions += int(answer.abstained and expected_abstain)
        if answer.abstained == expected_abstain and case["expected_contains"].lower() in answer.text.lower():
            correct += 1

    total = len(cases)
    return {
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "abstention_precision": correct_abstentions / actual_abstentions if actual_abstentions else 0.0,
        "abstention_recall": correct_abstentions / expected_abstentions if expected_abstentions else 0.0,
    }

