# Changelog

Versions are declared in `multi_agent/config.yaml` (`system.version`) unless noted.

## 0.6.2-knowledge-rag — 2026-08-16

- Shared `knowledge/` RAG promoted to a multi-agent tool.
- `retrieve_knowledge` is Sensitivity.READ, granted to all specialists.
- `RETRIEVE_KNOWLEDGE:` marker executes immediately; results inject into the specialist turn.
- WRITE tools remain human-gated through Gate.
- Sandbox roots extended to `../knowledge` and `../rf_residual_stream`.

## 0.6.1-rf — 2026-08-15

- Pure-plugin `specialists/rf.py` added.
- Primary focus: pro-audio live RF (wireless mics, IEMs, intercom, coordination, antenna distribution, venue multipath).
- Marine / telemetry RF kept as secondary.

## 0.6.0-act-schema — 2026-08-15

- Closed Act vocabulary: `respond | ask_user | delegate | revise | done`.
- `validate_act`: ok | repair | reject (one repair max, then fail-closed).
- Optional colon on `INVOKE` / `FINAL`.
- Direct INVOKE fast-path preserved.
- Unit tests 12/12 at landing. Backups under `multi_agent/backups/`.

## 0.5.0-self-improvement — 2026-08-15

- Architect emits `CHANGE_PROPOSAL` blocks.
- Gated tool `propose_patch` writes `proposals/` and appends `improvement_log.jsonl`.
- Coordinator extracts `RESEARCH_NOTE:` and `CHANGE_PROPOSAL:`.
- Self-modification remains human-gated.

## 0.4.x-domain-specialists — 2026-08-15

- Domain factory: `residual_stream`, `vibration`, `quantum_sim`.
- Direct INVOKE fast-path working.

## 0.3 tool layer restart — 2026-08-15

- Minimal `Gate` + `ToolCall` + `ToolResult` in `core/gate.py`.
- Only Gate performs side-effects. `approve.py` rebuilt.

## 0.1–0.2 Phase 0 — 2026-08-14

- Hybrid LLM (Ollama default, Grok optional).
- Strict `INVOKE | FINAL` protocol.
- Specialists as pure plugins.
- First end-to-end local run on `tonyedge:latest`.

## edge_bridge 0.1.0-bridge — 2026-08-31

- Sibling project. multi_agent left intact.
- Protocol: `FINAL / INVOKE / CONSULT / HANDOFF`.
- Frontends get private namespaces; only HANDOFF writes `board.jsonl`.
- Starter specialists: researcher, critic, coder, architect.
