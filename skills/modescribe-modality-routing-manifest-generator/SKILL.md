---
name: modescribe-modality-routing-manifest-generator
description: Generate deterministic Markdown modality routing manifests for AI retrieval and agent routers when users mention ModeScribe, modality routing, routing-manifest.json, Markdown modality detection, or frontmatter patch suggestions.
license: MIT
---

# ModeScribe Modality Routing Manifest Generator

Auto-generated and experimental reference skill.

## Overview

ModeScribe analyzes Markdown notes and produces explicit routing metadata for AI and LLM agent systems. It detects text, tables, code, math, citations, benchmarks, logs, and mixed-modality content before retrieval, ranking, summarization, or tool selection. The bundled script writes a machine-readable `routing-manifest.json` and a separate frontmatter suggestion file so notes can be reviewed before metadata is applied.

The implementation is deterministic and self-contained. It uses a lightweight Markdown block parser plus structural heuristics for fenced code blocks, table shapes, math delimiters, citation patterns, benchmark names, and log-like sequences. It does not call external models or services.

## When to use

Use this skill when a user wants to:

- Generate a `routing-manifest.json` for a Markdown knowledge base.
- Detect Markdown modalities before retrieval or agent routing.
- Route tables, code, math, citations, benchmarks, logs, and prose to different downstream processing nodes.
- Produce Obsidian-compatible frontmatter patch suggestions without rewriting notes.
- Prototype ModeScribe, modality routing, mixed-modality indexing, or deterministic routing metadata.

## Installation

Place this folder in the skills directory used by your agent runtime.

No Python packages are required. The script uses only the Python standard library.

## Usage

Run the bundled sample:

```bash
python scripts/run.py
```

Analyze one Markdown file:

```bash
python scripts/run.py examples/sample-note.md --out routing-manifest.json --patches frontmatter-patches.json
```

Analyze a directory of Markdown files:

```bash
python scripts/run.py path/to/notes --out routing-manifest.json
```

Use a custom routing policy:

```bash
python scripts/run.py examples/sample-note.md --policy examples/policy.json
```

Use environment variables:

```bash
MODESCRIBE_INPUT=examples/sample-note.md MODESCRIBE_OUTPUT=routing-manifest.json python scripts/run.py
```

Supported environment variables are `MODESCRIBE_INPUT`, `MODESCRIBE_OUTPUT`, `MODESCRIBE_PATCHES`, `MODESCRIBE_POLICY_FILE`, and `MODESCRIBE_MIN_CONFIDENCE`. `MODESCRIBE_API_KEY` may be present, but the reference script never reads its value and never sends data to an external service.

## Example

```bash
python scripts/run.py examples/sample-note.md --out routing-manifest.json
```

Example output shape:

```json
{
  "schema_version": "0.1.0",
  "notes": [
    {
      "path": "examples/sample-note.md",
      "modalities": ["text", "table", "code", "math", "citation", "benchmark", "log", "mixed"],
      "routes": {
        "table": "table_parser",
        "code": "code_indexer"
      }
    }
  ]
}
```

## Limitations

- This is a reference implementation, not a full CommonMark parser.
- Confidence scores are heuristic and should be calibrated against real corpora.
- Section splitting is heading-based and does not model nested heading hierarchies.
- Frontmatter changes are suggestions only; the script does not rewrite Markdown files.
- No external LLMs, embeddings, databases, or private services are used.
