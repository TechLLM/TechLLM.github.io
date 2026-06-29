# TraceVault - Evidence Audits for Agent-Written Knowledge Bases

TraceVault is a small, local reference CLI for auditing Markdown vault changes made by agents or LLM workflows. It compares before and after vault directories, checks a YAML expectation file, and emits a machine-readable evidence audit report.

## Install

Use this folder as an installable skill directory:

```sh
mkdir -p ../skills
cp -R . ../skills/tracevault-evidence-audits-for-agent-written-knowledge-bases
```

The CLI has no external dependencies.

## Run

Run with the bundled sample data:

```sh
python scripts/run.py
```

Run against the included example files:

```sh
python scripts/run.py \
  --before examples/before_vault \
  --after examples/after_vault \
  --expectations examples/audit.yaml \
  --out evidence_audit.json
```

Use `--fail-on-fail` in CI when a failing audit should return a non-zero exit code.

## Audit Specification

The expectation file supports a small YAML subset:

- `required_created_notes`
- `required_modified_notes`
- `required_frontmatter_fields`
- `required_sections`
- `required_output_fields`
- `required_evidence_nodes`
- `min_created_notes`
- `min_modified_notes`
- `min_new_wikilinks`
- `max_broken_links`
- `max_unsupported_claims`

See `examples/audit.yaml` for a complete minimal contract.
