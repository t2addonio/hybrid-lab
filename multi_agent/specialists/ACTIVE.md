# Active Specialists (v0.6.2 — Knowledge RAG)

## Core (Phase-0)
- `researcher` — literature, synthesis, factual grounding
- `experiment_critic` — experimental design critique, confounds, statistics
- `coder` — modular code production
- `architect` — system design, interfaces, trade-offs, **reflection & gated change proposals**

## Domain
- `residual_stream` — residual-stream geometry, causal interventions, grokking dynamics, α-sweeps, phase-cancellation, dynamic-range control
- `vibration` — multi-axis vibration features (RMS/peak/FFT), mechanical anomaly detection, NMEA 2000 fusion, rigid-mount constraints
- `quantum_sim` — NV-center / diamond color-center simulation helpers, phononic isolation, QuTiP patterns, T³ structural scaling
- `rf` — pro-audio live RF (wireless mics, IEMs, intercom), frequency coordination, antenna distribution, spectrum management, venue multipath; marine/telemetry when relevant

## Status
- All eight specialists load and fire via direct `INVOKE name | task` fast-path (colon optional).
- **Act Schema v1 live**: closed vocabulary `respond | ask_user | delegate | revise | done` + `validate_act` (ok | repair | reject, one repair max, then fail-closed).
- Legacy `INVOKE` / `FINAL` forms still accepted and preferred for local-model reliability.
- Architect enhanced (v0.5.0) for self-improvement: can emit `CHANGE_PROPOSAL:` blocks; Coordinator extracts them and proposes gated `propose_patch` calls.
- **Knowledge RAG (v0.6.2)**: shared `knowledge/` layer. Specialists emit `RETRIEVE_KNOWLEDGE: <query>` (or `domain=rf | <query>`). READ tools execute immediately and results are injected into the specialist turn. WRITE tools still require human approve.
- Hybrid Grok path remains available (enable in config.yaml + XAI_API_KEY) for high-quality output without code changes.
- Hybrid invariants are non-negotiable: local-first, human override, pure-plugin specialists, strict protocol surface.
