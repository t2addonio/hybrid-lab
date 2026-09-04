"""Minimal gated tool interface.

Only this module is allowed to perform side-effects.
Propose → human confirms → execute under sandbox.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .audit import get_auditor
from .sandbox import SandboxError, get_sandbox

PENDING_PATH = Path(__file__).resolve().parent.parent / "pending.json"


class Sensitivity(str, Enum):
    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"
    DESTRUCTIVE = "destructive"


@dataclass
class ToolCall:
    tool: str
    args: Dict[str, Any]
    requester: str
    reason: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sensitivity: Sensitivity = Sensitivity.WRITE
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sensitivity"] = self.sensitivity.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ToolCall":
        return cls(
            tool=d["tool"],
            args=d.get("args", {}),
            requester=d.get("requester", "unknown"),
            reason=d.get("reason", ""),
            id=d.get("id", str(uuid.uuid4())[:8]),
            sensitivity=Sensitivity(d.get("sensitivity", "write")),
            created=d.get("created", ""),
        )


@dataclass
class ToolResult:
    call_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None


def _write_file(args: Dict[str, Any]) -> Any:
    path = args["path"]
    content = args.get("content", "")
    safe = get_sandbox().check_write(path, content)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(content, encoding="utf-8")
    return {"path": str(safe), "bytes": len(content.encode("utf-8"))}


def _research_note(args: Dict[str, Any]) -> Any:
    from .state import ResearchState
    text = args.get("text", "")
    tags = args.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    item = ResearchState().add_insight(text, tags=tags)
    return {"insight_id": item["id"]}


def _execute_command(args: Dict[str, Any]) -> Any:
    return {
        "blocked": True,
        "message": "execute_command is proposal-only this phase; run the command manually after review",
        "command": args.get("command"),
    }


def _propose_patch(args: Dict[str, Any]) -> Any:
    import json as _json
    root = Path(__file__).resolve().parent.parent
    proposals_dir = root / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    prop_id = args.get("id") or f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    content = args.get("content", "")
    if not content.strip():
        raise ValueError("propose_patch requires non-empty content")
    if not content.lstrip().startswith("CHANGE_PROPOSAL:") and not content.lstrip().startswith("---"):
        content = f"CHANGE_PROPOSAL:\nid: {prop_id}\n{content}"
    path = proposals_dir / f"{prop_id}.md"
    safe = get_sandbox().check_write(str(path), content)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(content, encoding="utf-8")
    log_path = root / "improvement_log.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "proposal_created",
        "id": prop_id,
        "author": args.get("requester", "architect"),
        "status": "proposed",
        "hybrid": args.get("hybrid_invariant", "unknown"),
        "target": args.get("target", ""),
        "title": args.get("title", ""),
        "path": str(safe.relative_to(root)),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(entry) + "\n")
    return {"proposal_id": prop_id, "path": str(safe), "bytes": len(content.encode("utf-8")), "log_appended": True}


def _retrieve_knowledge(args: Dict[str, Any]) -> Any:
    import sys
    query = (args.get("query") or "").strip()
    if not query:
        raise ValueError("retrieve_knowledge requires a non-empty 'query'")
    domain = args.get("domain")
    if domain is not None:
        domain = str(domain).strip() or None
    k = max(1, min(int(args.get("k") or 6), 20))
    artifacts_root = Path(__file__).resolve().parents[2]
    if str(artifacts_root) not in sys.path:
        sys.path.insert(0, str(artifacts_root))
    from knowledge.rag.retrieve import load_index, retrieve
    n = load_index("default")
    hits = retrieve(query, domain=domain, k=k)
    compact = []
    for h in hits:
        compact.append({
            "score": h.get("score"),
            "domain": h.get("domain"),
            "path": h.get("rel_path") or h.get("path"),
            "snippet": h.get("snippet", "")[:350],
        })
    return {"query": query, "domain": domain, "k": k, "index_docs": n, "hits": compact, "hit_count": len(compact)}


TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "write_file": _write_file,
    "research_note": _research_note,
    "execute_command": _execute_command,
    "propose_patch": _propose_patch,
    "retrieve_knowledge": _retrieve_knowledge,
}

TOOL_SENSITIVITY: Dict[str, Sensitivity] = {
    "write_file": Sensitivity.WRITE,
    "research_note": Sensitivity.WRITE,
    "execute_command": Sensitivity.DESTRUCTIVE,
    "propose_patch": Sensitivity.WRITE,
    "retrieve_knowledge": Sensitivity.READ,
}


class Gate:
    def __init__(self) -> None:
        self.pending: Dict[str, ToolCall] = {}
        self._load()

    def _load(self) -> None:
        if not PENDING_PATH.exists():
            return
        try:
            data = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
            for item in data.get("pending", []):
                call = ToolCall.from_dict(item)
                self.pending[call.id] = call
        except Exception:
            pass

    def _save(self) -> None:
        payload = {
            "pending": [c.to_dict() for c in self.pending.values()],
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        PENDING_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def propose(self, call: ToolCall) -> ToolCall:
        if call.tool in TOOL_SENSITIVITY:
            call.sensitivity = TOOL_SENSITIVITY[call.tool]
        self.pending[call.id] = call
        self._save()
        get_auditor().log(
            "proposed",
            call_id=call.id,
            tool=call.tool,
            requester=call.requester,
            reason=call.reason,
            args_preview={k: str(v)[:80] for k, v in call.args.items()},
        )
        return call

    def list_pending(self) -> List[ToolCall]:
        return list(self.pending.values())

    def get(self, call_id: str) -> Optional[ToolCall]:
        return self.pending.get(call_id)

    def deny(self, call_id: str, comment: str = "") -> Optional[ToolCall]:
        call = self.pending.pop(call_id, None)
        if call:
            self._save()
            get_auditor().log("denied", call_id=call_id, tool=call.tool, comment=comment)
        return call

    def execute(self, call_id: str) -> ToolResult:
        call = self.pending.pop(call_id, None)
        if call is None:
            return ToolResult(call_id=call_id, success=False, error="unknown or already handled call_id")
        self._save()
        handler = TOOL_HANDLERS.get(call.tool)
        if handler is None:
            res = ToolResult(call_id=call_id, success=False, error=f"no handler for tool '{call.tool}'")
            get_auditor().log("failed", call_id=call_id, error=res.error)
            return res
        try:
            data = handler(call.args)
            if isinstance(data, dict) and data.get("blocked"):
                res = ToolResult(call_id=call_id, success=False, error=data.get("message"), data=data)
            else:
                res = ToolResult(call_id=call_id, success=True, data=data)
            get_auditor().log("executed" if res.success else "blocked", call_id=call_id, tool=call.tool, result=data)
            return res
        except SandboxError as e:
            res = ToolResult(call_id=call_id, success=False, error=f"sandbox: {e}")
            get_auditor().log("blocked", call_id=call_id, error=str(e))
            return res
        except Exception as e:
            res = ToolResult(call_id=call_id, success=False, error=str(e))
            get_auditor().log("failed", call_id=call_id, error=str(e))
            return res

    def format_pending(self) -> str:
        if not self.pending:
            return "No pending tool calls."
        lines = ["Pending tool calls (human confirmation required):"]
        for c in self.pending.values():
            lines.append(f"  {c.id}  [{c.sensitivity.value}] {c.tool}")
            lines.append(f"       requester: {c.requester}")
            if c.reason:
                lines.append(f"       reason:    {c.reason}")
            for k, v in c.args.items():
                val = str(v)
                if len(val) > 100:
                    val = val[:97] + "..."
                lines.append(f"       {k}: {val}")
        return "\n".join(lines)
