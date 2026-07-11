---
name: riftlens-domain-collapse-maps-for-rag-evaluation
description: Generates domain-collapse maps for RAG evaluation from JSONL retrieval logs; use for riftlens, RAG eval, domain split, retriever regression, reranker gate, and release review checks.
version: 0.1.0
license: MIT
---

# RiftLens — Domain Collapse Maps for RAG Evaluation
Auto-generated and experimental; validate thresholds against your own evaluation policy before using as a release gate.

## Overview
RAG systems can look healthy on an aggregate relevance score while failing badly on one source domain, such as API references, tickets, notes, wiki pages, summaries, or policy documents. RiftLens evaluates retrieved documents by domain and highlights hit-rate gaps, false passes, false rejects, and coverage so hidden domain regressions are visible in review.

The bundled CLI reads plain JSONL retrieval logs, applies a configurable score threshold, and emits a deterministic Markdown report suitable for pull requests, audit notes, and experiment tracking.

## When to use
- Use when comparing RAG retrievers, rerankers, relevance gates, or prompt changes across mixed source domains.
- Use when a query set includes tagged retrieved documents from domains such as notes, wiki pages, tickets, docs, summaries, policies, or API references.
- Use before shipping a retrieval change whose average score improved but may have harmed a source domain.
- Use when writing a PR comment, evaluation memo, regression report, or release-gate note for RAG behavior.
- When NOT to use: do not use RiftLens as the only quality signal for generation faithfulness, answer correctness, latency, or user satisfaction.

## Workflow
1. Export retrieval evaluation logs as JSONL, one query per line.
2. Ensure each retrieved document has a `domain`, numeric `score`, and boolean `relevant` label.
3. Choose a threshold for the relevance gate or reranker score; use `--threshold` or `RIFTLENS_THRESHOLD`.
4. Run `python scripts/run.py --input <file.jsonl> --threshold <value>` from the skill directory.
5. Review the Markdown report, especially worst-domain gap, low hit-rate domains, high false-pass domains, and high false-reject domains.
6. Save the report into the PR, experiment tracker, release checklist, or regression notes.
7. Re-run the same input and threshold for deterministic comparisons across branches or model versions.

## Inputs & Outputs
Input is newline-delimited JSON. Each line must be an object with a query id and a `retrieved` list:

```json
{"query_id":"q1","retrieved":[{"doc_id":"d1","domain":"wiki","score":0.82,"relevant":true}]}
```

Required fields:
- `query_id` or `id`: stable query identifier.
- `retrieved`: list of retrieved document objects.
- `retrieved[].domain`: source-domain label.
- `retrieved[].score`: numeric score used by the gate.
- `retrieved[].relevant`: boolean ground-truth relevance label.

Optional fields:
- `retrieved[].doc_id`: document identifier used only for validation context.
- `RIFTLENS_THRESHOLD`: default threshold when `--threshold` is not supplied.
- `RIFTLENS_TOP_K`: default top-k cutoff when `--top-k` is not supplied.

CLI output is Markdown with this shape:
- H1 title: `# RiftLens Domain Collapse Report`
- Summary bullets: threshold, top-k, query count, retrieved item count, overall hit rate, overall false pass rate, overall false reject rate, worst-domain gap, worst domain.
- Domain table with columns: Domain, Coverage, Hit rate, False pass, False reject, Relevant, Passed.
- Flags list naming collapse, false-pass, and false-reject risks.

The importable function `evaluate_records(records, threshold=0.6, top_k=None)` returns a dictionary with:
- `threshold`, `top_k`, `query_count`, `domain_count`
- `overall`: counts and aggregate rates
- `domains`: sorted list of per-domain metric dictionaries
- `best_domain`, `worst_domain`, `worst_domain_gap`
- `flags`: list of human-readable risk flags

## Installation
Copy this directory into your Claude Code, OpenClaw, or compatible skills folder. No third-party packages are required.

```bash
python --version
python scripts/run.py --help
python scripts/test.py
```

## Usage
Run the built-in sample with no external data:

```bash
python scripts/run.py --selftest
```

Run an example file:

```bash
python scripts/run.py --input examples/sample.jsonl --threshold 0.6
```

Write the report to a Markdown file:

```bash
python scripts/run.py --input examples/sample.jsonl --threshold 0.6 --output report.md
```

Limit evaluation to the top retrieved documents per query:

```bash
python scripts/run.py --input examples/sample.jsonl --threshold 0.6 --top-k 3
```

Show all CLI options:

```bash
python scripts/run.py --help
```

## Example
Command:

```bash
python scripts/run.py --input examples/sample.jsonl --threshold 0.6
```

Expected output:

```markdown
# RiftLens Domain Collapse Report

- Threshold: `0.60`
- Top K: `all`
- Queries: `3`
- Retrieved items: `8`
- Overall hit rate: `75.0%`
- Overall false pass rate: `50.0%`
- Overall false reject rate: `25.0%`
- Worst-domain gap: `100.0 pp`
- Worst domain: `api_reference`

| Domain | Coverage | Hit rate | False pass | False reject | Relevant | Passed |
|---|---:|---:|---:|---:|---:|---:|
| api_reference | 66.7% | 0.0% | 0.0% | 100.0% | 1 | 0 |
| notes | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |
| tickets | 66.7% | 100.0% | 0.0% | 0.0% | 1 | 1 |
| wiki | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |

## Flags

- Collapse: `api_reference` trails the best domain by `100.0 pp`.
- Risk: `api_reference` has high false reject rate (`100.0%`).
- Risk: `notes` has high false pass rate (`100.0%`).
- Risk: `wiki` has high false pass rate (`100.0%`).
```

## Limitations
- RiftLens depends on truthful domain tags and relevance labels; poor labels produce poor diagnostics.
- It evaluates retrieval and gating behavior, not final generated answer quality.
- It uses simple threshold-based pass/fail logic and does not model calibrated probabilities.
- Small per-domain sample sizes can create noisy rates; inspect counts before making release decisions.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
