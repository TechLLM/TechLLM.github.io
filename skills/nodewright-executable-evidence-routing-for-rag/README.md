# Nodewright - Executable Evidence Routing for RAG

Nodewright is an installable experimental skill that scans Markdown files and emits a deterministic JSONL manifest for RAG evidence routing. It detects tables, code blocks, formulas, links, citations, dates, tasks, front matter, embedded references, and external-state language, then assigns each section a retrieval role and recommended tool.

## Install

Place this directory in your Claude Code or OpenClaw-style skills folder, then verify it:

```bash
python scripts/run.py --selftest
python scripts/test.py
```

No dependencies are required beyond Python 3.10 or newer.

## Usage

Show help:

```bash
python scripts/run.py --help
```

Scan the included example:

```bash
python scripts/run.py --input examples/knowledge_base
```

Write a manifest:

```bash
python scripts/run.py --input examples/knowledge_base --output manifest.jsonl
```

Run on built-in sample data:

```bash
python scripts/run.py --selftest
```

## Expected Example Output

The expected output for `python scripts/run.py --input examples/knowledge_base` is also stored in `examples/expected_output.jsonl`.

```jsonl
{"node_id":"nw_0413aa301434","source_identifier":"ops-note.md","content_hash":"9f2a30a5c6ca3c5d","section_anchor":"revenue-check","section_title":"Revenue Check","affordances":["front_matter","table","code_block","link","citation","date","external_state"],"retrieval_role":"run_code","recommended_tool":"python_sandbox","confidence":0.98,"routing_notes":["Fenced code detected; run in a sandbox before trusting generated results.","Linked provenance is present; keep URL context attached to this node.","Date-like text is present; consider freshness checks for time-sensitive use.","Front matter keys are available in source_metadata.front_matter_keys."],"source_metadata":{"source_path":"ops-note.md","section_index":0,"start_line":5,"heading_level":1,"front_matter_keys":["owner","title"],"char_count":235,"word_count":33}}
{"node_id":"nw_e56210919167","source_identifier":"ops-note.md","content_hash":"fcce00a1a59b356d","section_anchor":"launch-tasks","section_title":"Launch Tasks","affordances":["task","external_state"],"retrieval_role":"execute_checklist","recommended_tool":"task_runner","confidence":0.76,"routing_notes":["Checklist state detected; preserve item completion state during retrieval."],"source_metadata":{"source_path":"ops-note.md","section_index":1,"start_line":20,"heading_level":1,"front_matter_keys":[],"char_count":75,"word_count":10}}
```
