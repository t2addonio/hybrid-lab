"""Research memory state (state.json) — offline-first, schema v1.0."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "state.json"

SCHEMA = {
    "schema_version": "1.0",
    "last_updated": "",
    "project": "Research & Engineering Multi-Agent System",
    "session_notes": "",
    "open_hypotheses": [],
    "active_experiments": [],
    "closed_archive": {"hypotheses": [], "experiments": []},
    "key_insights": [],
    "meta": {"next_hypothesis_id": 1, "next_experiment_id": 1, "next_insight_id": 1},
}


class ResearchState:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or DEFAULT_PATH
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = json.loads(json.dumps(SCHEMA))
        else:
            self._data = json.loads(json.dumps(SCHEMA))
            self._save()

    def _save(self) -> None:
        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def add_hypothesis(self, statement: str, notes: str = "") -> Dict[str, Any]:
        meta = self._data.setdefault("meta", {})
        hid = meta.get("next_hypothesis_id", 1)
        item = {
            "id": f"H{hid:03d}",
            "statement": statement,
            "notes": notes,
            "status": "open",
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._data.setdefault("open_hypotheses", []).append(item)
        meta["next_hypothesis_id"] = hid + 1
        self._save()
        return item

    def list_hypotheses(self, status: str = "open") -> List[Dict[str, Any]]:
        if status == "open":
            return list(self._data.get("open_hypotheses", []))
        return list(self._data.get("closed_archive", {}).get("hypotheses", []))

    def close_hypothesis(self, hid: str, resolution: str = "") -> bool:
        open_list = self._data.get("open_hypotheses", [])
        for i, h in enumerate(open_list):
            if h["id"] == hid:
                h["status"] = "closed"
                h["resolution"] = resolution
                h["closed"] = datetime.now(timezone.utc).isoformat()
                closed = open_list.pop(i)
                self._data.setdefault("closed_archive", {}).setdefault("hypotheses", []).append(closed)
                self._save()
                return True
        return False

    def add_experiment(self, title: str, hypothesis_id: str = "", notes: str = "") -> Dict[str, Any]:
        meta = self._data.setdefault("meta", {})
        eid = meta.get("next_experiment_id", 1)
        item = {
            "id": f"E{eid:03d}",
            "title": title,
            "hypothesis_id": hypothesis_id,
            "notes": notes,
            "status": "active",
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._data.setdefault("active_experiments", []).append(item)
        meta["next_experiment_id"] = eid + 1
        self._save()
        return item

    def list_experiments(self, status: str = "active") -> List[Dict[str, Any]]:
        if status == "active":
            return list(self._data.get("active_experiments", []))
        return list(self._data.get("closed_archive", {}).get("experiments", []))

    def add_insight(self, text: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        meta = self._data.setdefault("meta", {})
        iid = meta.get("next_insight_id", 1)
        item = {
            "id": f"I{iid:03d}",
            "text": text,
            "tags": tags or [],
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._data.setdefault("key_insights", []).append(item)
        meta["next_insight_id"] = iid + 1
        self._save()
        return item

    def list_insights(self) -> List[Dict[str, Any]]:
        return list(self._data.get("key_insights", []))

    def set_notes(self, notes: str) -> None:
        self._data["session_notes"] = notes
        self._save()

    def summary(self) -> str:
        oh = len(self._data.get("open_hypotheses", []))
        ae = len(self._data.get("active_experiments", []))
        ki = len(self._data.get("key_insights", []))
        return f"Research memory — open hypotheses: {oh}, active experiments: {ae}, key insights: {ki}"

    def raw(self) -> Dict[str, Any]:
        return self._data
