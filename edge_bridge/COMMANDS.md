# Edge Bridge commands

```bash
python smoke_test.py
python main.py
python main.py "INVOKE researcher | summarize isolation rules"
python main.py "CONSULT grok | review this interface: HANDOFF only"
```

Coordinator protocol lines:

```
FINAL: ...
INVOKE: <specialist> | <task>
CONSULT: <ollama|grok|openai|anthropic> | <task>
HANDOFF: to=<name> | <payload slice>
```
