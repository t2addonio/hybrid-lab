# Knowledge indexes

The live lexical index is machine-local. Sandbox builds embed absolute paths and are not published.

Rebuild from the repo root (or `knowledge/`):

```bash
python knowledge/scripts/rag_cli.py status
python knowledge/scripts/rag_cli.py scan
python knowledge/scripts/rag_cli.py query "residual stream phase cancellation"
```

Committed docs under `docs/`, `catalog/`, `templates/`, and domain READMEs are the portable corpus. Personal SDR captures and `/Volumes/rf_data` scans stay on the operator machine.
