# PathLoom - Critical-Path Prioritization for Agent Memory

Minimal installable skill with a working standard-library CLI for scoring agent trace JSONL by critical-path relevance.

## Install

```bash
mkdir -p ~/.claude/skills/pathloom-critical-path-prioritization-for-agent-memory
cp -R . ~/.claude/skills/pathloom-critical-path-prioritization-for-agent-memory/
```

No third-party dependencies are required.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --input examples/sample_trace.jsonl
cat examples/sample_trace.jsonl | python scripts/run.py --input -
python scripts/test.py
```

Optional non-secret environment variables:

- `PATHLOOM_NEXT_ACTION`
- `PATHLOOM_WEIGHTS`
- `PATHLOOM_PREFETCH_THRESHOLD`
- `PATHLOOM_PRUNE_THRESHOLD`

## Example

```bash
python scripts/run.py --input examples/sample_trace.jsonl
```

Expected output is deterministic JSON matching `examples/expected_output.json`. The top recommendations include:

```json
{
  "prefetch": [
    {"id": "t2", "priority": 0.955, "why": "directly referenced by next action"},
    {"id": "o1", "priority": 0.885, "why": "directly referenced by next action"},
    {"id": "c1", "priority": 0.845, "why": "directly referenced by next action"}
  ]
}
```
