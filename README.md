# Hybrid Lab

Local-first, human-gated multi-agent research lab.

**Live code:** `multi_agent` v0.6.2-knowledge-rag  
**Sibling systems:** `edge_bridge` v0.1.0-bridge · `knowledge` RAG · `rf_residual_stream`  
**Owner:** [t2addonio](https://github.com/t2addonio)

This repository is the curated snapshot of the kitchen-table research bus: a Coordinator that speaks a closed protocol, specialists that are pure text plugins, a single Gate for every side-effect, and shared retrieval across domains.

Related public work:

- Residual-stream grokking paper + code: [residual-stream-grokking](https://github.com/t2addonio/residual-stream-grokking)
- Residual Causal Toolkit: [residual-causal-toolkit](https://github.com/t2addonio/residual-causal-toolkit)

---

## Why this exists

Engineering here is the science of laziness: fewest new bits, least action, no autonomous writes.

Non-negotiable invariants:

1. **Local-first** — Ollama is the default backend. Grok is optional hybrid quality.
2. **Human override** — no write, shell, research note, or patch lands without `python approve.py execute <id>`.
3. **Pure-plugin specialists** — they emit text only. They never hold tool handles.
4. **Strict protocol** — Coordinator output starts with `FINAL` or `INVOKE`. Act schema v1 adds `respond | ask_user | delegate | revise | done`.
5. **Single side-effect gate** — only `multi_agent/core/gate.py` may touch the filesystem, shell, or research memory.
6. **Shared stores are message boards** — `state.json`, `pending.json`, `knowledge` indexes, and `edge_bridge/board.jsonl` are write-gated namespaces, not free-for-all memory.

---

## Repository map

| Path | What it is | Start here |
|------|------------|------------|
| [`multi_agent/`](multi_agent/) | Running hybrid bus: Coordinator, Gate, specialists, research memory | [`multi_agent/README.md`](multi_agent/README.md), [`multi_agent/COMMANDS.md`](multi_agent/COMMANDS.md) |
| [`edge_bridge/`](edge_bridge/) | Isolated frontend bridge. Private namespaces. Only `HANDOFF` writes `board.jsonl`. | [`edge_bridge/README.md`](edge_bridge/README.md) |
| [`knowledge/`](knowledge/) | Shared lexical RAG. `retrieve_knowledge` is Sensitivity.READ and runs immediately. | [`knowledge/README.md`](knowledge/README.md) |
| [`rf_residual_stream/`](rf_residual_stream/) | Deep RF scan understanding (residual-style spectrum analysis) | [`rf_residual_stream/README.md`](rf_residual_stream/README.md) |
| [`docs/`](docs/) | Architecture, inventory, operating procedures, handoff | [`docs/MASTER_README.md`](docs/MASTER_README.md) |
| [`catalog/`](catalog/) | Authoritative specialist roster | [`catalog/SPECIALIST_CATALOG.md`](catalog/SPECIALIST_CATALOG.md) |
| [`templates/`](templates/) | Research and self-improvement session checklists | [`templates/RESEARCH_SESSION_TEMPLATE.md`](templates/RESEARCH_SESSION_TEMPLATE.md) |

Full file index: [`INDEX.md`](INDEX.md)  
Version history: [`CHANGELOG.md`](CHANGELOG.md)

---

## Specialists (live)

**Core:** researcher · experiment_critic · coder · architect  
**Domain:** residual_stream · vibration · quantum_sim · rf

Architect is the only specialist fully primed to emit `CHANGE_PROPOSAL` blocks. All specialists may emit `RESEARCH_NOTE:`. Knowledge retrieval uses `RETRIEVE_KNOWLEDGE:`.

---

## Quick start

```bash
git clone https://github.com/t2addonio/hybrid-lab.git
cd hybrid-lab/multi_agent
python -m pip install -r requirements.txt

# Registry only (no LLM)
python -c "from core.registry import Registry; print(Registry.load_default().list_names())"

# Interactive REPL (needs local Ollama or XAI_API_KEY + backends.grok.enabled)
python main.py
python main.py "INVOKE residual_stream | Design a minimal α-sweep + phase-cancellation"

# Side-effects stay pending until a human confirms
python approve.py list
python approve.py execute <id>    # or: deny <id> \"reason\"
```

Enable Grok for preferred roles by setting `backends.grok.enabled: true` in `multi_agent/config.yaml` and exporting `XAI_API_KEY`. Keys are never logged.

---

## Safety

- Do not bypass the Gate.
- Prefer deny when uncertain.
- Sandbox roots are declared in `multi_agent/config.yaml`.
- Runtime logs (`audit.jsonl`) and private namespace scratch are not source of truth; treat them as local operator state.
- API keys live in environment variables only (`XAI_API_KEY`, never committed).

---

## License

MIT. See [`LICENSE`](LICENSE).
