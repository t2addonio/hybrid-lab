#!/usr/bin/env python3
"""Research & Engineering Multi-Agent System — REPL + one-shot entry."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.llm import load_config
from core.registry import Registry
from core.coordinator import Coordinator
from core.gate import Gate
from core.tools import write_file_call, research_note_call


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Research & Engineering Multi-Agent System")
    parser.add_argument("query", nargs="?", help="Single-shot query (omit for interactive)")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    setup_logging(args.verbose)
    cfg = load_config(args.config)
    print(f"Loaded: {cfg['system']['name']} v{cfg['system']['version']}")
    print(f"Local-first: {cfg['system']['local_first']} | Grok enabled: {cfg['backends']['grok']['enabled']}")

    registry = Registry.load_default()
    print(f"Specialists: {', '.join(registry.list_names())}")

    gate = Gate()
    n = len(gate.list_pending())
    if n:
        print(f"Pending tool calls: {n}  →  python approve.py list")
    print("-" * 60)

    coord = Coordinator(registry, gate=gate)

    if args.query:
        answer = coord.run(args.query)
        print("\n=== FINAL ANSWER ===\n")
        print(answer)
        return

    print("Interactive mode. Type 'quit' or Ctrl-D to exit.")
    print("Extra commands: reset | pending | propose-write <path> | propose-note <text>")
    print("Approval:       python approve.py execute <id>   (or deny <id>)\n")

    while True:
        try:
            user = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user:
            continue
        if user.lower() in {"quit", "exit", "q"}:
            break
        if user.lower() == "reset":
            coord.reset()
            print("(history cleared)")
            continue
        if user.lower() == "pending":
            print(coord.gate.format_pending())
            continue
        if user.lower().startswith("propose-write "):
            path = user.split(maxsplit=1)[1].strip()
            print("content (end with empty line):")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line == "":
                    break
                lines.append(line)
            body = "\n".join(lines)
            call = write_file_call(path, body, requester="coordinator", reason="manual REPL proposal")
            coord.propose(call)
            print(f"proposed {call.id} → {path}")
            print(coord.gate.format_pending())
            continue
        if user.lower().startswith("propose-note "):
            text = user.split(maxsplit=1)[1].strip()
            call = research_note_call(text, requester="coordinator", reason="manual REPL note")
            coord.propose(call)
            print(f"proposed {call.id}")
            print(coord.gate.format_pending())
            continue
        answer = coord.run(user)
        print("\n=== FINAL ANSWER ===\n")
        print(answer)
        print()


if __name__ == "__main__":
    main()
