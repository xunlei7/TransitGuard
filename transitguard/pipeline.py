from __future__ import annotations

from datetime import datetime
from typing import Callable, Protocol

from .domain import Answer, FeedSnapshot, ParsedQuestion
from .gate import EvidenceGate
from .mta import MTAClient, MTAError
from .router import parse_question


class EvidenceSource(Protocol):
    def snapshot_for(self, question: ParsedQuestion) -> FeedSnapshot: ...


class TransitGuard:
    def __init__(
        self,
        *,
        source: EvidenceSource | None = None,
        gate: EvidenceGate | None = None,
        parser: Callable[..., ParsedQuestion] = parse_question,
    ):
        self.source = source or MTAClient()
        self.gate = gate or EvidenceGate()
        self.parser = parser

    def ask(
        self,
        question: str,
        *,
        stop_id: str | None = None,
        now: datetime | None = None,
    ) -> Answer:
        parsed = self.parser(question, stop_id=stop_id)
        if parsed.reason:
            return self.gate.evaluate(parsed, None, now=now)
        try:
            snapshot = self.source.snapshot_for(parsed)
        except MTAError:
            return Answer("I don't know.", True, "source_unavailable")
        return self.gate.evaluate(parsed, snapshot, now=now)
