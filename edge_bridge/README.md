# Edge Bridge (v0.1.0)

Sibling of `multi_agent`. That tree is frozen and still readable.
This tree is a new local-first edge whose **Coordinator is the only shared brain**.

## Point

Frontier models (Grok, OpenAI, Anthropic) and local Ollama do not share a mailbox.
They talk **through this edge**.

- `INVOKE` — local specialist plugin (text only)
- `CONSULT` — one named backend, private scratch under `namespaces/<backend>/`
- `HANDOFF` — the only object that may copy a *slice* onto the shared board (`board.jsonl`)
- `FINAL` — answer to the operator

This is the HF-swarm rule applied as code: a shared writable store is a board; recruiting is explicit; isolation is namespaces + write gates, not vendor labels.

## Run

```bash
cd edge_bridge
pip install -r requirements.txt
python smoke_test.py
python main.py "INVOKE architect | how should two frontiers share an interface"
```

Enable a frontier in `config.yaml` (`backends.grok.enabled: true`) and export its key. Ollama stays required.
