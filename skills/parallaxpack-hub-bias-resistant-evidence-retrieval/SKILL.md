---
name: parallaxpack-hub-bias-resistant-evidence-retrieval
description: Rerank knowledge-graph evidence into diverse, provenance-rich packs; use for graph RAG, hub bias, evidence retrieval, community diversity, recency, provenance, or nearest-neighbor baseline comparison requests.
version: 0.1.0
license: MIT
---

# ParallaxPack — Hub-Bias-Resistant Evidence Retrieval

Auto-generated and experimental; validate policy settings against your corpus before production use.

## Overview

Graph retrieval can over-select highly connected background nodes while missing fresh operational evidence in smaller communities. Apply this skill after candidate generation to combine semantic relevance, inverse graph degree, recency, source completeness, metadata quality, community constraints, and redundancy penalties in a reproducible evidence pack.

## When to use

- Use when graph-RAG results are dominated by hubs or generic overview notes.
- Use when an evidence pack must cover multiple graph communities with inspectable provenance.
- Use when comparing a diversity-aware policy with a semantic nearest-neighbor baseline.
- Use when recent incidents, long-tail notes, or operational records need explicit retrieval weight.
- When NOT to use: do not use this script as a vector database, graph crawler, or factual verifier; provide already-authorized candidate notes and validate their sources separately.

## Workflow

1. Export candidate notes and an edge list from the existing graph or retrieval system.
2. Add a natural-language `query`, a deterministic `as_of` date, note metadata, and optional policy settings using the schema below.
3. Run `scripts/run.py` in `json`, `markdown`, or `both` mode; use `--top-k`, `--per-community-cap`, or `--min-communities` for run-specific overrides.
4. Inspect each selected note's raw score components, weighted contributions, redundancy penalty, provenance, community, and rationale.
5. Compare the ParallaxPack metrics with the semantic-only baseline for community coverage, hub concentration, freshness, and provenance coverage.
6. Pass only the reviewed evidence pack to prompt assembly; retain the JSON output for reproducibility.

## Inputs & Outputs

Input is one UTF-8 JSON object:

```text
query: non-empty string
as_of: YYYY-MM-DD (optional; defaults to the latest note date)
graph.nodes: optional unique node-ID array
graph.edges: array of two-node ID arrays; candidate degree is computed from unique neighbors
notes[]: {id, title, text, community, updated_at, sources[], tags[], semantic_score?}
sources[]: {title, uri, retrieved_at?}
settings: {top_k, per_community_cap, min_communities, redundancy_weight, weights?}
```

`semantic_score` must be between 0 and 1. If omitted, the script uses deterministic token-overlap relevance. Output formats are:

- `json`: `{query, as_of, configuration, summary, baseline_comparison, results[], excluded[]}`. Every result contains `rank`, identity and date fields, `degree`, final `score`, `score_components`, `weighted_contributions`, `provenance`, and `rationale`. Excluded candidates contain the same scoring explanation plus an exclusion rationale.
- `markdown`: an LLM-ready report with baseline metrics, a selected-evidence table, detailed component/provenance sections, and exclusions.
- `both`: `{evidence_pack: <json object>, markdown: <string>}`.

Scores and metrics are rounded to six decimal places. Ties break by note ID, so identical input produces identical output.

## Installation

```bash
git clone <repository-url> parallaxpack-hub-bias-resistant-evidence-retrieval
cd parallaxpack-hub-bias-resistant-evidence-retrieval
python3 scripts/run.py --help
python3 scripts/test.py
```

The reference implementation uses only the Python standard library and requires Python 3.9 or newer. No API key is required.

## Usage

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/run.py --input examples/input.json --format json
python3 scripts/run.py --input examples/input.json --format markdown
python3 scripts/run.py --input examples/input.json --format both --output evidence-pack.json
python3 scripts/run.py --input examples/input.json --top-k 4 --per-community-cap 2 --min-communities 3
```

Set `PARALLAXPACK_DEFAULT_FORMAT` to `json`, `markdown`, or `both`, and optionally set `PARALLAXPACK_TOP_K` to a positive integer. Command-line values take precedence. Existing output files are rejected unless both `--output` and `--force` are supplied.

## Example

Run:

```bash
python3 scripts/run.py --input examples/input.json --format json
```

The complete expected document is in `examples/expected-output.json`. Its summary selects four notes from at least three communities and reports both the semantic-only baseline and the reranked policy:

```json
{
  "candidate_count": 6,
  "selected_count": 4,
  "excluded_count": 2
}
```

## Limitations

- Treat supplied semantic scores and metadata as inputs, not independently verified facts.
- Use the lexical fallback only for small demonstrations; production systems should pass candidate relevance scores from their retriever.
- Tune weights and diversity limits per corpus; the defaults are policy examples, not universal optima.
- Graph degree is calculated only from the supplied edge list, so truncated graphs can misclassify hubs.
- Recency uses a simple deterministic decay and does not model domain-specific urgency.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · contract=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
