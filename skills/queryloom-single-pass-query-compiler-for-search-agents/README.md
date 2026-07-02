# Queryloom

Queryloom is a minimal installable skill that compiles a natural-language question and a local corpus into a BM25-ready expanded query plan.

## Install

Copy this folder into a Claude Code, OpenClaw, or compatible skills directory.

## Run

Use the built-in sample:

```bash
python scripts/run.py
```

Use the included example corpus:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus.json
```

Save JSON output:

```bash
python scripts/run.py --question "Find low-latency retrieval tactics for search agents" --corpus examples/corpus.json --output query_plan.json
```

## Notes

- No third-party Python packages are required.
- The script reads `QUERYLOOM_API_KEY` if present for future integration compatibility, but it does not call external APIs or print secrets.
- When no question or corpus is supplied, it runs with built-in sample data.
