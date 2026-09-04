#!/usr/bin/env python3
"""Research memory CLI (state.json)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.state import ResearchState


def main() -> None:
    parser = argparse.ArgumentParser(description="Research memory (state.json)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("list-hypotheses")
    p_ah = sub.add_parser("add-hypothesis")
    p_ah.add_argument("statement")
    p_ah.add_argument("--notes", default="")
    p_ch = sub.add_parser("close-hypothesis")
    p_ch.add_argument("id")
    p_ch.add_argument("--resolution", default="")
    sub.add_parser("list-experiments")
    p_ae = sub.add_parser("add-experiment")
    p_ae.add_argument("title")
    p_ae.add_argument("--hypothesis", default="")
    p_ae.add_argument("--notes", default="")
    sub.add_parser("list-insights")
    p_ai = sub.add_parser("add-insight")
    p_ai.add_argument("text")
    p_ai.add_argument("--tags", default="")
    p_notes = sub.add_parser("notes")
    p_notes.add_argument("text", nargs="?", default=None)
    args = parser.parse_args()
    state = ResearchState()
    if args.cmd == "summary":
        print(state.summary())
        print(f"last_updated: {state.raw().get('last_updated')}")
        if state.raw().get("session_notes"):
            print(f"session_notes: {state.raw()['session_notes']}")
    elif args.cmd == "list-hypotheses":
        items = state.list_hypotheses()
        print("(none)" if not items else "")
        for h in items:
            print(f"{h['id']}  {h['statement']}")
    elif args.cmd == "add-hypothesis":
        item = state.add_hypothesis(args.statement, notes=args.notes)
        print(f"Added {item['id']}: {item['statement']}")
    elif args.cmd == "close-hypothesis":
        ok = state.close_hypothesis(args.id, resolution=args.resolution)
        print("Closed." if ok else f"Hypothesis {args.id} not found in open list.")
    elif args.cmd == "list-experiments":
        items = state.list_experiments()
        print("(none)" if not items else "")
        for e in items:
            print(f"{e['id']}  {e['title']}  (hyp={e.get('hypothesis_id') or '-'})")
    elif args.cmd == "add-experiment":
        item = state.add_experiment(args.title, hypothesis_id=args.hypothesis, notes=args.notes)
        print(f"Added {item['id']}: {item['title']}")
    elif args.cmd == "list-insights":
        items = state.list_insights()
        print("(none)" if not items else "")
        for i in items:
            print(f"{i['id']}  {i['text'][:100]}")
    elif args.cmd == "add-insight":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        item = state.add_insight(args.text, tags=tags)
        print(f"Added {item['id']}")
    elif args.cmd == "notes":
        if args.text is None:
            print(state.raw().get("session_notes") or "(empty)")
        else:
            state.set_notes(args.text)
            print("Session notes updated.")


if __name__ == "__main__":
    main()
