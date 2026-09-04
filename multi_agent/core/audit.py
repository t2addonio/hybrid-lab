"""Append-only JSONL audit log for every ToolRequest / ActionProposal / decision.

Offline-first. Never contains API keys. Survives process restarts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm import get_config


def _default_audit_path() -> Path:
    cfg = get_config()
    audit_cfg = cfg.get("audit", {})
    rel = audit_cfg.get("path", "audit.jsonl")
    base = Path(__file__).resolve().parent.parent
    return (base / rel).resolve()


class Auditor:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or _default_audit_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def log(self, event: str, **payload: Any) -> None:
        """Append one structured event. Failures are silent (never crash the agent)."""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **payload,
        }
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception:
            pass  # audit must never block the main loop

    def recent(self, n: int = 20) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


_AUDITOR: Optional[Auditor] = None


def get_auditor() -> Auditor:
    global _AUDITOR
    if _AUDITOR is None:
        _AUDITOR = Auditor()
    return _AUDITOR
