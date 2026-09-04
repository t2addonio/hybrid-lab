# RF Residual Stream

**Sibling project** to `multi_agent/`.
**Focus:** Deep model understanding of RF spectrum scans (live SDR + notes), residual-style analysis of occupancy, and the foundation for a future RF Coordination / Analysis / Warning system.

## Relationship to multi_agent

- `multi_agent/specialists/rf.py` remains the pure-plugin live-sound RF specialist.
- This project owns the heavier understanding, representation, and experimental work.
- Shared retrieval goes through the top-level `knowledge/` RAG layer so other specialists can also consume RF (and other) knowledge.

## Near-term goals (Milestone 1)

1. Reliable ingest path for SDR captures + operator frequency notes
2. Strong retrieval + residual-style analysis of spectrum occupancy
3. Clear separation between “understanding layer” and the later full coordination/warning product

## Later (out of scope for now)

Full RF coordination, real-time analysis, and warning system. That will be built on top of the understanding this project produces.

## Key insight carried forward

> Structure + retrieval of real spectrum beats thin fine-tunes.
> Public scans power RAG; personal SDR + frequency notes are what make training and deep understanding worth it.

## Status

Project scaffold created 2026-08-16. Next: define scan representation + residual analysis primitives + wire into shared knowledge RAG.
