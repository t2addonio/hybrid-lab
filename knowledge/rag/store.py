"""Lightweight document store for the shared Knowledge RAG."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

TOKEN_RE = re.compile(r"[a-z0-9_./+-]+", re.IGNORECASE)


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if len(t) > 1]


class DocumentStore:
    def __init__(self):
        self.docs: Dict[str, Dict[str, Any]] = {}
        self.inverted: Dict[str, set] = defaultdict(set)

    def clear(self) -> None:
        self.docs.clear()
        self.inverted.clear()

    def add(self, doc: Dict[str, Any]) -> None:
        doc_id = doc["id"]
        self.docs[doc_id] = doc
        tokens = set(tokenize(doc.get("text", "") + " " + doc.get("rel_path", "")))
        for t in tokens:
            self.inverted[t].add(doc_id)

    def add_many(self, docs: Sequence[Dict[str, Any]]) -> int:
        for d in docs:
            self.add(d)
        return len(docs)

    def search(self, query: str, domain: Optional[str] = None, k: int = 6) -> List[Dict[str, Any]]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        scores: Dict[str, float] = defaultdict(float)
        for t in q_tokens:
            for doc_id in self.inverted.get(t, ()):
                scores[doc_id] += 1.0
        for doc_id, doc in self.docs.items():
            path_l = (doc.get("rel_path") or "").lower()
            if any(tok in path_l for tok in q_tokens):
                scores[doc_id] += 1.5
            if domain and doc.get("domain") != domain:
                scores[doc_id] *= 0.35
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        results = []
        for doc_id, score in ranked:
            if score <= 0:
                continue
            doc = dict(self.docs[doc_id])
            doc["score"] = round(score, 3)
            doc.pop("text", None)
            results.append(doc)
        return results

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for doc in self.docs.values():
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    def load(self, path: str | Path) -> int:
        path = Path(path)
        if not path.exists():
            return 0
        self.clear()
        count = 0
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    self.add(json.loads(line))
                    count += 1
                except json.JSONDecodeError:
                    continue
        return count


_default_store: Optional[DocumentStore] = None


def get_store() -> DocumentStore:
    global _default_store
    if _default_store is None:
        _default_store = DocumentStore()
    return _default_store
