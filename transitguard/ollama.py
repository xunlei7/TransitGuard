from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .domain import Intent, ParsedQuestion
from .router import SUBWAY_ROUTES


class OllamaQuestionParser:
    """Use a local model only for constrained parsing, never for transit facts."""

    def __init__(self, *, url: str | None = None, model: str | None = None):
        self.url = url or os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def __call__(self, text: str, *, stop_id: str | None = None) -> ParsedQuestion:
        prompt = (
            "Parse an NYC subway question. Return only JSON with keys intent, route_id, stop_id. "
            "intent must be service_status, next_arrival, or unsupported. "
            "route_id must be one of 1-7, A, C, E, B, D, F, M, G, J, Z, L, N, Q, R, W, or null. "
            "Never answer the transit question.\n\n"
            f"Question: {text}\nJSON:"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0, "num_predict": 80},
        }
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                outer = json.loads(response.read().decode("utf-8"))
            data = json.loads(outer.get("response", "{}"))
        except (OSError, ValueError, TypeError, urllib.error.HTTPError, urllib.error.URLError):
            return ParsedQuestion(text, Intent.UNSUPPORTED, reason="local_parser_unavailable")

        try:
            intent = Intent(str(data.get("intent", "unsupported")))
        except ValueError:
            intent = Intent.UNSUPPORTED
        route_id = str(data.get("route_id") or "").upper() or None
        parsed_stop_id = (stop_id or str(data.get("stop_id") or "")).upper() or None

        if route_id not in SUBWAY_ROUTES:
            route_id = None
        reason = "" if intent is not Intent.UNSUPPORTED else "unsupported_intent"
        return ParsedQuestion(str(text).strip(), intent, route_id, parsed_stop_id, reason)

