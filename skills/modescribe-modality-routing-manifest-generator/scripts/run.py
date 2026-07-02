#!/usr/bin/env python3
"""ModeScribe reference runner.

Analyze Markdown notes and generate routing metadata for AI agent pipelines.
The implementation is intentionally small, deterministic, and standard-library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


MODALITY_ORDER = ["text", "table", "code", "math", "citation", "benchmark", "log", "mixed"]

DEFAULT_POLICY = {
    "text": "prose_retriever",
    "table": "table_parser",
    "code": "code_indexer",
    "math": "math_parser",
    "citation": "citation_graph",
    "benchmark": "benchmark_scorer",
    "log": "log_sequence_parser",
    "mixed": "mixed_modality_router",
}

SAMPLE_MARKDOWN = """# Sample Routing Note

This built-in sample is used when no input path is provided.
It mentions MMLU and HumanEval as benchmark signals [@sample2026].

| Item | Score |
| --- | ---: |
| baseline | 0.62 |
| routed | 0.71 |

```python
print("route me")
```

$$
score = alpha + beta
$$

2026-01-01T00:00:00Z INFO sample started
2026-01-01T00:00:01Z INFO sample completed
"""

FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*([\w.+-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
MATH_BLOCK_RE = re.compile(r"^\s*(\$\$|\\\[|\\begin\{(?:equation|align|gather|multline)\*?\})")
INLINE_MATH_RE = re.compile(r"(?<!\$)\$[^$\n]{2,}\$(?!\$)|\\\([^)\n]{2,}\\\)")
CITATION_RE = re.compile(
    r"(\[@[\w:.-]+\]|\[[A-Z][^\]]+? et al\.?,?\s+\d{4}[^\]]*\]|\[\s*\d+(?:\s*,\s*\d+)*\s*\]|"
    r"\b(?:doi|DOI):\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+|\barXiv:\s*\d{4}\.\d{4,5})"
)
BENCHMARK_RE = re.compile(
    r"\b(MMLU|GSM8K|HumanEval|SWE-bench|GLUE|SuperGLUE|ImageNet|COCO|SQuAD|HellaSwag|"
    r"TruthfulQA|ARC|BIG-bench|BLEU|ROUGE|F1|leaderboard|benchmark|dataset)\b",
    re.IGNORECASE,
)
LOG_RE = re.compile(
    r"^\s*(?:\d{4}-\d{2}-\d{2}[T ][0-9:.+-]*Z?\s+)?"
    r"(?:TRACE|DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL)\b|"
    r"^\s*(?:epoch|step|iteration)\s+\d+(?:\s*/\s*\d+)?\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Markdown modality structure and write a routing manifest."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=os.getenv("MODESCRIBE_INPUT"),
        help="Markdown file or directory. Defaults to examples/sample-note.md or an in-memory sample.",
    )
    parser.add_argument(
        "--out",
        default=os.getenv("MODESCRIBE_OUTPUT", "routing-manifest.json"),
        help="Manifest output path.",
    )
    parser.add_argument(
        "--patches",
        default=os.getenv("MODESCRIBE_PATCHES", "frontmatter-patches.json"),
        help="Frontmatter suggestion output path.",
    )
    parser.add_argument(
        "--policy",
        default=os.getenv("MODESCRIBE_POLICY_FILE"),
        help="Optional JSON file mapping modalities to route node names.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=float(os.getenv("MODESCRIBE_MIN_CONFIDENCE", "0.30")),
        help="Drop modalities below this confidence.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print manifest JSON to stdout.")
    return parser.parse_args()


def load_policy(path: str | None) -> dict[str, str]:
    policy = dict(DEFAULT_POLICY)
    if not path:
        return policy
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Could not read policy file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Policy file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Policy file must be a JSON object.")
    for key, value in data.items():
        if key in MODALITY_ORDER and isinstance(value, str) and value.strip():
            policy[key] = value.strip()
    return policy


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def collect_sources(input_arg: str | None) -> list[dict[str, Any]]:
    if not input_arg:
        example = Path("examples/sample-note.md")
        if example.exists():
            return [{"path": display_path(example), "text": example.read_text(encoding="utf-8"), "sample": True}]
        return [{"path": "sample-note.md", "text": SAMPLE_MARKDOWN, "sample": True}]

    root = Path(input_arg)
    if not root.exists():
        raise SystemExit(f"Input path does not exist: {input_arg}")

    if root.is_file():
        return [{"path": display_path(root), "text": root.read_text(encoding="utf-8"), "sample": False}]

    files = sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".md", ".markdown", ".mdown"}
    )
    if not files:
        raise SystemExit(f"No Markdown files found under: {input_arg}")
    return [{"path": display_path(p), "text": p.read_text(encoding="utf-8"), "sample": False} for p in files]


def content_start_line(lines: list[str]) -> int:
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return index + 1
    return 0


def parse_blocks(lines: list[str], start_line: int) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        absolute = start_line + i

        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            language = fence_match.group(2) or ""
            close_index = i + 1
            while close_index < len(lines) and not lines[close_index].lstrip().startswith(marker[:3]):
                close_index += 1
            end_index = min(close_index, len(lines) - 1)
            text = "\n".join(lines[i : end_index + 1])
            blocks.append(
                {
                    "type": "fenced_code",
                    "start": absolute,
                    "end": start_line + end_index,
                    "language": language,
                    "text": text,
                }
            )
            i = end_index + 1
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            blocks.append(
                {
                    "type": "heading",
                    "start": absolute,
                    "end": absolute,
                    "level": len(heading_match.group(1)),
                    "title": heading_match.group(2).strip(),
                    "text": line,
                }
            )
            i += 1
            continue

        if MATH_BLOCK_RE.match(line):
            end_index = i
            if line.strip().startswith("$$"):
                end_index = i + 1
                while end_index < len(lines) and not lines[end_index].strip().endswith("$$"):
                    end_index += 1
            elif "\\]" not in line and "\\end{" not in line:
                end_index = i + 1
                while end_index < len(lines) and "\\]" not in lines[end_index] and "\\end{" not in lines[end_index]:
                    end_index += 1
            end_index = min(end_index, len(lines) - 1)
            blocks.append(
                {
                    "type": "math_block",
                    "start": absolute,
                    "end": start_line + end_index,
                    "text": "\n".join(lines[i : end_index + 1]),
                }
            )
            i = end_index + 1
            continue

        if "|" in line and i + 1 < len(lines) and TABLE_SEPARATOR_RE.match(lines[i + 1]):
            end_index = i + 2
            while end_index < len(lines) and "|" in lines[end_index].strip():
                end_index += 1
            text = "\n".join(lines[i:end_index])
            blocks.append(
                {
                    "type": "table",
                    "start": absolute,
                    "end": start_line + end_index - 1,
                    "rows": max(0, end_index - i - 2),
                    "columns": max(1, line.count("|") - 1),
                    "text": text,
                }
            )
            i = end_index
            continue

        if not line.strip():
            i += 1
            continue

        start_index = i
        parts = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                break
            if FENCE_RE.match(next_line) or HEADING_RE.match(next_line) or MATH_BLOCK_RE.match(next_line):
                break
            if "|" in next_line and i + 1 < len(lines) and TABLE_SEPARATOR_RE.match(lines[i + 1]):
                break
            parts.append(next_line)
            i += 1
        blocks.append(
            {
                "type": "paragraph",
                "start": start_line + start_index,
                "end": start_line + i - 1,
                "text": "\n".join(parts),
            }
        )

    return blocks


def snippet(text: str, limit: int = 120) -> str:
    compact = " ".join(text.strip().split())
    return compact[: limit - 1] + "..." if len(compact) > limit else compact


def evidence(node: dict[str, Any], kind: str, detail: str | None = None) -> dict[str, Any]:
    item = {
        "line_start": node["start"],
        "line_end": node["end"],
        "kind": kind,
        "snippet": snippet(node.get("text", "")),
    }
    if detail:
        item["detail"] = detail
    return item


def add_line_evidence(
    bucket: dict[str, list[dict[str, Any]]],
    modality: str,
    line_no: int,
    line: str,
    kind: str,
) -> None:
    bucket.setdefault(modality, []).append(
        {"line_start": line_no, "line_end": line_no, "kind": kind, "snippet": snippet(line)}
    )


def analyze_blocks(
    blocks: list[dict[str, Any]],
    raw_lines: list[str],
    min_confidence: float,
    raw_start_line: int = 1,
) -> dict[str, Any]:
    evidence_by_modality: dict[str, list[dict[str, Any]]] = {name: [] for name in MODALITY_ORDER}

    paragraph_words = 0
    paragraph_count = 0
    for block in blocks:
        block_type = block["type"]
        if block_type == "paragraph":
            words = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]*\b", block["text"])
            if len(words) >= 8:
                paragraph_count += 1
                paragraph_words += len(words)
                evidence_by_modality["text"].append(evidence(block, "prose paragraph"))
        elif block_type == "heading":
            evidence_by_modality["text"].append(evidence(block, "heading"))
        elif block_type == "table":
            detail = f"{block.get('rows', 0)} data rows, {block.get('columns', 0)} columns"
            evidence_by_modality["table"].append(evidence(block, "markdown table", detail))
        elif block_type == "fenced_code":
            language = block.get("language") or "unknown"
            evidence_by_modality["code"].append(evidence(block, "fenced code block", f"language={language}"))
        elif block_type == "math_block":
            evidence_by_modality["math"].append(evidence(block, "display math"))

    code_ranges = [(block["start"], block["end"]) for block in blocks if block["type"] == "fenced_code"]

    def inside_code(line_no: int) -> bool:
        return any(start <= line_no <= end for start, end in code_ranges)

    for line_no, line in enumerate(raw_lines, start=raw_start_line):
        if inside_code(line_no):
            continue
        if INLINE_MATH_RE.search(line):
            add_line_evidence(evidence_by_modality, "math", line_no, line, "inline math")
        if CITATION_RE.search(line):
            add_line_evidence(evidence_by_modality, "citation", line_no, line, "citation pattern")
        if BENCHMARK_RE.search(line):
            add_line_evidence(evidence_by_modality, "benchmark", line_no, line, "benchmark keyword")
        if LOG_RE.search(line):
            add_line_evidence(evidence_by_modality, "log", line_no, line, "log-like line")

    confidence = {
        "text": min(0.95, 0.45 + paragraph_count * 0.08 + min(paragraph_words, 200) / 1000),
        "table": min(0.98, 0.72 + 0.08 * len(evidence_by_modality["table"])),
        "code": min(0.99, 0.78 + 0.07 * len(evidence_by_modality["code"])),
        "math": min(0.98, 0.62 + 0.08 * len(evidence_by_modality["math"])),
        "citation": min(0.97, 0.50 + 0.08 * len(evidence_by_modality["citation"])),
        "benchmark": min(0.97, 0.48 + 0.08 * len(evidence_by_modality["benchmark"])),
        "log": min(0.96, 0.40 + 0.10 * len(evidence_by_modality["log"])),
    }

    # One isolated log-looking line is often prose, so require a small sequence.
    if len(evidence_by_modality["log"]) < 2:
        evidence_by_modality["log"] = []
        confidence["log"] = 0.0

    modalities = [
        name
        for name in MODALITY_ORDER
        if name != "mixed" and evidence_by_modality.get(name) and confidence.get(name, 0.0) >= min_confidence
    ]

    if len(modalities) >= 3 or (len([m for m in modalities if m != "text"]) >= 2 and "text" in modalities):
        confidence["mixed"] = min(0.97, 0.50 + 0.06 * len(modalities))
        evidence_by_modality["mixed"] = [
            {
                "line_start": min(item["line_start"] for name in modalities for item in evidence_by_modality[name]),
                "line_end": max(item["line_end"] for name in modalities for item in evidence_by_modality[name]),
                "kind": "mixed modality note",
                "snippet": ", ".join(modalities),
            }
        ]
        modalities.append("mixed")

    return {
        "modalities": sort_modalities(modalities),
        "confidence": {name: round(confidence[name], 2) for name in sort_modalities(modalities)},
        "evidence": {
            name: evidence_by_modality[name][:5]
            for name in sort_modalities(modalities)
            if evidence_by_modality.get(name)
        },
    }


def sort_modalities(values: list[str]) -> list[str]:
    order = {name: index for index, name in enumerate(MODALITY_ORDER)}
    return sorted(dict.fromkeys(values), key=lambda item: order.get(item, 99))


def section_bounds(lines: list[str], blocks: list[dict[str, Any]], content_start: int) -> list[dict[str, Any]]:
    headings = [block for block in blocks if block["type"] == "heading"]
    last_line = len(lines)
    sections: list[dict[str, Any]] = []

    if headings and content_start + 1 < headings[0]["start"]:
        sections.append({"title": "Preamble", "start": content_start + 1, "end": headings[0]["start"] - 1})

    for index, heading in enumerate(headings):
        next_start = headings[index + 1]["start"] if index + 1 < len(headings) else last_line + 1
        sections.append(
            {
                "title": heading["title"],
                "heading_level": heading["level"],
                "start": heading["start"],
                "end": max(heading["start"], next_start - 1),
            }
        )

    if not sections and lines:
        sections.append({"title": "Document", "start": content_start + 1, "end": last_line})

    return [section for section in sections if section["start"] <= section["end"]]


def analyze_note(source: dict[str, Any], policy: dict[str, str], min_confidence: float) -> dict[str, Any]:
    text = source["text"]
    lines = text.splitlines()
    start = content_start_line(lines)
    content_lines = lines[start:]
    blocks = parse_blocks(content_lines, start + 1)
    note_analysis = analyze_blocks(blocks, lines, min_confidence)

    sections = []
    for bounds in section_bounds(lines, blocks, start):
        section_lines = lines[bounds["start"] - 1 : bounds["end"]]
        section_blocks = parse_blocks(section_lines, bounds["start"])
        section_analysis = analyze_blocks(section_blocks, section_lines, min_confidence, bounds["start"])
        if not section_analysis["modalities"]:
            continue
        sections.append(
            {
                "title": bounds["title"],
                "line_start": bounds["start"],
                "line_end": bounds["end"],
                "modalities": section_analysis["modalities"],
                "confidence": section_analysis["confidence"],
                "routes": routes_for(section_analysis["modalities"], policy),
                "evidence": section_analysis["evidence"],
            }
        )

    note_id = hashlib.sha1((source["path"] + "\n" + text).encode("utf-8")).hexdigest()[:12]
    return {
        "id": note_id,
        "path": source["path"],
        "source": "sample" if source.get("sample") else "input",
        "modalities": note_analysis["modalities"],
        "confidence": note_analysis["confidence"],
        "routes": routes_for(note_analysis["modalities"], policy),
        "evidence": note_analysis["evidence"],
        "sections": sections,
    }


def routes_for(modalities: list[str], policy: dict[str, str]) -> dict[str, str]:
    return {name: policy.get(name, f"{name}_processor") for name in modalities}


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def yaml_dump(value: Any, indent: int = 0) -> list[str]:
    spaces = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                lines.append(f"{spaces}{key}:")
                lines.extend(yaml_dump(nested, indent + 2))
            else:
                lines.append(f"{spaces}{key}: {yaml_scalar(nested)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{spaces}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}-")
                lines.extend(yaml_dump(item, indent + 2))
            else:
                lines.append(f"{spaces}- {yaml_scalar(item)}")
        return lines
    return [f"{spaces}{yaml_scalar(value)}"]


def frontmatter_suggestions(notes: list[dict[str, Any]]) -> dict[str, Any]:
    suggestions = []
    for note in notes:
        metadata = {
            "modescribe_modalities": note["modalities"],
            "modescribe_routes": note["routes"],
            "modescribe_confidence": note["confidence"],
        }
        preview = "---\n" + "\n".join(yaml_dump(metadata)) + "\n---"
        suggestions.append(
            {
                "path": note["path"],
                "operation": "review_and_merge_frontmatter",
                "suggested_frontmatter": metadata,
                "patch_preview": preview,
            }
        )
    return {
        "schema_version": "0.1.0",
        "note_count": len(notes),
        "suggestions": suggestions,
    }


def build_manifest(notes: list[dict[str, Any]], policy: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "generator": "modescribe-reference",
        "deterministic": True,
        "external_models": False,
        "api_key_configured": bool(os.getenv("MODESCRIBE_API_KEY")),
        "policy": policy,
        "note_count": len(notes),
        "notes": notes,
    }


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    policy = load_policy(args.policy)
    sources = collect_sources(args.input)
    notes = [analyze_note(source, policy, args.min_confidence) for source in sources]
    manifest = build_manifest(notes, policy)
    patches = frontmatter_suggestions(notes)

    write_json(args.out, manifest)
    write_json(args.patches, patches)

    if args.stdout:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(f"Wrote {args.out}")
        print(f"Wrote {args.patches}")
        print(f"Analyzed {len(notes)} Markdown note(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
