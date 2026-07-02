# ModeScribe Modality Routing Manifest Generator

ModeScribe is a small installable skill that analyzes Markdown notes and writes routing metadata for AI retrieval, agent routers, and specialized scorers.

## Install

Copy this folder into the skills directory used by your Claude Code or OpenClaw-style agent runtime.

The reference script has no third-party dependencies.

## Run

Use the bundled sample:

```bash
python scripts/run.py
```

Analyze a Markdown file:

```bash
python scripts/run.py examples/sample-note.md --out routing-manifest.json --patches frontmatter-patches.json
```

Analyze a Markdown directory:

```bash
python scripts/run.py path/to/notes --out routing-manifest.json
```

Use a custom routing policy:

```bash
python scripts/run.py examples/sample-note.md --policy examples/policy.json
```

## Outputs

- `routing-manifest.json`: note-level and section-level modality detections, confidence scores, evidence spans, and route assignments.
- `frontmatter-patches.json`: safe Obsidian-compatible frontmatter suggestions that can be reviewed before applying metadata.

## Environment

Optional variables:

- `MODESCRIBE_INPUT`
- `MODESCRIBE_OUTPUT`
- `MODESCRIBE_PATCHES`
- `MODESCRIBE_POLICY_FILE`
- `MODESCRIBE_MIN_CONFIDENCE`
- `MODESCRIBE_API_KEY`

The script never reads the value of `MODESCRIBE_API_KEY`; it only checks whether one is configured. No external API is called.
