"""File scanner and text extractor for the shared Knowledge RAG."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_EXTENSIONS = {
    ".md", ".txt", ".csv", ".json", ".yaml", ".yml",
    ".py", ".log", ".rst", ".toml",
}
MAX_FILE_BYTES = 2_000_000


def _file_id(path: Path) -> str:
    return hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:16]


def extract_text(path: Path, max_bytes: int = MAX_FILE_BYTES) -> Optional[str]:
    try:
        if not path.is_file():
            return None
        size = path.stat().st_size
        if size > max_bytes or size == 0:
            return None
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = path.read_text(encoding=encoding, errors="strict")
                return text.replace("\r\n", "\n").replace("\r", "\n").strip()
            except UnicodeDecodeError:
                continue
        return None
    except (OSError, PermissionError):
        return None


def scan_directory(
    root: str | Path,
    domain: str = "general",
    extensions: Optional[Iterable[str]] = None,
    max_bytes: int = MAX_FILE_BYTES,
    recursive: bool = True,
) -> List[Dict[str, Any]]:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        return []
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in (extensions or DEFAULT_EXTENSIONS)}
    docs: List[Dict[str, Any]] = []
    paths = root.rglob("*") if recursive else root.glob("*")
    for p in paths:
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        text = extract_text(p, max_bytes=max_bytes)
        if text is None:
            continue
        snippet = text[:400].replace("\n", " ").strip()
        if len(text) > 400:
            snippet += "…"
        try:
            st = p.stat()
            docs.append({
                "id": _file_id(p),
                "path": str(p),
                "rel_path": str(p.relative_to(root)),
                "domain": domain,
                "extension": p.suffix.lower(),
                "mtime": st.st_mtime,
                "size": st.st_size,
                "text": text,
                "snippet": snippet,
            })
        except (OSError, ValueError):
            continue
    return docs
