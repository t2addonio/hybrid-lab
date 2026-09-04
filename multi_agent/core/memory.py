"""Simple file-based conversation memory for Phase 0."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "memory.json"

class Memory:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or DEFAULT_PATH
        self._data: Dict = {"history": []}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {"history": []}

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def add_turn(self, user: str, assistant: str) -> None:
        self._data.setdefault("history", []).append({
            "user": user,
            "assistant": assistant,
        })
        self._data["history"] = self._data["history"][-20:]
        self.save()

    def get_history(self) -> List[Dict[str, str]]:
        """Return OpenAI-style message list."""
        messages = []
        for turn in self._data.get("history", []):
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        return messages

    def clear(self) -> None:
        self._data = {"history": []}
        self.save()
