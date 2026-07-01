# TraceLoom Execution Log Knowledge Graph Builder

TraceLoom is a minimal installable skill for converting local AI agent execution logs into a small knowledge graph.

It parses JSONL and Markdown logs, resolves references to Markdown notes, and writes:

- `traceloom-output/graph.json`
- `traceloom-output/edge-index.md`

## Quick Install

No Python packages are required.

```bash
python scripts/run.py --help
```

To install as a reusable local skill:

```bash
export SKILL_HOME="${SKILL_HOME:-.codex/skills}"
mkdir -p "$SKILL_HOME"
cp -R . "$SKILL_HOME/traceloom-execution-log-knowledge-graph-builder"
```

## Usage

Run with built-in sample data:

```bash
python scripts/run.py
```

Run the included example:

```bash
python scripts/run.py --logs examples/sample-run.jsonl --notes examples/notes --out traceloom-output
```

Dry-run without writing files:

```bash
python scripts/run.py --logs examples/sample-run.jsonl --notes examples/notes --dry-run
```

Merge newly detected relationships into an existing output graph:

```bash
python scripts/run.py --logs examples/sample-run.jsonl --notes examples/notes --out traceloom-output --incremental
```

## Output

Example edge:

```markdown
[[Research Plan]] --failed--> [[Crawler Prototype]]
```

The JSON graph includes nodes, edges, timestamps, event metadata, confidence scores, and source pointers.
