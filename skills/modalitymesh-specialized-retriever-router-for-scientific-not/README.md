# ModalityMesh — Specialized Retriever Router for Scientific Notes

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Route scientific notes to the retrieval strategy each modality deserves.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

ModalityMesh is a proposed open-source CLI for building modality-aware retrieval manifests from Markdown knowledge bases. It helps retrieval systems understand that scientific notes are not just prose: they often contain tables, formulas, code, citations, timelines, benchmarks, and other structured evidence.

Most retrieval pipelines flatten notes into generic text chunks and send everything through the same embedding or ranking model. That can miss important signals, especially when the best match depends on numeric comparison, symbolic structure, citation context, or temporal order.

ModalityMesh scans notes, detects retrieval-relevant content patterns, and produces a JSON manifest that downstream systems can use to choose better scorer pipelines for each file, section, or block.

**Who is this for.** ModalityMesh is for builders of AI research assistants, scientific note systems, agent memory layers, vector search workflows, and RAG pipelines that need stronger recall and ranking across mixed technical material.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "schema_version": "1.0",
  "generator": "modalitymesh",
  "policy": "balanced",
  "source_count": 1,
  "modalities": [
    "table",
    "formula",
    "code",
    "citation",
    "timeline",
    "benchmark"
  ],
  "files": [
    {
      "path": "scientific_notes.md",
      "tags": [
        "table",
        "formula",
        "code",
        "citation",
        "timeline",
        "benchmark"
      ],
      "recommended_scorers": [
        "bm25",
        "dense-semantic",
        "numeric-range",
        "table-structure",
        "symbolic-formula",
        "code-semantic",
        "citation-graph",
        "temporal-date",
        "benchmark-reranker"
      ],
      "evidence": [
        {
          "modality": "timeline",
          "block_type": "line",
          "line_start": 3,
          "line_end": 3,
          "reason": "Explicit calendar date",
          "snippet": "Observed on 2024-03-12 during instrument sweep."
        },
        {
          "modality": "formula",
          "block_type": "line",
          "line_start": 5,
          "line_end": 5,
          "reason": "Inline or display math marker",
          "snippet": "The transition estimate follows $T_c = 92K$ for sample A."
        },
        {
          "modality": "table",
          "block_type": "table",
          "line_start": 7,
          "line_end": 10,
          "reason": "Markdown table with header separator",
          "snippet": "| sample | Tc_K | resistance_ohm | | --- | ---: | ---: | | A | 92 | 0.02 | | B | 88 | 0.05 |"
        },
        {
          "modality": "code",
          "block_type": "code_fence",
          "line_start": 12,
          "line_end": 15,
          "reason": "Fenced code block (python)",
          "snippet": "```python def normalize(x): return x / max(x) ```"
        },
        {
          "modality": "citation",
          "block_type": "line",
          "line_start": 17,
          "line_end": 17,
          "reason": "Citation marker or DOI",
          "snippet":
… (+397 chars truncated)
```

## Requirements

| Key | Value |
|---|---|
| Python | 3.9+ |
| Dependencies | Python standard library only |
| API key | Not required |

## 📦 Installation

**1) As a Claude Code / OpenClaw skill**

```bash
# Personal (available in every project)
git clone https://github.com/TechLLM/TechLLM.github.io /tmp/techllm-skills
mkdir -p ~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not
cp -r /tmp/techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not/* ~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/

# Project-local
mkdir -p .claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not
cp -r /tmp/techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not/* .claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/modalitymesh-specialized-retriever-router-for-scientific-not
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/modalitymesh-specialized-retriever-router-for-scientific-not/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [-o OUTPUT] [--policy {conservative,balanced,recall-heavy}]
              [--compact] [--selftest]
              [input_dir]

Build a modality-aware retrieval manifest from Markdown scientific notes.

positional arguments:
  input_dir             Markdown folder to scan. If omitted, the built-in
                        self-test sample is emitted.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Write manifest JSON to this path. Defaults to
                        retrieval_manifest.json when scanning a folder.
  --policy {conservative,balanced,recall-heavy}
                        Routing policy. Defaults to MODALITYMESH_POLICY or
                        balanced.
  --compact             Emit compact single-line JSON instead of pretty-
                        printed JSON.
  --selftest            Run on built-in sample data with no API key and print
                        the manifest.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Scans a Markdown knowledge base recursively and produces deterministic manifest data.
- Detects structured modalities such as tables, formulas, code blocks, citations, timelines, and benchmarks.
- Assigns modality tags and evidence metadata at the file, section, or block level.
- Recommends scorer pipelines suited to each modality, including lexical, semantic, symbolic, numeric, and temporal strategies.
- Supports routing policies so systems can choose conservative, balanced, or recall-heavy retrieval behavior.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The manifest contains fewer modality tags than expected. | The notes may use inconsistent Markdown formatting or patterns that are too ambiguous to classify confidently. | Make structured content more explicit by using standard Markdown tables, fenced code blocks, clear citation markers, and consistent date or benchmark notation. |
| Downstream retrieval still returns generic prose results first. | The consuming search or RAG system may be ignoring the routing recommendations in the manifest. | Check that the manifest tags and scorer recommendations are being read during indexing or query routing, not only generated as a side artifact. |
| A block is tagged with the wrong modality. | Some scientific note patterns overlap, such as code-like formulas, benchmark tables, or citation-heavy prose. | Use routing policy settings and local conventions to bias classification toward the modality that matters most for retrieval. |

## FAQ

**Does ModalityMesh replace a vector database or embedding model?**

No. It is designed to sit before or beside those systems. It creates routing metadata that helps an indexing job, agent, search service, or vector pipeline decide which retrieval strategy to apply.

**Why not embed every note with one strong model?**

A single embedding model can work well for prose, but scientific notes often contain structured signals that need different treatment. Numeric benchmarks, formulas, code, and timelines may require specialized scorers to rank results accurately.

**What does the manifest contain?**

The manifest contains modality tags, evidence metadata, and recommended scorer pipelines for detected files, sections, or blocks. It is intended to be easy for downstream retrieval systems to consume.

**Can this be used outside scientific notes?**

Yes, as long as the knowledge base contains structured Markdown content. It is especially useful when retrieval quality depends on recognizing formats such as tables, code, dates, citations, or measured results.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/` or `.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
