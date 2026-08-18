# CLI 是 Command-Line Interface，也就是命令行界面

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .evaluate import evaluate
from .fixtures import FixtureSource, load_snapshot
from .ollama import OllamaQuestionParser
from .pipeline import TransitGuard


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="transitguard", description="Evidence-gated NYC subway QA")
    commands = parser.add_subparsers(dest="command", required=True)

    ask = commands.add_parser("ask", help="Ask a service-status or next-arrival question")
    ask.add_argument("question")
    ask.add_argument("--stop-id", help="MTA GTFS stop ID, including N/S suffix when applicable")
    ask.add_argument("--fixture", type=Path, help="Use an offline evidence snapshot")
    ask.add_argument("--now", help="Override current time with an ISO-8601 timestamp")
    ask.add_argument(
        "--ollama-parser",
        action="store_true",
        help="Use a local Ollama model for constrained intent/entity parsing",
    )

    run_eval = commands.add_parser("evaluate", help="Run the bundled deterministic evaluation")
    run_eval.add_argument("path", nargs="?", default="data/evaluation.jsonl")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "evaluate":
        print(json.dumps(evaluate(args.path), indent=2))
        return

    source = FixtureSource(load_snapshot(args.fixture)) if args.fixture else None
    parser = OllamaQuestionParser() if args.ollama_parser else None
    app = TransitGuard(source=source, **({"parser": parser} if parser else {}))
    now = datetime.fromisoformat(args.now) if args.now else None
    print(json.dumps(app.ask(args.question, stop_id=args.stop_id, now=now).as_dict(), indent=2))
