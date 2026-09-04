"""Public retrieval API for specialists and sibling projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .scanner import scan_directory
from .store import DocumentStore, get_store


def _knowledge_root() -> Path:
    return Path(__file__).resolve().parents[1]  # knowledge/


def index_domain(
    domain: str,
    roots: List[str | Path],
    store: Optional[DocumentStore] = None,
    recursive: bool = True,
) -> int:
    """Scan one or more roots and add documents to the store under the given domain."""
    store = store or get_store()
    total = 0
    for root in roots:
        docs = scan_directory(root, domain=domain, recursive=recursive)
        total += store.add_many(docs)
    return total


def retrieve(
    query: str,
    domain: Optional[str] = None,
    k: int = 6,
    store: Optional[DocumentStore] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant documents.

    Returns list of dicts with keys:
      id, path, rel_path, domain, extension, mtime, size, snippet, score
    """
    store = store or get_store()
    return store.search(query, domain=domain, k=k)


def rebuild_from_domains(domain_roots: Dict[str, List[str | Path]]) -> Dict[str, int]:
    """Convenience: clear store and re-index every domain."""
    store = get_store()
    store.clear()
    counts = {}
    for domain, roots in domain_roots.items():
        counts[domain] = index_domain(domain, roots, store=store)
    return counts


def save_index(name: str = "default") -> Path:
    path = _knowledge_root() / "indexes" / f"{name}.jsonl"
    get_store().save(path)
    return path


def load_index(name: str = "default") -> int:
    path = _knowledge_root() / "indexes" / f"{name}.jsonl"
    return get_store().load(path)
