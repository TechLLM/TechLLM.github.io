# DeltaWeave

DeltaWeave is a small installable skill and reference CLI for incremental context compression in LLM and agent workflows.

It compares a previous snapshot with a current snapshot and emits a compact delta pack that shows changed sections, nearby context, and unchanged anchors.

## Install

Copy this folder into your agent runtime's skills directory.

No Python packages are required.

## Run

Use the built-in sample:

```bash
python scripts/run.py
```

Compare the included example files:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format markdown
```

Emit JSON:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format json
```

Emit an LLM-ready prompt:

```bash
python scripts/run.py --old examples/previous.md --new examples/current.md --format prompt
```

Compare code by function/class boundaries:

```bash
python scripts/run.py --old examples/previous.py --new examples/current.py --granularity function
```

## Notes

- The CLI is local-only and standard-library only.
- Optional environment variables such as `DELTAWEAVE_API_KEY` or `OPENAI_API_KEY` are detected only as booleans; secret values are never printed.
- Function/class extraction is heuristic and intended as a compact reference implementation.
