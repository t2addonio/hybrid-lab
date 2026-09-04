# RF Residual Stream — Vision & Scope

**Created:** 2026-08-16
**Status:** Scaffold

## Core Idea

Treat spectrum occupancy the way residual-stream work treats model activations:

- There is a high-dimensional “stream” (frequency × time × amplitude / occupancy)
- Most of the stream is background or stable structure
- A smaller set of residual features carry the actionable signal (live transmitters, intermod products, multipath signatures, body absorption, etc.)
- Understanding = being able to isolate, attribute, and reason about those residual features under real venue conditions

## Near-term (this project)

1. Reliable personal data path: SDR capture → normalized scan + operator notes
2. Shared RAG integration (via top-level `knowledge/`) so the multi-agent `rf` specialist and other specialists can retrieve real scans and notes
3. Residual-style analysis primitives:
   - Peak list + context
   - Stable vs transient occupancy
   - Simple intermod candidate generation from observed carriers
   - Venue / show context tagging

## Explicitly later (separate product)

Full RF coordination engine, real-time warning system, automated frequency assignment, etc. Those will consume the understanding layer this project builds.

## Relationship to multi_agent

- `multi_agent/specialists/rf.py` stays the pure text specialist for live-sound RF questions.
- This sibling project owns the heavier data, representation, and experimental work.
- Retrieval is shared through `knowledge/` so the Coordinator path can eventually inject real scan context without the RF specialist itself doing I/O.

## Key principle

> Structure + retrieval of real spectrum beats thin fine-tunes.
> Public scans are useful for occupancy examples.
> Personal SDR captures + frequency notes are what make deep understanding (and later training) valuable.
