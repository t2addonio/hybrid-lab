# Self-Improvement Session Template
**Trigger:** Architect reflection + gated CHANGE_PROPOSAL cycle

```bash
python main.py "INVOKE architect | Reflect on current multi-agent system friction points and emit zero or more CHANGE_PROPOSAL blocks. Preserve all hybrid invariants."
python approve.py list
python approve.py show <id>
python approve.py execute <id>
```

Land the change by hand until gated apply_patch exists. Confirm invariants still hold.
