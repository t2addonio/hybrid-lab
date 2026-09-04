"""Hierarchical Coordinator — Act Schema v1 + gated tool proposals."""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set

from .audit import get_auditor
from .llm import chat
from .protocol import ActType, parse_act, validate_act
from .registry import Registry
from .gate import Gate, ToolCall, TOOL_HANDLERS
from .tools import research_note_call, propose_patch_call, retrieve_knowledge_call

logger = logging.getLogger("multi_agent.coordinator")

COORDINATOR_SYSTEM = """You are the Coordinator of a Research & Engineering Multi-Agent System.

Available specialists:
{specialist_list}

Your entire reply must begin with EXACTLY one of:
ACT: respond | <answer>
ACT: ask_user | <question>
ACT: delegate | <specialist_name> | <task>
ACT: revise | <reason>
ACT: done | <note>
INVOKE <specialist_name> | <task>
FINAL: <answer>

Rules:
1. Call a specialist only when you need their expertise.
2. After specialist results, prefer ACT: respond / FINAL.
3. Never invent specialist names.
4. Do not repeat the same delegate.
5. Human override is mandatory for write / shell / research_note / propose_patch.
6. RETRIEVE_KNOWLEDGE is READ and executed immediately.
"""


class Coordinator:
    def __init__(self, registry: Registry, max_steps: int = 6, gate: Optional[Gate] = None) -> None:
        self.registry = registry
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []
        self.gate = gate or Gate()
        self._known = set(registry.list_names())

    def _build_coordinator_messages(self, user_query: str, scratchpad: List[str]) -> List[Dict[str, str]]:
        system = COORDINATOR_SYSTEM.format(specialist_list=self.registry.describe())
        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(self.history)
        content = user_query
        if scratchpad:
            content += "\n\n--- Intermediate specialist results ---\n" + "\n\n".join(scratchpad)
            content += "\n\nNow synthesize an ACT: respond (or FINAL). Prefer respond over another delegate."
        messages.append({"role": "user", "content": content})
        return messages

    def _repair_prompt(self, messages: List[Dict[str, str]], bad_raw: str, hint: str) -> str:
        correction = (
            "Your previous reply did not produce a valid Act.\n\n"
            f"Validation message:\n{hint}\n\n"
            "Reply again starting with ACT: respond |, ACT: delegate |, INVOKE, or FINAL:"
        )
        messages = list(messages)
        messages.append({"role": "assistant", "content": bad_raw})
        messages.append({"role": "user", "content": correction})
        return chat(messages, role="coordinator", temperature=0.05)

    def run(self, user_query: str) -> str:
        direct = self._try_direct_invoke(user_query)
        if direct is not None:
            return direct
        scratchpad: List[str] = []
        last_error: Optional[str] = None
        invoked: Set[str] = set()
        repaired_once = False
        for step in range(1, self.max_steps + 1):
            logger.info("Coordinator step %d/%d", step, self.max_steps)
            messages = self._build_coordinator_messages(user_query, scratchpad)
            raw = chat(messages, role="coordinator", temperature=0.1)
            act = parse_act(raw)
            status, msg = validate_act(act, self._known)
            if status == "repair" and not repaired_once and step <= self.max_steps - 1:
                raw = self._repair_prompt(messages, raw, msg)
                act = parse_act(raw)
                status, msg = validate_act(act, self._known)
                repaired_once = True
            if status == "reject":
                last_error = msg
                scratchpad.append(f"[REJECTED ACT]\n{msg}")
                continue
            if status == "repair":
                last_error = msg
                scratchpad.append(f"[UNREPAIRABLE]\n{msg}")
                continue
            if act.type in (ActType.RESPOND, ActType.DONE):
                self._extract_and_propose(act.content, requester="coordinator")
                self.history.append({"role": "user", "content": user_query})
                self.history.append({"role": "assistant", "content": act.content})
                return self._with_pending_footer(act.content)
            if act.type == ActType.ASK_USER:
                return self._with_pending_footer(f"**Clarification needed:**\n\n{act.content}")
            if act.type == ActType.REVISE:
                scratchpad.append(f"[REVISE] {act.content}")
                continue
            if act.type == ActType.DELEGATE:
                name = (act.specialist or "").lower()
                if name in invoked:
                    scratchpad.append(f"[NOTE] Specialist '{name}' already invoked. Produce ACT: respond now.")
                    continue
                try:
                    specialist = self.registry.get(name)
                except KeyError as e:
                    scratchpad.append(f"[ERROR] {e}")
                    last_error = str(e)
                    continue
                result = self._run_specialist(specialist, act.content)
                scratchpad.append(f"### {name} result\n{result}")
                invoked.add(name)
                continue
            last_error = f"unhandled act type {act.type}"
        return (
            f"Coordinator reached max steps ({self.max_steps}) without a clean respond.\n"
            f"Last error: {last_error}\n\nScratchpad:\n" + "\n\n".join(scratchpad)
            + "\n" + self.gate.format_pending()
        )

    def _try_direct_invoke(self, user_query: str) -> Optional[str]:
        act = parse_act(user_query)
        if act.type != ActType.DELEGATE:
            return None
        name = (act.specialist or "").lower()
        if name not in self._known:
            return None
        logger.info("Direct INVOKE fast-path -> %s", name)
        print(f"Direct INVOKE fast-path -> {name}")
        try:
            specialist = self.registry.get(name)
        except KeyError:
            return None
        return self._with_pending_footer(self._run_specialist(specialist, act.content))

    def propose(self, call: ToolCall) -> ToolCall:
        return self.gate.propose(call)

    def _with_pending_footer(self, content: str) -> str:
        if not self.gate.list_pending():
            return content + "\n\n(no pending tool calls)"
        return (
            content + "\n\n---\n" + self.gate.format_pending()
            + "\n\nRun:  python approve.py list"
            + "\n      python approve.py execute <id>"
            + "\n      python approve.py deny <id>"
        )

    def _run_specialist(self, specialist, task: str) -> str:
        messages = specialist.build_messages(task)
        result = chat(messages, role=specialist.name, temperature=0.2)
        injected = self._extract_and_propose(result, requester=specialist.name)
        if injected:
            result = result.rstrip() + "\n\n---\n**Knowledge retrieved for this turn:**\n" + injected
        return result

    def _extract_and_propose(self, text: str, requester: str) -> str:
        if not text:
            return ""
        injected_parts: List[str] = []
        for m in re.finditer(
            r"(?im)^\s*RETRIEVE_KNOWLEDGE\s*:\s*(.+?)(?=\n\s*(?:RESEARCH_NOTE|CHANGE_PROPOSAL|RETRIEVE_KNOWLEDGE)\s*:|\Z)",
            text, re.DOTALL,
        ):
            raw = m.group(1).strip()
            if len(raw) < 3:
                continue
            domain = None
            query = raw
            dm = re.match(r"(?i)^\s*domain\s*=\s*(\S+)\s*\|\s*(.+)$", raw, re.DOTALL)
            if dm:
                domain = dm.group(1).strip()
                query = dm.group(2).strip()
            try:
                call = retrieve_knowledge_call(query=query, domain=domain, k=6, requester=requester, reason=f"auto-retrieve from {requester}")
                data = TOOL_HANDLERS["retrieve_knowledge"](call.args)
                get_auditor().log("executed", call_id=call.id, tool="retrieve_knowledge", requester=requester, result={"hit_count": data.get("hit_count", 0)})
                lines = [f"_Query:_ `{query}`" + (f"  _(domain={domain})_" if domain else "")]
                if not data.get("hits"):
                    lines.append("_No hits._")
                else:
                    for i, h in enumerate(data["hits"], 1):
                        lines.append(f"{i}. **[{h.get('score')}]** `{h.get('path')}` ({h.get('domain')})\n   {h.get('snippet', '')[:220]}")
                injected_parts.append("\n".join(lines))
            except PermissionError as e:
                logger.warning("Grant blocked retrieve_knowledge from %s: %s", requester, e)
            except Exception as e:
                injected_parts.append(f"_Retrieval error:_ {e}")
        for m in re.finditer(
            r"(?im)^\s*RESEARCH_NOTE\s*:\s*(.+?)(?=\n\s*(?:RESEARCH_NOTE|CHANGE_PROPOSAL|RETRIEVE_KNOWLEDGE)\s*:|\Z)",
            text, re.DOTALL,
        ):
            insight = m.group(1).strip()
            if len(insight) < 8:
                continue
            try:
                call = research_note_call(insight, tags=["auto-extracted", requester], requester=requester, reason=f"extracted from {requester} output")
                self.gate.propose(call)
            except PermissionError as e:
                logger.warning("Grant blocked research_note from %s: %s", requester, e)
        for m in re.finditer(
            r"(?im)^\s*CHANGE_PROPOSAL\s*:\s*(.*?)(?=\n\s*(?:RESEARCH_NOTE|CHANGE_PROPOSAL|RETRIEVE_KNOWLEDGE)\s*:|\Z)",
            text, re.DOTALL,
        ):
            block = m.group(1).strip()
            if len(block) < 20:
                continue
            prop_id = title = target = ""
            hybrid = "preserved"
            id_m = re.search(r"(?im)^\s*id\s*:\s*(\S+)", block)
            if id_m:
                prop_id = id_m.group(1).strip()
            title_m = re.search(r"(?im)^\s*title\s*:\s*(.+)$", block)
            if title_m:
                title = title_m.group(1).strip()
            target_m = re.search(r"(?im)^\s*target\s*:\s*(.+)$", block)
            if target_m:
                target = target_m.group(1).strip()
            hybrid_m = re.search(r"(?im)^\s*hybrid_invariant\s*:\s*(\S+)", block)
            if hybrid_m:
                hybrid = hybrid_m.group(1).strip().lower()
            try:
                call = propose_patch_call(
                    content="CHANGE_PROPOSAL:\n" + block, prop_id=prop_id, title=title,
                    target=target, hybrid_invariant=hybrid, requester=requester,
                    reason=f"proposal from {requester}",
                )
                self.gate.propose(call)
            except PermissionError as e:
                logger.warning("Grant blocked propose_patch from %s: %s", requester, e)
        return "\n\n".join(injected_parts)

    def reset(self) -> None:
        self.history.clear()
