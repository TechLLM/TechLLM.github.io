#!/usr/bin/env python3
"""Nodewright reference CLI for routing Markdown evidence nodes.

The scanner converts Markdown files into deterministic JSONL evidence nodes.
It detects action-oriented affordances such as tables, code blocks, dates,
citations, links, formulas, tasks, front matter, and embedded references, then
assigns each section a retrieval role and recommended handling tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable


SAMPLE_MARKDOWN = """---
title: Quarterly Ops Note
owner: Example Team
---
# Revenue Check

As of 2026-01-15, paid seats rose from 120 to 150.

| metric | value |
| --- | ---: |
| paid_seats | 150 |
| churn_rate | 0.04 |

```python
print(150 - 120)
```

See [source](https://example.com/report) and [@doe2025].

# Launch Tasks

- [x] Draft release notes
- [ ] Verify current pricing page
"""


AFFORDANCE_ORDER = [
    "front_matter",
    "table",
    "code_block",
    "formula",
    "link",
    "citation",
    "date",
    "task",
    "embedded_reference",
    "external_state",
]


class NodewrightError(Exception):
    """Raised for user-facing CLI errors."""


@dataclass(frozen=True)
class Section:
    """A Markdown section split from a source file."""

    title: str
    anchor: str
    heading_level: int
    content: str
    start_line: int
    index: int


def parse_front_matter(text: str) -> tuple[dict[str, object], str, int]:
    """Extract a small YAML-like front matter block from Markdown text.

    The parser intentionally supports only simple `key: value` pairs and
    one-level list values. This keeps the reference implementation dependency
    free while preserving useful routing metadata.
    """

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, 0

    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        return {}, text, 0

    raw_lines = lines[1:end_index]
    metadata: dict[str, object] = {}
    current_key: str | None = None

    for raw_line in raw_lines:
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", line) and current_key:
            existing = metadata.get(current_key)
            if not isinstance(existing, list):
                existing = [] if existing in (None, "") else [existing]
            existing.append(_clean_scalar(re.sub(r"^\s+-\s+", "", line)))
            metadata[current_key] = existing
            continue
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            current_key = key.strip()
            metadata[current_key] = _clean_scalar(value.strip())

    body = "\n".join(lines[end_index + 1 :])
    return metadata, body, end_index + 1


def _clean_scalar(value: str) -> object:
    """Convert a simple front matter scalar into a stable Python value."""

    if value == "":
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_clean_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def split_sections(markdown_body: str, line_offset: int = 0) -> list[Section]:
    """Split Markdown into ATX-heading sections with stable anchors."""

    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
    matches = list(heading_re.finditer(markdown_body))
    if not matches:
        content = markdown_body.strip()
        return [
            Section(
                title="Document",
                anchor="document",
                heading_level=0,
                content=content,
                start_line=line_offset + 1,
                index=0,
            )
        ]

    sections: list[Section] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(markdown_body)
        raw_section = markdown_body[match.start() : next_start].strip()
        title = match.group(2).strip()
        title = re.sub(r"\s+#*$", "", title).strip()
        line_number = markdown_body.count("\n", 0, match.start()) + line_offset + 1
        sections.append(
            Section(
                title=title,
                anchor=slugify(title),
                heading_level=len(match.group(1)),
                content=raw_section,
                start_line=line_number,
                index=index,
            )
        )
    return sections


def slugify(value: str) -> str:
    """Create a GitHub-like lowercase heading anchor."""

    value = re.sub(r"`([^`]+)`", r"\1", value.lower())
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def detect_affordances(text: str, front_matter: dict[str, object] | None = None) -> list[str]:
    """Detect executable and routing-relevant Markdown affordances."""

    found: set[str] = set()
    if front_matter:
        found.add("front_matter")
    if has_markdown_table(text):
        found.add("table")
    if re.search(r"(?m)^(```|~~~)\s*[\w.+-]*\s*$", text):
        found.add("code_block")
    if has_formula(text):
        found.add("formula")
    if re.search(r"(?<!!)\[[^\]\n]+\]\([^)]+\)|https?://[^\s)]+", text):
        found.add("link")
    if re.search(r"\[@[A-Za-z0-9_:-]+(?:[^\]]*)\]|\[\d+\]|\[\^[^\]]+\]|\([A-Z][A-Za-z]+,\s*(?:19|20)\d{2}\)", text):
        found.add("citation")
    if re.search(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", text) or re.search(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+\d{1,2},\s+(?:19|20)\d{2}\b",
        text,
        flags=re.IGNORECASE,
    ):
        found.add("date")
    if re.search(r"(?m)^\s*[-*+]\s+\[[ xX]\]\s+\S+", text):
        found.add("task")
    if re.search(r"!\[[^\]]*\]\([^)]+\)|!?\[\[[^\]]+\]\]|\{\{[^}]+\}\}", text):
        found.add("embedded_reference")
    if re.search(
        r"\b(current|latest|today|now|live|dashboard|database|endpoint|api|external|fetch|query|as of)\b",
        text,
        flags=re.IGNORECASE,
    ):
        found.add("external_state")

    return [name for name in AFFORDANCE_ORDER if name in found]


def has_markdown_table(text: str) -> bool:
    """Return true when adjacent Markdown lines look like a pipe table."""

    lines = text.splitlines()
    separator_re = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
    for current, following in zip(lines, lines[1:]):
        if "|" in current and separator_re.match(following):
            return True
    return False


def has_formula(text: str) -> bool:
    """Detect common Markdown math blocks and simple equation lines."""

    if re.search(r"\$\$.*?\$\$", text, flags=re.DOTALL):
        return True
    if re.search(r"\\begin\{(?:equation|align|math)\}", text):
        return True
    equation_re = re.compile(r"(?m)^\s*[A-Za-z][A-Za-z0-9_()^*/+\-\s]*\s*=\s*[-+*/(). A-Za-z0-9_^]+\s*$")
    return bool(equation_re.search(text))


def detect_code_languages(text: str) -> list[str]:
    """Return fenced code block languages in first-seen order."""

    languages: list[str] = []
    for match in re.finditer(r"(?m)^(```|~~~)\s*([\w.+-]*)\s*$", text):
        language = match.group(2).strip().lower() or "plain"
        if language not in languages:
            languages.append(language)
    return languages


def route_evidence(text: str, affordances: list[str]) -> tuple[str, str, float, list[str]]:
    """Assign a retrieval role, recommended tool, confidence, and notes."""

    affordance_set = set(affordances)
    languages = detect_code_languages(text)

    if "task" in affordance_set:
        role = "execute_checklist"
        tool = "task_runner"
        notes = ["Checklist state detected; preserve item completion state during retrieval."]
    elif "code_block" in affordance_set:
        role = "run_code"
        tool = tool_for_code_languages(languages)
        notes = ["Fenced code detected; run in a sandbox before trusting generated results."]
    elif "table" in affordance_set or "formula" in affordance_set:
        role = "compute_table"
        tool = "python_sandbox"
        notes = ["Structured numeric evidence detected; parse before summarizing."]
    elif "citation" in affordance_set:
        role = "verify_claim"
        tool = "citation_checker"
        notes = ["Citation detected; verify source support before reuse."]
    elif "date" in affordance_set:
        role = "verify_claim"
        tool = "calendar_parser"
        notes = ["Dated claim detected; check freshness before reuse."]
    elif "link" in affordance_set:
        role = "follow_link"
        tool = "web_fetcher"
        notes = ["External link detected; fetch linked context when provenance matters."]
    elif "external_state" in affordance_set:
        role = "inspect_state"
        tool = "web_fetcher"
        notes = ["External or current-state language detected; inspect live state if available."]
    elif "front_matter" in affordance_set or "embedded_reference" in affordance_set:
        role = "inspect_state"
        tool = "markdown_reader"
        notes = ["Structured metadata or embedded reference detected; preserve document state."]
    else:
        role = "read_context"
        tool = "markdown_reader"
        notes = ["No executable affordance detected; read as normal context."]

    if "link" in affordance_set and role not in {"follow_link", "verify_claim"}:
        notes.append("Linked provenance is present; keep URL context attached to this node.")
    if "date" in affordance_set and role != "verify_claim":
        notes.append("Date-like text is present; consider freshness checks for time-sensitive use.")
    if "front_matter" in affordance_set:
        notes.append("Front matter keys are available in source_metadata.front_matter_keys.")

    confidence = min(0.95, 0.55 + 0.08 * len(affordances))
    if role != "read_context":
        confidence += 0.05
    confidence = min(0.98, round(confidence, 2))

    return role, tool, confidence, notes


def tool_for_code_languages(languages: list[str]) -> str:
    """Map detected code languages to a conservative execution tool."""

    if any(language in {"py", "python", "python3"} for language in languages):
        return "python_sandbox"
    if any(language in {"sql", "postgres", "postgresql", "sqlite"} for language in languages):
        return "sql_engine"
    if any(language in {"bash", "sh", "zsh", "shell"} for language in languages):
        return "shell_sandbox"
    return "python_sandbox"


def analyze_markdown_text(
    text: str,
    source_identifier: str,
    front_matter_scope: str = "first_section",
) -> list[dict[str, object]]:
    """Analyze Markdown text and return JSON-serializable evidence nodes."""

    metadata, body, offset = parse_front_matter(text)
    sections = split_sections(body, line_offset=offset)
    nodes: list[dict[str, object]] = []

    for section in sections:
        section_metadata = metadata if front_matter_scope == "all_sections" or section.index == 0 else {}
        affordances = detect_affordances(section.content, section_metadata)
        role, tool, confidence, notes = route_evidence(section.content, affordances)
        content_hash = hashlib.sha256(section.content.encode("utf-8")).hexdigest()[:16]
        node_seed = f"{source_identifier}\n{section.anchor}\n{section.index}\n{content_hash}"
        node_id = "nw_" + hashlib.sha1(node_seed.encode("utf-8")).hexdigest()[:12]
        word_count = len(re.findall(r"\b\w+\b", section.content))

        nodes.append(
            {
                "node_id": node_id,
                "source_identifier": source_identifier,
                "content_hash": content_hash,
                "section_anchor": section.anchor,
                "section_title": section.title,
                "affordances": affordances,
                "retrieval_role": role,
                "recommended_tool": tool,
                "confidence": confidence,
                "routing_notes": notes,
                "source_metadata": {
                    "source_path": source_identifier,
                    "section_index": section.index,
                    "start_line": section.start_line,
                    "heading_level": section.heading_level,
                    "front_matter_keys": sorted(section_metadata.keys()),
                    "char_count": len(section.content),
                    "word_count": word_count,
                },
            }
        )

    return nodes


def iter_markdown_files(input_path: Path) -> Iterable[Path]:
    """Yield Markdown files from a file or directory in deterministic order."""

    if not input_path.exists():
        raise NodewrightError(f"input path does not exist: {input_path}")
    if input_path.is_file():
        if input_path.suffix.lower() not in {".md", ".markdown"}:
            raise NodewrightError(f"input file is not Markdown: {input_path}")
        yield input_path
        return
    if not input_path.is_dir():
        raise NodewrightError(f"input path is neither a file nor a directory: {input_path}")

    files = sorted(
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".markdown"}
    )
    if not files:
        raise NodewrightError(f"no Markdown files found under: {input_path}")
    yield from files


def scan_markdown_path(input_path: Path) -> list[dict[str, object]]:
    """Scan a Markdown file or folder and return evidence nodes."""

    nodes: list[dict[str, object]] = []
    input_path = input_path.expanduser()
    base = input_path if input_path.is_dir() else input_path.parent

    for markdown_file in iter_markdown_files(input_path):
        try:
            text = markdown_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise NodewrightError(f"could not read UTF-8 Markdown file: {markdown_file}") from exc

        source_identifier = markdown_file.relative_to(base).as_posix()
        if source_identifier == ".":
            source_identifier = markdown_file.name
        nodes.extend(analyze_markdown_text(text, source_identifier=source_identifier))

    return nodes


def format_jsonl(nodes: list[dict[str, object]]) -> str:
    """Serialize nodes as deterministic line-delimited JSON."""

    return "\n".join(json.dumps(node, ensure_ascii=True, separators=(",", ":")) for node in nodes) + "\n"


def write_or_print(jsonl: str, output_path: Path | None) -> None:
    """Write JSONL to a file or print it to stdout."""

    if output_path is None:
        sys.stdout.write(jsonl)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(jsonl, encoding="utf-8")


def read_env_options() -> dict[str, str | None]:
    """Read optional environment configuration without exposing secrets."""

    return {
        "api_key_present": "yes" if os.environ.get("NODEWRIGHT_API_KEY") else "no",
        "llm_provider": os.environ.get("NODEWRIGHT_LLM_PROVIDER"),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Scan Markdown files and emit Nodewright evidence-routing JSONL."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Markdown file or directory to scan. If omitted, --selftest behavior is used.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output JSONL path. Defaults to stdout.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run on built-in sample Markdown with no API key or network access.",
    )
    parser.add_argument(
        "--llm-refine",
        action="store_true",
        help="Reserved for external refinement; this self-contained implementation exits with a clear error.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Nodewright CLI and return a process exit code."""

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["--selftest"]

    parser = build_parser()
    args = parser.parse_args(argv)
    read_env_options()

    if args.llm_refine:
        raise NodewrightError(
            "LLM refinement is not available in this self-contained reference CLI; "
            "unset --llm-refine and use deterministic routing."
        )
    if args.selftest and args.input:
        raise NodewrightError("--selftest cannot be combined with --input")

    if args.selftest or not args.input:
        nodes = analyze_markdown_text(SAMPLE_MARKDOWN, source_identifier="sample.md")
    else:
        nodes = scan_markdown_path(args.input)

    write_or_print(format_jsonl(nodes), args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NodewrightError as exc:
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(2)
