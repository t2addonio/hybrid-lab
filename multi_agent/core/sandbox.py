"""Path and resource sandbox for the Tool Layer.

All write / execute paths are validated against roots declared in config.yaml.
Offline-first: pure local filesystem checks, no network.
"""
from __future__ import annotations

import os
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

        # Writes are far narrower than reads: only these roots (relative to
        # multi_agent/), and never the deny-listed guardrail files.
        self.base = base
        self.write_roots: List[Path] = []
        for r in sandbox_cfg.get("write_roots", ["workspace", "proposals"]):
            p = Path(r)
            p = (p if p.is_absolute() else base / p).resolve()
            p.mkdir(parents=True, exist_ok=True)
            self.write_roots.append(p)
        self.write_deny: List[Path] = [
            (base / d).resolve()
            for d in sandbox_cfg.get("write_deny", ["core", "config.yaml", "approve.py"])
        ]

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

    def resolve_write(self, path: Union[str, Path]) -> Path:
        """Resolve a write target; must sit under a write root and off the deny-list.

        Relative paths are anchored at multi_agent/ (not the process CWD).
        Symlinks are resolved, and any symlink component inside the write root
        (including the target itself) is refused, so links cannot redirect writes.
        """
        p = Path(path).expanduser()
        if ".." in p.parts:
            raise SandboxError(f"Path traversal blocked: {path}")
        if not p.is_absolute():
            p = self.base / p
        p = Path(os.path.abspath(p))
        try:
            resolved = p.resolve()
        except Exception as e:
            raise SandboxError(f"Cannot resolve path {path}: {e}") from e

        for deny in self.write_deny:
            for cand in (p, resolved):
                if cand == deny or deny in cand.parents:
                    raise SandboxError(f"Write to protected path blocked: {cand}")

        for root in self.write_roots:
            if resolved == root or root not in resolved.parents:
                continue
            # The lexical path must also live under the root, with no symlinks
            # between the root and the target.
            if p != resolved:
                raise SandboxError(f"Symlink in write path blocked: {path}")
            return resolved
        raise SandboxError(
            f"Write outside write roots: {resolved}\nAllowed: {[str(r) for r in self.write_roots]}"
        )

    def check_write(self, path: Union[str, Path], content: str) -> Path:
        safe = self.resolve_write(path)
        if len(content.encode("utf-8")) > self.max_write_bytes:
            raise SandboxError(
                f"Content exceeds max_write_bytes ({self.max_write_bytes})"
            )
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
