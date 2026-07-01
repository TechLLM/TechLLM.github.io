# DeltaLoom - Incremental Reasoning for Markdown Knowledge Bases

DeltaLoom is a small, installable skill with a runnable reference CLI for detecting what changed in Markdown notes and what reasoning context should be refreshed.

## Install

Copy this folder into your agent runtime's skills directory, or run the script directly from this folder.

No third-party Python dependencies are required.

## Quick Start

Run the built-in sample:

```bash
python scripts/run.py
```

Analyze the included example:

```bash
python scripts/run.py \
  --previous examples/previous.md \
  --current examples/current.md \
  --graph examples/link-graph.json \
  --note-title "Project Alpha" \
  --format report
```

Generate JSON for another agent or pipeline:

```bash
python scripts/run.py \
  --previous examples/previous.md \
  --current examples/current.md \
  --graph examples/link-graph.json \
  --note-title "Project Alpha" \
  --format json
```

## What It Produces

- Changed Markdown block ranges.
- Deleted previous block ranges.
- Added and removed wikilinks.
- Impacted backlinks from the supplied graph.
- Stable summary blocks that can be reused.
- Compact context packets for downstream reasoning.

## Link Graph Format

Use a simple JSON object keyed by note title:

```json
{
  "Project Alpha": {
    "links": ["Roadmap", "Risk Register"],
    "backlinks": ["Research Inbox", "Team Plan"]
  }
}
```

The script also accepts `{"notes": {...}}` with the same per-note shape.
