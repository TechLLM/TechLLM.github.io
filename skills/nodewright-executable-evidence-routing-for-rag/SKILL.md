---
name: nodewright-executable-evidence-routing-for-rag
description: Turns Markdown knowledge bases into executable evidence-routing JSONL manifests for RAG; use for Nodewright, evidence routing, Markdown RAG, executable affordances, retrieval roles, JSONL manifests.
license: MIT
---

# Nodewright - Executable Evidence Routing for RAG

Auto-generated and experimental; review outputs before production indexing.

## Overview

Markdown knowledge bases often contain more than prose: tables, code, dates, citations, links, equations, front matter, and task state all imply different retrieval and execution behavior. Nodewright scans Markdown files before indexing and emits JSONL evidence nodes that preserve those affordances. The manifest lets an agent retrieve context together with a recommended handling procedure, such as reading, computing, verifying, following links, running code, or executing checklist state.

## When to use

- Use when preparing a Markdown, Obsidian, MkDocs, or docs-as-code knowledge base for retrieval-augmented generation.
- Use when a RAG agent must know whether retrieved evidence should be read, computed, verified, queried, transformed, or executed.
- Use when building indexing jobs, evaluation fixtures, retrieval manifests, or orchestration inputs from Markdown folders.
- Use when trigger keywords appear: Nodewright, executable evidence, evidence routing, Markdown RAG, affordance detection, retrieval roles, JSONL manifest.
- When NOT to use: do not use this skill as a semantic search engine or as a replacement for human review of legal, medical, financial, or safety-critical claims.

## Workflow

1. Identify the Markdown file or folder to scan.
2. Run the bundled CLI with `python scripts/run.py --input <markdown-path> --output <manifest.jsonl>`.
3. Inspect each JSONL line for `affordances`, `retrieval_role`, `recommended_tool`, `confidence`, and `routing_notes`.
4. Feed the manifest into an indexer, RAG evaluation harness, or agent orchestration layer.
5. Route retrieved nodes according to `retrieval_role`: read context directly, compute tables or formulas, run code in a sandbox, verify dated or cited claims, follow links, inspect state, or execute checklists.
6. Re-run the CLI when source notes change so node hashes and routing hints stay current.

## Inputs & Outputs

Input contract:

- A Markdown file or a directory containing `.md` or `.markdown` files.
- Optional YAML-like front matter delimited by `---`.
- No API key is required for the deterministic rule-based scanner.
- Optional environment variables are read but never printed: `NODEWRIGHT_API_KEY` and `NODEWRIGHT_LLM_PROVIDER`. The reference implementation does not call external services.

Output contract:

- The CLI emits line-delimited JSON.
- Each line is one evidence node with this exact object shape:

```json
{
  "node_id": "stable sha1-derived identifier",
  "source_identifier": "relative markdown source path",
  "content_hash": "sha256 hash prefix for the section content",
  "section_anchor": "slugified markdown heading anchor",
  "section_title": "markdown heading title or Document",
  "affordances": ["detected affordance names"],
  "retrieval_role": "read_context | compute_table | run_code | verify_claim | follow_link | inspect_state | execute_checklist",
  "recommended_tool": "markdown_reader | python_sandbox | sql_engine | shell_sandbox | web_fetcher | citation_checker | calendar_parser | task_runner",
  "confidence": 0.0,
  "routing_notes": ["short deterministic routing note"],
  "source_metadata": {
    "source_path": "relative markdown source path",
    "section_index": 0,
    "start_line": 1,
    "heading_level": 1,
    "front_matter_keys": ["sorted metadata keys"],
    "char_count": 0,
    "word_count": 0
  }
}
```

## Installation

Copy or symlink this skill directory into your agent skill folder, then run the self-test:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

No third-party Python packages are required.

## Usage

Show CLI help:

```bash
python scripts/run.py --help
```

Run on the included example:

```bash
python scripts/run.py --input examples/knowledge_base --output examples/generated_manifest.jsonl
```

Run on your own Markdown folder and print JSONL to stdout:

```bash
python scripts/run.py --input path/to/notes
```

Run the built-in deterministic sample:

```bash
python scripts/run.py --selftest
```

## Example

Command:

```bash
python scripts/run.py --input examples/knowledge_base
```

Expected output is JSONL with one evidence node per Markdown section. The included fixture is stored at `examples/expected_output.jsonl` and contains nodes for a code/table-heavy evidence section and a checklist section.

## Limitations

- The classifier is deterministic and rule-based, so it does not infer deep semantics beyond visible Markdown signals.
- The scanner handles common front matter patterns but is not a full YAML parser.
- Code is classified and routed but never executed by the CLI.
- Links and citations are detected but not fetched or validated by the CLI.
- LLM-assisted refinement is intentionally not implemented in this self-contained reference version.
