# CLI Commands

Tags: #cli #execution

Run the compressor locally before calling an LLM:

```bash
python scripts/run.py --input examples/vault --budget 620 --reserve 80
```

Use `--format markdown` only when the next step expects plain prompt text.
