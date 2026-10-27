"""Run a multi-model deliberation from CLI or a local browser."""

from __future__ import annotations

import argparse
import json
import os

from .engine import Debate
from .llm import OpenAICompatibleLLM
from .web import serve

WEB_ACTIONS = {"debate": [("question", "Question", "textarea", True)]}


def execute(
    action: str, values: dict, *, models: list[str], synthesizer: str
) -> object:
    if action != "debate":
        raise ValueError("unknown action")
    if len(models) < 2:
        raise ValueError("configure at least two debating models")
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY before running a debate")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    agents = {
        f"agent-{index + 1}-{model}": OpenAICompatibleLLM(key, base_url, model)
        for index, model in enumerate(models)
    }
    judge = OpenAICompatibleLLM(key, base_url, synthesizer)
    result = Debate(agents, judge).run(values["question"])
    return result.__dict__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-model debate and synthesis")
    parser.add_argument("--model", dest="models", action="append", required=True)
    parser.add_argument("--synthesizer-model", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    debate = commands.add_parser("debate")
    debate.add_argument("question")
    browser = commands.add_parser("serve")
    browser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(
            "Multi Agent Debate",
            WEB_ACTIONS,
            lambda action, values: execute(
                action, values, models=args.models, synthesizer=args.synthesizer_model
            ),
            port=args.port,
        )
    else:
        print(
            json.dumps(
                execute(
                    args.command,
                    vars(args),
                    models=args.models,
                    synthesizer=args.synthesizer_model,
                ),
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
