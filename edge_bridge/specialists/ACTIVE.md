# Active specialists — Edge Bridge v0.1.0

- `researcher` — synthesis and grounding
- `critic` — attack assumptions
- `coder` — small modules, no fake disk writes
- `architect` — interfaces and isolation

Add new specialists the same way as `multi_agent`: a plugin module exposing `specialist = ...()`, then register in `core/registry.py`.
Do not give plugins tool handles.
