"""Act Schema v1 + legacy INVOKE/FINAL compatibility."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class ActType(str, Enum):
    RESPOND = "respond"
    ASK_USER = "ask_user"
    DELEGATE = "delegate"
    REVISE = "revise"
    DONE = "done"
    ERROR = "error"


@dataclass
class Act:
    type: ActType
    content: str = ""
    specialist: Optional[str] = None
    raw: str = ""
    repair_hint: str = ""


_ACT_RE = re.compile(
    r"^\s*ACT\s*:\s*(respond|ask_user|delegate|revise|done)\s*(?:\|\s*(.*))?$",
    re.IGNORECASE | re.DOTALL,
)
_INVOKE_RE = re.compile(
    r"^\s*INVOKE\s*:?\s*([a-zA-Z0-9_\-]+)\s*\|\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
_FINAL_RE = re.compile(
    r"^\s*FINAL\s*:?\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
_SOFT_ACT_RE = re.compile(
    r"(?im)^\s*ACT\s*:\s*(respond|ask_user|delegate|revise|done)\s*(?:\|\s*(.*))?$",
)


def parse_act(text: str) -> Act:
    raw = (text or "").strip()
    if not raw:
        return Act(type=ActType.ERROR, content="empty response", raw=raw,
                   repair_hint="Emit a non-empty ACT: line.")
    first = raw.splitlines()[0].strip() if raw else ""
    m = _ACT_RE.match(first)
    if m:
        return _build_act(m.group(1).lower(), (m.group(2) or "").strip(), raw)
    m = _INVOKE_RE.match(first)
    if m:
        return Act(type=ActType.DELEGATE, specialist=m.group(1).strip().lower(), content=m.group(2).strip(), raw=raw)
    m = _FINAL_RE.match(first)
    if m:
        return Act(type=ActType.RESPOND, content=m.group(1).strip(), raw=raw)
    m = _SOFT_ACT_RE.search(raw)
    if m:
        return _build_act(m.group(1).lower(), (m.group(2) or "").strip(), raw)
    return Act(
        type=ActType.ERROR,
        content=f"unparseable\n---\n{raw[:400]}",
        raw=raw,
        repair_hint="Reply with ACT: respond | <answer> or INVOKE <specialist> | <task> or FINAL: <answer>",
    )


def _build_act(kind: str, rest: str, raw: str) -> Act:
    if kind == "delegate":
        parts = [p.strip() for p in rest.split("|", 1)]
        if len(parts) == 2 and parts[0]:
            return Act(type=ActType.DELEGATE, specialist=parts[0].lower(), content=parts[1], raw=raw)
        return Act(type=ActType.ERROR, content=f"malformed delegate: {rest!r}", raw=raw,
                   repair_hint="Use: ACT: delegate | <specialist_name> | <self-contained task>")
    if kind == "respond":
        return Act(type=ActType.RESPOND, content=rest, raw=raw)
    if kind == "ask_user":
        return Act(type=ActType.ASK_USER, content=rest or "Please clarify.", raw=raw)
    if kind == "revise":
        return Act(type=ActType.REVISE, content=rest or "re-think", raw=raw)
    if kind == "done":
        return Act(type=ActType.DONE, content=rest, raw=raw)
    return Act(type=ActType.ERROR, content=f"unknown act kind: {kind}", raw=raw)


def validate_act(act: Act, known_specialists: set[str]) -> Tuple[str, str]:
    if act.type == ActType.ERROR:
        return "repair", act.repair_hint or act.content
    if act.type == ActType.DELEGATE:
        name = (act.specialist or "").lower()
        if not name:
            return "repair", "delegate missing specialist name"
        if name not in known_specialists:
            return "repair", f"unknown specialist '{name}'. Valid: {', '.join(sorted(known_specialists))}"
        if not (act.content or "").strip():
            return "repair", "delegate task is empty"
        return "ok", ""
    if act.type == ActType.RESPOND:
        if not (act.content or "").strip():
            return "repair", "respond content is empty"
        return "ok", ""
    if act.type == ActType.ASK_USER:
        if not (act.content or "").strip():
            return "repair", "ask_user question is empty"
        return "ok", ""
    if act.type in (ActType.REVISE, ActType.DONE):
        return "ok", ""
    return "reject", f"unsupported act type: {act.type}"


class DecisionType(str, Enum):
    FINAL = "FINAL"
    INVOKE = "INVOKE"
    ERROR = "ERROR"


@dataclass
class Decision:
    type: DecisionType
    content: str = ""
    specialist: Optional[str] = None
    raw: str = ""


def parse_decision(text: str) -> Decision:
    act = parse_act(text)
    if act.type == ActType.RESPOND or act.type == ActType.DONE:
        return Decision(type=DecisionType.FINAL, content=act.content, raw=act.raw)
    if act.type == ActType.DELEGATE:
        return Decision(type=DecisionType.INVOKE, specialist=act.specialist, content=act.content, raw=act.raw)
    return Decision(type=DecisionType.ERROR, content=act.content, raw=act.raw)
