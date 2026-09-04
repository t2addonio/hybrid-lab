"""Thin tool helpers + grant table.

Specialists never call handlers directly. They create ToolCall objects
(or the Coordinator creates them) and hand them to the Gate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .gate import Sensitivity, ToolCall, TOOL_SENSITIVITY
from .llm import get_config


def get_grants() -> Dict[str, List[str]]:
    cfg = get_config()
    return cfg.get("tools", {}).get("grants", {})


def is_allowed(requester: str, tool: str) -> bool:
    grants = get_grants()
    allowed = grants.get(requester, [])
    if requester == "coordinator":
        return tool in TOOL_SENSITIVITY
    return tool in allowed


def make_call(
    tool: str,
    args: Dict[str, Any],
    requester: str,
    reason: str = "",
) -> ToolCall:
    if not is_allowed(requester, tool):
        raise PermissionError(f"specialist '{requester}' is not granted tool '{tool}'")
    return ToolCall(
        tool=tool,
        args=args,
        requester=requester,
        reason=reason,
        sensitivity=TOOL_SENSITIVITY.get(tool, Sensitivity.WRITE),
    )


def write_file_call(path: str, content: str, requester: str, reason: str = "") -> ToolCall:
    return make_call("write_file", {"path": path, "content": content}, requester, reason)


def research_note_call(text: str, tags: Optional[List[str]] = None, requester: str = "researcher", reason: str = "") -> ToolCall:
    return make_call("research_note", {"text": text, "tags": tags or []}, requester, reason)


def execute_command_call(command: str, requester: str, reason: str = "") -> ToolCall:
    return make_call("execute_command", {"command": command}, requester, reason)


def propose_patch_call(
    content: str,
    prop_id: str = "",
    title: str = "",
    target: str = "",
    hybrid_invariant: str = "preserved",
    requester: str = "architect",
    reason: str = "",
) -> ToolCall:
    """Create a gated propose_patch ToolCall. Application is never automatic."""
    args: Dict[str, Any] = {
        "content": content,
        "title": title,
        "target": target,
        "hybrid_invariant": hybrid_invariant,
        "requester": requester,
    }
    if prop_id:
        args["id"] = prop_id
    return make_call("propose_patch", args, requester, reason or "Architect self-improvement proposal")


def retrieve_knowledge_call(
    query: str,
    domain: Optional[str] = None,
    k: int = 6,
    requester: str = "coordinator",
    reason: str = "",
) -> ToolCall:
    """Create a READ-only retrieve_knowledge ToolCall against the shared knowledge/ RAG."""
    args: Dict[str, Any] = {"query": query, "k": k}
    if domain:
        args["domain"] = domain
    return make_call(
        "retrieve_knowledge",
        args,
        requester,
        reason or f"knowledge retrieval: {query[:60]}",
    )
