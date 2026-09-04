# Shared Knowledge RAG Layer

**Purpose:** Local-first, specialist-agnostic retrieval over project files and domain data.

This layer provides a common file scanner + retrieval surface that any specialist
(or sibling project) can use. It is intentionally separate from the multi-agent
core so that:

- Retrieval stays read-only by default
- Heavy indexes (Chroma, embeddings) live here, not inside `multi_agent/`
- New domains (RF residual stream, residual_stream notes, vibration logs, etc.)
  can be added without touching the Coordinator or Gate

## Design Principles

1. **Local-first** — no cloud embeddings required for basic operation
2. **Read-only by default** — indexing is explicit; retrieval never writes
3. **Domain isolation** — each domain has its own root + metadata
4. **Specialist-friendly** — simple `retrieve(query, domain=..., k=...)` API
5. **Graceful degradation** — works with pure keyword / lexical if embeddings unavailable

## Layout

```
knowledge/
  README.md                 ← this file
  rag/                      ← core engine
  scanners/                 ← file-type specific extractors
  domains/                  ← per-domain config + roots
  indexes/                  ← generated indexes (gitignored later)
  config/                   ← global RAG settings
```

## Quick Use (from any specialist or sibling project)

```python
from knowledge.rag.retrieve import retrieve

hits = retrieve("hottest carriers near 675 MHz", domain="rf", k=5)
for h in hits:
    print(h["score"], h["path"], h["snippet"])
```

## Domains (initial)

| Domain            | Owner / Consumer              | Typical content                     |
|-------------------|-------------------------------|-------------------------------------|
| `rf`              | rf specialist + rf_residual_stream | spectrum scans, notes, coordination |
| `residual_stream` | residual_stream specialist    | experiment notes, α-sweep results   |
| `vibration`       | vibration specialist          | feature logs, NMEA fusion notes     |
| `quantum_sim`     | quantum_sim specialist        | QuTiP patterns, isolation notes     |
| `general`         | researcher / architect        | docs, papers, system notes          |

## Status

Scaffold created 2026-08-16. Core scanner + lexical retrieve first.
Chroma / embedding backends added as optional after the first domain is live.
