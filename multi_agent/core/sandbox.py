"""Path and resource sandbox for the Tool Layer.

All write / execute paths are validated against roots declared in config.yaml.
Offline-first: pure local filesystem checks, no network.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from .llm import get_config


class SandboxError(Exception):
    """Raised when a path or command violates the sandbox policy."""


class Sandbox:
    """Enforces allowed roots and blocks traversal / absolute escapes."""

    def __init__(self, roots: Optional[List[str]] = None) -> None:
        cfg = get_config()
        sandbox_cfg = cfg.get("sandbox", {})
        raw_roots = roots or sandbox_cfg.get("allowed_roots", ["."])
        self.roots: List[Path] = []
        base = Path(__file__).resolve().parent.parent  # multi_agent/
        for r in raw_roots:
            p = Path(r)
            if not p.is_absolute():
                p = (base / p).resolve()
            else:
                p = p.resolve()
            self.roots.append(p)

        self.allow_temp = sandbox_cfg.get("allow_temp", True)
        self.temp_roots = [Path("/tmp").resolve()]
        if self.allow_temp:
            self.roots.extend(self.temp_roots)

        self.max_write_bytes = int(sandbox_cfg.get("max_write_bytes", 2_000_000))

    def resolve(self, path: Union[str, Path]) -> Path:
        """Return a resolved Path that is guaranteed to live under an allowed root."""
        p = Path(path).expanduser()
        if ".." in p.parts:
            raise SandboxError(f"Path traversal blocked: {path}")
        try:
            resolved = p.resolve()
        except Exception as e:
            raise SandboxError(f"Cannot resolve path {path}: {e}") from e

        for root in self.roots:
            try:
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue
        raise SandboxError(
            f"Path outside sandbox roots: {resolved}\nAllowed: {[str(r) for r in self.roots]}"
        )

    def check_write(self, path: Union[str, Path], content: str) -> Path:
        safe = self.resolve(path)
        if len(content.encode("utf-8")) > self.max_write_bytes:
            raise SandboxError(
                f"Content exceeds max_write_bytes ({self.max_write_bytes})"
            )
        parent = safe.parent
        if not parent.exists():
            self.resolve(parent)
        return safe

    def check_read(self, path: Union[str, Path]) -> Path:
        return self.resolve(path)

    def is_allowed(self, path: Union[str, Path]) -> bool:
        try:
            self.resolve(path)
            return True
        except SandboxError:
            return False


_SANDBOX: Optional[Sandbox] = None


def get_sandbox() -> Sandbox:
    global _SANDBOX
    if _SANDBOX is None:
        _SANDBOX = Sandbox()
    return _SANDBOX
