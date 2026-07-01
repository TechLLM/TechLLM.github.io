#!/usr/bin/env python3
"""TraceVault reference grader for Markdown knowledge-base tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WIKI_LINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


@dataclass
class Note:
    path: str
    text: str
    digest: str
    frontmatter: dict[str, Any]
    links: set[str]


def normalize_path(value: str) -> str:
    value = value.strip().replace("\\", "/")
    value = value.split("#", 1)[0]
    if value.startswith("./"):
        value = value[2:]
    while "//" in value:
        value = value.replace("//", "/")
    return value.strip("/")


def strip_md_extension(value: str) -> str:
    return value[:-3] if value.endswith(".md") else value


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_simple_yaml(text: str) -> Any:
    """Parse the small YAML subset used by TraceVault expectation files."""

    lines = [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    index = 0

    def parse_block(indent: int) -> Any:
        nonlocal index
        if index >= len(lines):
            return {}

        current = lines[index]
        current_indent = len(current) - len(current.lstrip(" "))
        if current_indent < indent:
            return {}

        if current.lstrip().startswith("- "):
            items: list[Any] = []
            while index < len(lines):
                line = lines[index]
                line_indent = len(line) - len(line.lstrip(" "))
                stripped = line.strip()
                if line_indent != indent or not stripped.startswith("- "):
                    break
                item_text = stripped[2:].strip()
                index += 1
                if not item_text:
                    items.append(parse_block(indent + 2))
                elif ": " in item_text or item_text.endswith(":"):
                    item: dict[str, Any] = {}
                    key, _, raw = item_text.partition(":")
                    item[key.strip()] = (
                        parse_scalar(raw) if raw.strip() else parse_block(indent + 2)
                    )
                    while index < len(lines):
                        peek = lines[index]
                        peek_indent = len(peek) - len(peek.lstrip(" "))
                        if peek_indent < indent + 2:
                            break
                        if peek_indent == indent and peek.strip().startswith("- "):
                            break
                        if peek_indent != indent + 2:
                            break
                        child = peek.strip()
                        if ":" not in child:
                            break
                        child_key, _, child_raw = child.partition(":")
                        index += 1
                        item[child_key.strip()] = (
                            parse_scalar(child_raw)
                            if child_raw.strip()
                            else parse_block(indent + 4)
                        )
                    items.append(item)
                else:
                    items.append(parse_scalar(item_text))
            return items

        mapping: dict[str, Any] = {}
        while index < len(lines):
            line = lines[index]
            line_indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            if line_indent != indent or stripped.startswith("- "):
                break
            if ":" not in stripped:
                raise ValueError(f"Invalid YAML line: {line}")
            key, _, raw = stripped.partition(":")
            index += 1
            mapping[key.strip()] = (
                parse_scalar(raw) if raw.strip() else parse_block(indent + 2)
            )
        return mapping

    return parse_block(0)


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            raw = "\n".join(lines[1:idx])
            parsed = parse_simple_yaml(raw)
            return parsed if isinstance(parsed, dict) else {}
    return {}


def resolve_link(source_path: str, target: str, known_paths: set[str]) -> str:
    target = normalize_path(target)
    if not target:
        return target
    if target.startswith(("http://", "https://", "mailto:")):
        return target

    candidates = []
    if target.endswith(".md"):
        candidates.append(target)
    else:
        candidates.append(f"{target}.md")
        candidates.append(target)

    source_dir = str(Path(source_path).parent).replace("\\", "/")
    for candidate in candidates:
        if candidate in known_paths:
            return candidate
        joined = normalize_path(f"{source_dir}/{candidate}") if source_dir != "." else candidate
        if joined in known_paths:
            return joined

    if target.endswith(".md"):
        return target
    return f"{target}.md"


def extract_links(path: str, text: str, known_paths: set[str]) -> set[str]:
    links: set[str] = set()
    for match in WIKI_LINK_RE.finditer(text):
        links.add(resolve_link(path, match.group(1), known_paths))
    for match in MARKDOWN_LINK_RE.finditer(text):
        raw_target = match.group(1).strip()
        if raw_target.startswith(("http://", "https://", "mailto:")):
            links.add(raw_target)
        else:
            links.add(resolve_link(path, raw_target, known_paths))
    return links


def read_vault(root: Path) -> dict[str, Note]:
    files: dict[str, str] = {}
    for file_path in root.rglob("*.md"):
        if any(part.startswith(".") for part in file_path.relative_to(root).parts):
            continue
        rel = file_path.relative_to(root).as_posix()
        files[rel] = file_path.read_text(encoding="utf-8")

    known_paths = set(files)
    notes: dict[str, Note] = {}
    for rel, text in files.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        notes[rel] = Note(
            path=rel,
            text=text,
            digest=digest,
            frontmatter=parse_frontmatter(text),
            links=extract_links(rel, text, known_paths),
        )
    return notes


def note_from_text(path: str, text: str, known_paths: set[str]) -> Note:
    return Note(
        path=path,
        text=text,
        digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        frontmatter=parse_frontmatter(text),
        links=extract_links(path, text, known_paths),
    )


def built_in_case() -> tuple[dict[str, Note], dict[str, Note], dict[str, Any]]:
    before_texts = {
        "notes/index.md": "# Index\n\n- [[source]]\n",
        "notes/source.md": "---\ntags: [source]\n---\n# Source\n\nEvidence about agent grading.\n",
    }
    after_texts = {
        "notes/index.md": "# Index\n\n- [[source]]\n- [[agent-evaluation]]\n",
        "notes/source.md": "---\ntags: [source]\n---\n# Source\n\nEvidence about agent grading.\n",
        "notes/agent-evaluation.md": (
            "---\n"
            "status: reviewed\n"
            "tags:\n"
            "  - benchmark\n"
            "aliases: [Knowledge Agent QA]\n"
            "---\n"
            "# Agent Evaluation\n\n"
            "This note cites [[source]] and links back to [the index](index.md).\n"
        ),
    }
    known_after = set(after_texts)
    before = {
        path: note_from_text(path, text, set(before_texts))
        for path, text in before_texts.items()
    }
    after = {
        path: note_from_text(path, text, known_after)
        for path, text in after_texts.items()
    }
    expectations = {
        "created_files": ["notes/agent-evaluation.md"],
        "modified_files": ["notes/index.md"],
        "forbidden_edits": ["notes/source.md"],
        "required_links": [
            {"from": "notes/agent-evaluation.md", "to": "notes/source.md"},
            {"from": "notes/agent-evaluation.md", "to": "notes/index.md"},
        ],
        "required_citations": [
            {"file": "notes/agent-evaluation.md", "contains": "[[source]]"}
        ],
        "frontmatter": {
            "notes/agent-evaluation.md": {
                "status": "reviewed",
                "tags": {"contains": ["benchmark"]},
                "aliases": {"contains": ["Knowledge Agent QA"]},
            }
        },
    }
    return before, after, expectations


def load_expectations(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    parsed = parse_simple_yaml(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Expectation file must contain a YAML mapping.")
    return parsed


def check(condition: bool, name: str, evidence: Any, failures: list[dict[str, Any]]) -> None:
    if not condition:
        failures.append({"check": name, "evidence": evidence})


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def grade(
    before: dict[str, Note], after: dict[str, Note], expectations: dict[str, Any]
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "created_files": sorted(set(after) - set(before)),
        "deleted_files": sorted(set(before) - set(after)),
        "modified_files": sorted(
            path for path in set(before) & set(after) if before[path].digest != after[path].digest
        ),
        "all_after_files": sorted(after),
    }

    for path in as_list(expectations.get("created_files")):
        normalized = normalize_path(str(path))
        check(
            normalized in after and normalized not in before,
            "created_file",
            {"expected": normalized, "actual_created": evidence["created_files"]},
            failures,
        )

    for path in as_list(expectations.get("modified_files")):
        normalized = normalize_path(str(path))
        modified = (
            normalized in before
            and normalized in after
            and before[normalized].digest != after[normalized].digest
        )
        check(
            modified,
            "modified_file",
            {"expected": normalized, "actual_modified": evidence["modified_files"]},
            failures,
        )

    for path in as_list(expectations.get("forbidden_edits")):
        normalized = normalize_path(str(path))
        unchanged = normalized in before and normalized in after and (
            before[normalized].digest == after[normalized].digest
        )
        check(
            unchanged,
            "forbidden_edit",
            {"expected_unchanged": normalized, "actual_modified": evidence["modified_files"]},
            failures,
        )

    link_evidence: list[dict[str, Any]] = []
    for item in as_list(expectations.get("required_links")):
        if not isinstance(item, dict):
            failures.append({"check": "required_link", "evidence": {"invalid": item}})
            continue
        source = normalize_path(str(item.get("from", "")))
        target = normalize_path(str(item.get("to", "")))
        resolved_target = resolve_link(source, target, set(after))
        actual_links = sorted(after[source].links) if source in after else []
        link_evidence.append(
            {"from": source, "to": resolved_target, "actual_links": actual_links}
        )
        check(
            source in after and resolved_target in after[source].links,
            "required_link",
            {"from": source, "to": resolved_target, "actual_links": actual_links},
            failures,
        )
    evidence["required_links"] = link_evidence

    citation_evidence: list[dict[str, Any]] = []
    for item in as_list(expectations.get("required_citations")):
        if not isinstance(item, dict):
            failures.append({"check": "required_citation", "evidence": {"invalid": item}})
            continue
        source = normalize_path(str(item.get("file", "")))
        needle = str(item.get("contains", ""))
        found = source in after and needle in after[source].text
        citation_evidence.append({"file": source, "contains": needle, "found": found})
        check(
            found,
            "required_citation",
            {"file": source, "contains": needle},
            failures,
        )
    evidence["required_citations"] = citation_evidence

    frontmatter_evidence: dict[str, Any] = {}
    expected_frontmatter = expectations.get("frontmatter", {})
    if isinstance(expected_frontmatter, dict):
        for raw_path, rules in expected_frontmatter.items():
            path = normalize_path(str(raw_path))
            actual = after[path].frontmatter if path in after else {}
            frontmatter_evidence[path] = actual
            if not isinstance(rules, dict):
                failures.append(
                    {"check": "frontmatter", "evidence": {"file": path, "invalid": rules}}
                )
                continue
            for key, expected in rules.items():
                actual_value = actual.get(key)
                if isinstance(expected, dict) and "contains" in expected:
                    required_values = as_list(expected["contains"])
                    actual_values = actual_value if isinstance(actual_value, list) else [actual_value]
                    missing = [value for value in required_values if value not in actual_values]
                    check(
                        not missing,
                        "frontmatter_contains",
                        {
                            "file": path,
                            "field": key,
                            "missing": missing,
                            "actual": actual_value,
                        },
                        failures,
                    )
                else:
                    check(
                        actual_value == expected,
                        "frontmatter_equals",
                        {
                            "file": path,
                            "field": key,
                            "expected": expected,
                            "actual": actual_value,
                        },
                        failures,
                    )
    evidence["frontmatter"] = frontmatter_evidence

    return {
        "tool": "tracevault-kb-task-grader",
        "version": "0.1.0",
        "mode": "local",
        "api_key_present": bool(os.environ.get("TRACEVAULT_API_KEY")),
        "passed": not failures,
        "summary": {
            "checks_failed": len(failures),
            "files_before": len(before),
            "files_after": len(after),
        },
        "failures": failures,
        "evidence": evidence,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade Markdown knowledge-base task evidence from before/after snapshots."
    )
    parser.add_argument("--before", type=Path, help="Directory containing the before vault.")
    parser.add_argument("--after", type=Path, help="Directory containing the after vault.")
    parser.add_argument(
        "--expectations", type=Path, help="YAML expectation file for required evidence."
    )
    parser.add_argument("--out", type=Path, help="Optional JSON output file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    using_files = bool(args.before or args.after or args.expectations)

    if using_files and not (args.before and args.after and args.expectations):
        print(
            "error: --before, --after, and --expectations must be provided together",
            file=sys.stderr,
        )
        return 2

    try:
        if using_files:
            before = read_vault(args.before)
            after = read_vault(args.after)
            expectations = load_expectations(args.expectations)
        else:
            before, after, expectations = built_in_case()

        report = grade(before, after, expectations)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    output = json.dumps(report, indent=indent, sort_keys=True)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
