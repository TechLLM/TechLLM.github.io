---
name: modalitymesh-specialized-retriever-router-for-scientific-not
description: Builds modality-aware retrieval manifests from Markdown scientific notes when triggers include ModalityMesh, specialized retriever router, scientific notes, Markdown RAG, or modality-aware retrieval.
version: 0.1.0
license: MIT
---

# ModalityMesh - Specialized Retriever Router for Scientific Notes
Auto-generated and experimental; validate routing choices before using them in production retrieval systems.

## Overview
Scientific Markdown notes often mix prose with tables, formulas, code, citations, dates, benchmarks, and structured observations. ModalityMesh scans a Markdown knowledge base and emits a deterministic `retrieval_manifest.json` that tags these patterns and recommends specialized scorers for each file. The manifest is intended as a lightweight routing layer for agents, search services, vector indexing jobs, and RAG pipelines.

## When to use
- Use when a Markdown knowledge base contains scientific, engineering, benchmark, or lab notes with mixed content types.
- Use when building a RAG or agent memory pipeline that should route table, formula, code, citation, timeline, or benchmark queries differently.
- Use when you need explainable evidence for why a file should receive a specialized scorer.
- Use when trigger keywords include `ModalityMesh`, `specialized retriever router`, `scientific notes`, `Markdown RAG`, `modality-aware retrieval`, or `retrieval_manifest.json`.
- When NOT to use: do not use this as a complete search engine or as a substitute for domain review of scorer quality.

## Workflow
1. Collect Markdown notes in one folder, keeping private data and secrets out of the input corpus.
2. Run `python scripts/run.py --help` to inspect available options.
3. Run `python scripts/run.py <markdown-folder> --output retrieval_manifest.json --policy balanced`.
4. Inspect the generated manifest for `tags`, `recommended_scorers`, and `evidence` records.
5. Feed the manifest into an indexing, vector database, agent memory, or RAG routing step.
6. Adjust the policy to `conservative`, `balanced`, or `recall-heavy` and regenerate if retrieval behavior needs to shift.
7. Run `python scripts/test.py` after local edits to confirm the reference implementation still works.

## Inputs & Outputs
Input contract:
- A directory containing one or more `.md` files.
- Optional environment variable: `MODALITYMESH_POLICY`, one of `conservative`, `balanced`, or `recall-heavy`.
- Optional CLI flags: `--policy`, `--output`, `--compact`, and `--selftest`.

Output format:
```json
{
  "schema_version": "1.0",
  "generator": "modalitymesh",
  "policy": "balanced",
  "source_count": 1,
  "modalities": ["table", "formula", "code", "citation", "timeline", "benchmark"],
  "files": [
    {
      "path": "relative-note-path.md",
      "tags": ["table", "formula"],
      "recommended_scorers": ["bm25", "dense-semantic", "numeric-range", "table-structure", "symbolic-formula"],
      "evidence": [
        {
          "modality": "table",
          "block_type": "table",
          "line_start": 7,
          "line_end": 10,
          "reason": "Markdown table with header separator",
          "snippet": "| sample | Tc_K | resistance_ohm |"
        }
      ]
    }
  ]
}
```

## Installation
Copy this skill folder into your local skills directory:

```bash
mkdir -p "$CODEX_HOME/skills"
cp -R . "$CODEX_HOME/skills/modalitymesh-specialized-retriever-router-for-scientific-not"
```

No package installation is required because the reference CLI uses only the Python standard library.

## Usage
```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py examples --output retrieval_manifest.json --policy balanced
MODALITYMESH_POLICY=recall-heavy python scripts/run.py examples --output retrieval_manifest.json
python scripts/test.py
```

## Example
Run:

```bash
python scripts/run.py examples --output retrieval_manifest.json --policy balanced
cat retrieval_manifest.json
```

Expected output is equivalent to `examples/expected_retrieval_manifest.json`. It contains one file record for `scientific_notes.md`, tags all six supported modalities, recommends scorers such as `bm25`, `table-structure`, `symbolic-formula`, `code-semantic`, `citation-graph`, `temporal-date`, and `benchmark-reranker`, and includes line-level evidence for each modality.

## Limitations
- Pattern detection is heuristic and intentionally lightweight.
- The CLI recommends scorer names; it does not execute retrieval or ranking.
- Markdown tables, fenced code blocks, dates, citations, formulas, and benchmarks are detected with practical regex and line-based rules.
- The manifest contains deterministic metadata, not embeddings, model calls, or private service integrations.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
