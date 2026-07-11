#!/usr/bin/env python3
"""Build modality-aware retrieval manifests for Markdown scientific notes.

The CLI scans Markdown files, detects retrieval-relevant modalities, and emits
a deterministic JSON manifest with scorer recommendations and evidence records.
It uses only the Python standard library and does not require API keys.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


SCHEMA_VERSION = "1.0"
GENERATOR = "modalitymesh"
POLICIES = ("conservative", "balanced", "recall-heavy")
MODALITY_ORDER = ("table", "formula", "code", "citation", "timeline", "benchmark")

SCORERS_BY_POLICY = {
    "conservative": {
        "table": ("bm25", "table-structure"),
        "formula": ("bm25", "symbolic-formula"),
        "code": ("bm25", "code-semantic"),
        "citation": ("bm25", "citation-graph"),
        "timeline": ("bm25", "temporal-date"),
        "benchmark": ("bm25", "numeric-range"),
    },
    "balanced": {
        "table": ("bm25", "dense-semantic", "numeric-range", "table-structure"),
        "formula": ("bm25", "symbolic-formula"),
        "code": ("bm25", "code-semantic"),
        "citation": ("bm25", "citation-graph"),
        "timeline": ("bm25", "temporal-date"),
        "benchmark": ("bm25", "dense-semantic", "numeric-range", "benchmark-reranker"),
    },
    "recall-heavy": {
        "table": ("bm25", "dense-semantic", "numeric-range", "table-structure", "cross-modal-reranker"),
        "formula": ("bm25", "dense-semantic", "symbolic-formula", "cross-modal-reranker"),
        "code": ("bm25", "dense-semantic", "code-semantic", "cross-modal-reranker"),
        "citation": ("bm25", "dense-semantic", "citation-graph", "cross-modal-reranker"),
        "timeline": ("bm25", "dense-semantic", "temporal-date", "cross-modal-reranker"),
        "benchmark": ("bm25", "dense-semantic", "numeric-range", "benchmark-reranker", "cross-modal-reranker"),
    },
}

SAMPLE_MARKDOWN = """# Superconductor Notes

Observed on 2024-03-12 during instrument sweep.

The transition estimate follows $T_c = 92K$ for sample A.

| sample | Tc_K | resistance_ohm |
| --- | ---: | ---: |
| A | 92 | 0.02 |
| B | 88 | 0.05 |

```python
def normalize(x):
    return x / max(x)
```

Smith et al. [Smith 2021] reported a comparable curve. DOI:10.1000/example

Benchmark: recall@10 improved from 0.71 to 0.83 with table-aware scoring.
"""

SAMPLE_NOTES = {"scientific_notes.md": SAMPLE_MARKDOWN}


Evidence = Dict[str, object]
Manifest = Dict[str, object]


def normalize_policy(policy: str | None) -> str:
    """Return a validated routing policy, falling back to the environment."""
    value = policy or os.environ.get("MODALITYMESH_POLICY", "balanced")
    if value not in POLICIES:
        allowed = ", ".join(POLICIES)
        raise ValueError(f"invalid policy {value!r}; expected one of: {allowed}")
    return value


def build_manifest_from_texts(notes: Mapping[str, str], policy: str | None = None) -> Manifest:
    """Build a retrieval manifest from a mapping of relative Markdown paths to text."""
    selected_policy = normalize_policy(policy)
    files = []
    detected_modalities = set()

    for note_path in sorted(notes):
        text = notes[note_path]
        evidence = detect_modalities(text)
        tags = [name for name in MODALITY_ORDER if any(item["modality"] == name for item in evidence)]
        detected_modalities.update(tags)
        files.append(
            {
                "path": note_path,
                "tags": tags,
                "recommended_scorers": recommend_scorers(tags, selected_policy),
                "evidence": evidence,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "policy": selected_policy,
        "source_count": len(files),
        "modalities": [name for name in MODALITY_ORDER if name in detected_modalities],
        "files": files,
    }


def scan_markdown_directory(root: str | Path) -> Dict[str, str]:
    """Read all Markdown files under a directory and return relative paths to text."""
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"input directory does not exist: {root}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {root}")

    markdown_files = sorted(root_path.rglob("*.md"), key=lambda item: item.relative_to(root_path).as_posix())
    if not markdown_files:
        raise ValueError(f"no Markdown files found under: {root}")

    notes: Dict[str, str] = {}
    for file_path in markdown_files:
        relative = file_path.relative_to(root_path).as_posix()
        try:
            notes[relative] = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"could not read {relative} as UTF-8") from exc
    return notes


def detect_modalities(markdown_text: str) -> List[Evidence]:
    """Detect supported modalities and return sorted block-level evidence."""
    lines = markdown_text.splitlines()
    code_evidence, code_ranges = detect_code_blocks(lines)
    evidence = []
    evidence.extend(detect_tables(lines, code_ranges))
    evidence.extend(detect_formulas(lines, code_ranges))
    evidence.extend(code_evidence)
    evidence.extend(detect_citations(lines, code_ranges))
    evidence.extend(detect_timelines(lines, code_ranges))
    evidence.extend(detect_benchmarks(lines, code_ranges))
    return sorted(
        evidence,
        key=lambda item: (
            int(item["line_start"]),
            int(item["line_end"]),
            MODALITY_ORDER.index(str(item["modality"])),
        ),
    )


def detect_code_blocks(lines: Sequence[str]) -> Tuple[List[Evidence], List[Tuple[int, int]]]:
    """Detect fenced code blocks and return evidence plus zero-based line ranges."""
    evidence = []
    ranges = []
    in_block = False
    fence = ""
    start_index = 0
    language = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not in_block and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_block = True
            fence = stripped[:3]
            start_index = index
            language = stripped[3:].strip() or "plain text"
            continue
        if in_block and stripped.startswith(fence):
            end_index = index
            block_text = "\n".join(lines[start_index : end_index + 1])
            evidence.append(
                make_evidence(
                    "code",
                    "code_fence",
                    start_index + 1,
                    end_index + 1,
                    f"Fenced code block ({language})",
                    block_text,
                )
            )
            ranges.append((start_index, end_index))
            in_block = False

    if in_block:
        end_index = len(lines) - 1
        block_text = "\n".join(lines[start_index : end_index + 1])
        evidence.append(
            make_evidence(
                "code",
                "code_fence",
                start_index + 1,
                end_index + 1,
                f"Unclosed fenced code block ({language})",
                block_text,
            )
        )
        ranges.append((start_index, end_index))

    return evidence, ranges


def detect_tables(lines: Sequence[str], ignored_ranges: Sequence[Tuple[int, int]]) -> List[Evidence]:
    """Detect GitHub-flavored Markdown tables."""
    evidence = []
    index = 0
    while index < len(lines) - 1:
        if line_is_ignored(index, ignored_ranges):
            index += 1
            continue
        if looks_like_table_header(lines[index]) and looks_like_table_separator(lines[index + 1]):
            start = index
            end = index + 1
            cursor = index + 2
            while cursor < len(lines) and looks_like_table_row(lines[cursor]):
                end = cursor
                cursor += 1
            block_text = "\n".join(lines[start : end + 1])
            evidence.append(
                make_evidence(
                    "table",
                    "table",
                    start + 1,
                    end + 1,
                    "Markdown table with header separator",
                    block_text,
                )
            )
            index = end + 1
            continue
        index += 1
    return evidence


def detect_formulas(lines: Sequence[str], ignored_ranges: Sequence[Tuple[int, int]]) -> List[Evidence]:
    """Detect inline or display math markers in Markdown lines."""
    pattern = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+\$|\\\(.+?\\\)|\\\[.+?\\\])")
    evidence = []
    for index, line in enumerate(lines):
        if line_is_ignored(index, ignored_ranges):
            continue
        if pattern.search(line):
            evidence.append(
                make_evidence(
                    "formula",
                    "line",
                    index + 1,
                    index + 1,
                    "Inline or display math marker",
                    line,
                )
            )
    return evidence


def detect_citations(lines: Sequence[str], ignored_ranges: Sequence[Tuple[int, int]]) -> List[Evidence]:
    """Detect bracketed year citations, DOI markers, and BibTeX-style references."""
    pattern = re.compile(
        r"(\[[^\]]*\b(?:19|20)\d{2}\b[^\]]*\]|\bdoi:\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+|@[A-Za-z][\w:-]+)",
        re.IGNORECASE,
    )
    evidence = []
    for index, line in enumerate(lines):
        if line_is_ignored(index, ignored_ranges):
            continue
        if pattern.search(line):
            evidence.append(
                make_evidence(
                    "citation",
                    "line",
                    index + 1,
                    index + 1,
                    "Citation marker or DOI",
                    line,
                )
            )
    return evidence


def detect_timelines(lines: Sequence[str], ignored_ranges: Sequence[Tuple[int, int]]) -> List[Evidence]:
    """Detect explicit dates that can support temporal retrieval."""
    pattern = re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")
    evidence = []
    for index, line in enumerate(lines):
        if line_is_ignored(index, ignored_ranges):
            continue
        if pattern.search(line):
            evidence.append(
                make_evidence(
                    "timeline",
                    "line",
                    index + 1,
                    index + 1,
                    "Explicit calendar date",
                    line,
                )
            )
    return evidence


def detect_benchmarks(lines: Sequence[str], ignored_ranges: Sequence[Tuple[int, int]]) -> List[Evidence]:
    """Detect benchmark and metric language that benefits from numeric scorers."""
    pattern = re.compile(
        r"\b(benchmark|accuracy|latency|recall@?\d*|precision@?\d*|f1|auc|rmse|mae|throughput)\b",
        re.IGNORECASE,
    )
    evidence = []
    for index, line in enumerate(lines):
        if line_is_ignored(index, ignored_ranges):
            continue
        if pattern.search(line):
            evidence.append(
                make_evidence(
                    "benchmark",
                    "line",
                    index + 1,
                    index + 1,
                    "Benchmark or metric keyword",
                    line,
                )
            )
    return evidence


def recommend_scorers(tags: Iterable[str], policy: str) -> List[str]:
    """Return scorer names for detected modality tags under a routing policy."""
    selected_policy = normalize_policy(policy)
    scorers = []
    seen = set()
    for tag in tags:
        for scorer in SCORERS_BY_POLICY[selected_policy].get(tag, ()):
            if scorer not in seen:
                scorers.append(scorer)
                seen.add(scorer)
    return scorers


def make_evidence(
    modality: str,
    block_type: str,
    line_start: int,
    line_end: int,
    reason: str,
    snippet: str,
) -> Evidence:
    """Create one evidence record with a normalized snippet."""
    return {
        "modality": modality,
        "block_type": block_type,
        "line_start": line_start,
        "line_end": line_end,
        "reason": reason,
        "snippet": trim_snippet(snippet),
    }


def trim_snippet(text: str, limit: int = 140) -> str:
    """Normalize whitespace and truncate long snippets deterministically."""
    compact = " ".join(line.strip() for line in text.strip().splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def line_is_ignored(index: int, ranges: Sequence[Tuple[int, int]]) -> bool:
    """Return true when a zero-based line index falls inside an ignored range."""
    return any(start <= index <= end for start, end in ranges)


def looks_like_table_header(line: str) -> bool:
    """Return true when a line has enough pipe separators to be a table header."""
    stripped = line.strip()
    return stripped.count("|") >= 2 and not looks_like_table_separator(stripped)


def looks_like_table_separator(line: str) -> bool:
    """Return true when a line is a Markdown table alignment separator."""
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", line.strip()))


def looks_like_table_row(line: str) -> bool:
    """Return true when a line looks like a Markdown table row."""
    stripped = line.strip()
    return stripped.count("|") >= 2


def manifest_to_json(manifest: Manifest, compact: bool = False) -> str:
    """Serialize a manifest deterministically as JSON."""
    if compact:
        return json.dumps(manifest, ensure_ascii=True, separators=(",", ":")) + "\n"
    return json.dumps(manifest, ensure_ascii=True, indent=2) + "\n"


def write_manifest(manifest: Manifest, output_path: str | Path, compact: bool = False) -> None:
    """Write a manifest JSON file."""
    Path(output_path).write_text(manifest_to_json(manifest, compact=compact), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Build a modality-aware retrieval manifest from Markdown scientific notes."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        help="Markdown folder to scan. If omitted, the built-in self-test sample is emitted.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write manifest JSON to this path. Defaults to retrieval_manifest.json when scanning a folder.",
    )
    parser.add_argument(
        "--policy",
        choices=POLICIES,
        default=None,
        help="Routing policy. Defaults to MODALITYMESH_POLICY or balanced.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact single-line JSON instead of pretty-printed JSON.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample data with no API key and print the manifest.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ModalityMesh CLI."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.selftest or not args.input_dir:
            manifest = build_manifest_from_texts(SAMPLE_NOTES, policy=args.policy)
            payload = manifest_to_json(manifest, compact=args.compact)
            if args.output:
                Path(args.output).write_text(payload, encoding="utf-8")
            else:
                sys.stdout.write(payload)
            return 0

        notes = scan_markdown_directory(args.input_dir)
        manifest = build_manifest_from_texts(notes, policy=args.policy)
        output_path = args.output or "retrieval_manifest.json"
        write_manifest(manifest, output_path, compact=args.compact)
        print(f"Wrote {output_path} with {manifest['source_count']} file(s).")
        return 0
    except (OSError, ValueError) as exc:
        print(f"modalitymesh: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
