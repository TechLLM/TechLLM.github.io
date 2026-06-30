# LexiPilot

LexiPilot is a minimal installable skill for compiling natural-language questions into BM25-oriented retrieval plans for local Markdown and text corpora.

## Install

Copy this folder into your Claude Code or OpenClaw-style skills directory:

```bash
mkdir -p skills
cp -R . skills/lexipilot-bm25-query-plan-compiler-for-llm-guided-retrieval
```

The CLI uses only the Python standard library.

## Run

Use built-in sample data:

```bash
python scripts/run.py
```

Use the included example corpus:

```bash
python scripts/run.py --question-file examples/question.txt --corpus examples/corpus --search --top-k 3
```

Use your own corpus:

```bash
python scripts/run.py --question "Find notes about BM25 and sparse identifiers" --corpus path/to/notes --out plan.json
```

## Output

The script prints a JSON plan containing extracted lexical signals, decomposed section queries, executable query strings, and optional SQLite FTS5 search results.

## Environment Variables

`OPENAI_API_KEY` and `LEXIPILOT_API_KEY` may be present for downstream integrations, but this reference script does not call external services or print environment variable values.
