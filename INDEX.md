# Curated file index

Published tree as of 2026-09-04. Runtime logs, bytecode, `.grok/` memory, and personal SDR captures are excluded.

## Root

| Path | Role |
|------|------|
| README.md | Lab map and invariants |
| LICENSE | MIT |
| CHANGELOG.md | Version history |
| INDEX.md | This file |
| .gitignore | Runtime / secrets / large data |

## docs/

| Path | Role |
|------|------|
| docs/MASTER_README.md | Architecture (single source of truth for the 0.5 freeze; live code is ahead) |
| docs/OPERATING_PROCEDURES.md | Day-to-day operator manual |
| docs/CURRENT_INVENTORY.md | Inventory at documentation freeze |
| docs/HANDOFF_NOTES.md | Next-work list A–F from Conversation 5 |

## catalog/ and templates/

| Path | Role |
|------|------|
| catalog/SPECIALIST_CATALOG.md | Authoritative specialist roster (includes rf) |
| templates/RESEARCH_SESSION_TEMPLATE.md | Research session checklist |
| templates/SELF_IMPROVEMENT_SESSION.md | Architect CHANGE_PROPOSAL cycle |

## multi_agent/

Running system. Version string in `config.yaml` is **0.6.2-knowledge-rag**.

| Path | Role |
|------|------|
| main.py | REPL + one-shot entry |
| approve.py | Human confirmation CLI |
| research.py | Research memory CLI (`state.json`) |
| smoke_test.py | Health check |
| config.yaml | Version, backends, routing, grants, sandbox |
| requirements.txt | `openai`, `pyyaml` |
| COMMANDS.md | Operator cheat sheet |
| README.md | Module overview |
| state.json | Research memory schema v1.0 (sample hypotheses/insights) |
| improvement_log.jsonl | Append-only self-improvement history |
| core/gate.py | Sole side-effect executor |
| core/coordinator.py | Decision loop, markers, fast-path |
| core/protocol.py | FINAL / INVOKE / Act schema |
| core/llm.py | Hybrid Ollama / Grok routing |
| core/registry.py | Specialist discovery |
| core/tools.py | Grants + ToolCall helpers |
| core/sandbox.py | Path allow-list |
| core/state.py | Research memory API |
| core/audit.py | Append-only audit |
| core/memory.py | File memory helper |
| specialists/*.py | Pure plugins |
| specialists/ACTIVE.md | Live roster |
| backups/ | Pre-Act-schema snapshots |

Not published: `audit.jsonl` (local forensic log), live `pending.json`.

## edge_bridge/

| Path | Role |
|------|------|
| main.py, smoke_test.py, config.yaml | Isolated multi-frontend coordinator |
| core/protocol.py | FINAL / INVOKE / CONSULT / HANDOFF |
| core/board.py | Shared board — HANDOFF only |
| specialists/ | researcher, critic, coder, architect |
| namespaces/ | Private scratch per frontend |

## knowledge/

| Path | Role |
|------|------|
| rag/scanner.py, store.py, retrieve.py | Lexical scan + store + retrieve |
| scripts/rag_cli.py | CLI |
| domains/*.yaml | Domain tags |
| config/defaults.yaml | Defaults |

Rebuild the lexical index locally; do not treat sandbox-absolute paths as portable.

## rf_residual_stream/

| Path | Role |
|------|------|
| README.md | Sibling charter |
| docs/01_VISION.md | Residual-style RF scan understanding |
| src/, scripts/, notebooks/, data/ | Scaffold (large captures stay off-repo) |
