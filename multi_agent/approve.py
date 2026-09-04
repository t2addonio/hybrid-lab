#!/usr/bin/env python3
"""Minimal approval CLI.

  python approve.py list
  python approve.py show <id>
  python approve.py execute <id>
  python approve.py deny <id> [comment]
  python approve.py audit [n]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.gate import Gate
from core.audit import get_auditor
from core.llm import load_config


def main() -> None:
    load_config()
    parser = argparse.ArgumentParser(description="Approve / deny gated tool calls")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Show pending calls")
    p_show = sub.add_parser("show", help="Show one call")
    p_show.add_argument("id")
    p_exec = sub.add_parser("execute", help="Confirm and run under sandbox")
    p_exec.add_argument("id")
    p_deny = sub.add_parser("deny", help="Reject a call")
    p_deny.add_argument("id")
    p_deny.add_argument("comment", nargs="?", default="")
    p_audit = sub.add_parser("audit", help="Recent audit events")
    p_audit.add_argument("n", nargs="?", type=int, default=15)

    args = parser.parse_args()
    gate = Gate()

    if args.cmd == "list":
        print(gate.format_pending())
    elif args.cmd == "show":
        c = gate.get(args.id)
        if not c:
            print(f"No pending call {args.id}")
            return
        print(f"{c.id}  [{c.sensitivity.value}] {c.tool}")
        print(f"  requester: {c.requester}")
        print(f"  reason:    {c.reason}")
        print(f"  created:   {c.created}")
        for k, v in c.args.items():
            print(f"  {k}: {v}")
    elif args.cmd == "execute":
        res = gate.execute(args.id)
        if res.success:
            print(f"OK  {res.data}")
        else:
            print(f"FAIL  {res.error}")
            if res.data:
                print(f"      {res.data}")
    elif args.cmd == "deny":
        c = gate.deny(args.id, args.comment)
        print("denied" if c else f"No pending call {args.id}")
    elif args.cmd == "audit":
        rows = get_auditor().recent(args.n)
        if not rows:
            print("(audit empty)")
            return
        for row in rows:
            ts = str(row.get("ts", ""))[:19]
            ev = row.get("event", "")
            extra = {k: v for k, v in row.items() if k not in ("ts", "event")}
            print(f"{ts}  {ev:12}  {extra}")


if __name__ == "__main__":
    main()
