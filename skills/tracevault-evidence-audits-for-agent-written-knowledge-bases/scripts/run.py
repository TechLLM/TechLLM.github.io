#!/usr/bin/env python3
"""TraceVault: local evidence audits for Markdown knowledge-base changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import unquote


VERSION = "0.1.0"
WIKILINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
MDLINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]{0,80}):\s*(.+?)\s*$")


@dataclass
class Link:
    raw: str
    target: str
    anchor: str
    kind: str


@dataclass
class Note:
    path: str
    sha256: str
    text: str
    frontmatter: Dict[str, Any]
    headings: List[str]
    fields: Dict[str, str]
    links: List[Link]


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def strip_yaml_comment(line: str) -> str:
    quote: Optional[str] = None
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
            continue
        if char == "#" and quote is None and (idx == 0 or line[idx - 1].isspace()):
            return line[:idx].rstrip()
    return line.rstrip()


def load_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a deliberately small YAML subset used by TraceVault examples."""

    raw_lines: List[Tuple[int, str]] = []
    for original in text.splitlines():
        without_comment = strip_yaml_comment(original)
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        raw_lines.append((indent, without_comment.strip()))

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if index >= len(raw_lines):
            return {}, index
        is_list = raw_lines[index][1].startswith("- ")
        container: Any = [] if is_list else {}
        while index < len(raw_lines):
            line_indent, content = raw_lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise ValueError(f"Unexpected indentation near: {content}")
            if is_list:
                if not content.startswith("- "):
                    break
                item = content[2:].strip()
                if not item:
                    nested, index = parse_block(index + 1, indent + 2)
                    container.append(nested)
                elif ":" in item and not item.startswith(("'", '"')):
                    key, value = item.split(":", 1)
                    item_map: Dict[str, Any] = {key.strip(): parse_scalar(value)}
                    container.append(item_map)
                    index += 1
                else:
                    container.append(parse_scalar(item))
                    index += 1
            else:
                if content.startswith("- "):
                    break
                if ":" not in content:
                    raise ValueError(f"Expected key/value YAML near: {content}")
                key, rest = content.split(":", 1)
                key = key.strip()
                rest = rest.strip()
                if rest:
                    container[key] = parse_scalar(rest)
                    index += 1
                else:
                    if index + 1 < len(raw_lines) and raw_lines[index + 1][0] > indent:
                        nested, index = parse_block(index + 1, raw_lines[index + 1][0])
                        container[key] = nested
                    else:
                        container[key] = None
                        index += 1
        return container, index

    parsed, end_index = parse_block(0, raw_lines[0][0] if raw_lines else 0)
    if end_index != len(raw_lines):
        raise ValueError("Could not parse the complete YAML document.")
    if not isinstance(parsed, dict):
        raise ValueError("Top-level audit specification must be a mapping.")
    return parsed


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end].strip()
    body_start = text.find("\n", end + 4)
    body = text[body_start + 1 :] if body_start != -1 else ""
    try:
        parsed = load_simple_yaml(block) if block else {}
        return parsed, body
    except ValueError:
        return {}, body


def posix_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_link(raw: str) -> Tuple[str, str]:
    cleaned = raw.split("|", 1)[0].strip()
    cleaned = unquote(cleaned)
    if "#" in cleaned:
        target, anchor = cleaned.split("#", 1)
        return target.strip(), anchor.strip()
    return cleaned.strip(), ""


def extract_links(text: str) -> List[Link]:
    links: List[Link] = []
    for match in WIKILINK_RE.finditer(text):
        target, anchor = normalize_link(match.group(1))
        links.append(Link(raw=match.group(1), target=target, anchor=anchor, kind="wikilink"))
    for match in MDLINK_RE.finditer(text):
        raw = match.group(1).strip()
        if re.match(r"^[a-z]+:", raw, flags=re.IGNORECASE):
            continue
        target, anchor = normalize_link(raw)
        links.append(Link(raw=raw, target=target, anchor=anchor, kind="markdown"))
    return links


def extract_headings(text: str) -> List[str]:
    headings: List[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def extract_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            fields[match.group(1).strip().lower()] = match.group(2).strip()
    return fields


def read_note(path: Path, root: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    return Note(
        path=posix_rel(path, root),
        sha256=hash_text(text),
        text=text,
        frontmatter=frontmatter,
        headings=extract_headings(body),
        fields=extract_fields(body),
        links=extract_links(body),
    )


def snapshot_vault(root: Path) -> Dict[str, Note]:
    if not root.exists():
        raise FileNotFoundError(f"Vault directory not found: {root}")
    notes: Dict[str, Note] = {}
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        notes[posix_rel(path, root)] = read_note(path, root)
    return notes


def slugify_heading(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"[^\w\s-]", "", lowered)
    lowered = re.sub(r"\s+", "-", lowered)
    return lowered.strip("-")


def resolve_link(
    source_path: str, link: Link, notes: Dict[str, Note]
) -> Tuple[Optional[str], str]:
    if not link.target:
        target_path = source_path
    else:
        target = link.target.strip().lstrip("./")
        candidates: List[str] = []
        if target.endswith(".md"):
            candidates.append(target)
        else:
            candidates.append(f"{target}.md")
        if "/" not in target:
            stem_matches = [
                path for path in notes if Path(path).stem.lower() == target.lower()
            ]
            candidates.extend(stem_matches)
        existing = sorted({candidate for candidate in candidates if candidate in notes})
        if len(existing) == 1:
            target_path = existing[0]
        elif len(existing) > 1:
            return None, "ambiguous"
        else:
            return None, "missing"

    if link.anchor:
        headings = notes[target_path].headings
        anchors = {slugify_heading(heading) for heading in headings}
        if slugify_heading(link.anchor) not in anchors:
            return None, "missing_anchor"
    return target_path, "ok"


def changed_paths(before: Dict[str, Note], after: Dict[str, Note]) -> Dict[str, List[str]]:
    before_paths = set(before)
    after_paths = set(after)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    common = before_paths & after_paths
    modified = sorted(path for path in common if before[path].sha256 != after[path].sha256)
    unchanged = sorted(path for path in common if before[path].sha256 == after[path].sha256)
    return {
        "created": created,
        "modified": modified,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def collect_new_links(
    before: Dict[str, Note], after: Dict[str, Note], changes: Dict[str, List[str]]
) -> List[Dict[str, str]]:
    new_links: List[Dict[str, str]] = []
    for path in changes["created"] + changes["modified"]:
        after_links = {(link.raw, link.kind) for link in after[path].links}
        before_links = (
            {(link.raw, link.kind) for link in before[path].links} if path in before else set()
        )
        for raw, kind in sorted(after_links - before_links):
            target, anchor = normalize_link(raw)
            resolved, status = resolve_link(path, Link(raw, target, anchor, kind), after)
            item = {
                "source": path,
                "raw": raw,
                "target": target,
                "kind": kind,
                "status": status,
            }
            if resolved:
                item["resolved"] = resolved
            new_links.append(item)
    return new_links


def collect_reference_evidence(after: Dict[str, Note]) -> Dict[str, Any]:
    backlinks: Dict[str, List[str]] = {path: [] for path in after}
    broken: List[Dict[str, str]] = []
    for source_path, note in after.items():
        for link in note.links:
            resolved, status = resolve_link(source_path, link, after)
            if resolved:
                backlinks.setdefault(resolved, []).append(source_path)
            else:
                broken.append(
                    {
                        "source": source_path,
                        "raw": link.raw,
                        "target": link.target,
                        "kind": link.kind,
                        "reason": status,
                    }
                )
    for target in backlinks:
        backlinks[target] = sorted(set(backlinks[target]))
    orphans = sorted(
        path
        for path, incoming in backlinks.items()
        if not incoming and Path(path).name.lower() not in {"index.md", "home.md", "readme.md"}
    )
    return {"backlinks": backlinks, "broken_references": broken, "orphaned_notes": orphans}


def collect_unsupported_claims(after: Dict[str, Note], changed: Sequence[str]) -> List[Dict[str, Any]]:
    unsupported: List[Dict[str, Any]] = []
    for path in changed:
        for line_no, line in enumerate(after[path].text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped.lower().startswith("claim:"):
                continue
            if WIKILINK_RE.search(stripped) or MDLINK_RE.search(stripped):
                continue
            unsupported.append(
                {
                    "path": path,
                    "line": line_no,
                    "text": stripped,
                    "reason": "Claim line has no wikilink or Markdown citation.",
                }
            )
    return unsupported


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_expected_note(value: Any) -> str:
    text = str(value).strip().lstrip("./")
    if not text.endswith(".md"):
        text = f"{text}.md"
    return text


def resolve_expected_note(value: Any, notes: Dict[str, Note]) -> Optional[str]:
    expected = normalize_expected_note(value)
    if expected in notes:
        return expected
    stem = Path(expected).stem.lower()
    matches = [path for path in notes if Path(path).stem.lower() == stem]
    return matches[0] if len(matches) == 1 else None


def contains_output_field(note: Note, field: str) -> bool:
    key = field.strip().lower()
    return key in {str(k).lower() for k in note.frontmatter} or key in note.fields


def evaluate_rules(
    expectations: Dict[str, Any],
    before: Dict[str, Note],
    after: Dict[str, Note],
    changes: Dict[str, List[str]],
    evidence: Dict[str, Any],
    new_links: List[Dict[str, str]],
    unsupported_claims: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rules = expectations.get("rules", expectations)
    if not isinstance(rules, dict):
        rules = {}
    changed = changes["created"] + changes["modified"]
    output_targets = changes["created"] or changed
    results: List[Dict[str, Any]] = []

    def add(rule_id: str, passed: bool, details: Dict[str, Any]) -> None:
        results.append({"id": rule_id, "pass": bool(passed), "details": details})

    expected_created = [normalize_expected_note(v) for v in as_list(rules.get("required_created_notes"))]
    if expected_created:
        missing = sorted(set(expected_created) - set(changes["created"]))
        add(
            "required_created_notes",
            not missing,
            {"expected": expected_created, "actual": changes["created"], "missing": missing},
        )

    expected_modified = [normalize_expected_note(v) for v in as_list(rules.get("required_modified_notes"))]
    if expected_modified:
        missing = sorted(set(expected_modified) - set(changes["modified"]))
        add(
            "required_modified_notes",
            not missing,
            {"expected": expected_modified, "actual": changes["modified"], "missing": missing},
        )

    for key, actual in [
        ("min_created_notes", len(changes["created"])),
        ("min_modified_notes", len(changes["modified"])),
        ("min_new_wikilinks", len(new_links)),
    ]:
        if key in rules:
            expected = int(rules[key])
            add(key, actual >= expected, {"expected_minimum": expected, "actual": actual})

    if "max_broken_links" in rules:
        expected = int(rules["max_broken_links"])
        actual = len(evidence["broken_references"])
        add("max_broken_links", actual <= expected, {"expected_maximum": expected, "actual": actual})

    if "max_unsupported_claims" in rules:
        expected = int(rules["max_unsupported_claims"])
        actual = len(unsupported_claims)
        add(
            "max_unsupported_claims",
            actual <= expected,
            {"expected_maximum": expected, "actual": actual},
        )

    required_frontmatter = [str(v) for v in as_list(rules.get("required_frontmatter_fields"))]
    if required_frontmatter:
        missing_by_file: Dict[str, List[str]] = {}
        for path in output_targets:
            lower_keys = {str(key).lower() for key in after[path].frontmatter}
            missing = [field for field in required_frontmatter if field.lower() not in lower_keys]
            if missing:
                missing_by_file[path] = missing
        add(
            "required_frontmatter_fields",
            not missing_by_file and bool(output_targets),
            {"checked_files": output_targets, "missing_by_file": missing_by_file},
        )

    required_sections = [str(v) for v in as_list(rules.get("required_sections"))]
    if required_sections:
        missing_by_file = {}
        for path in output_targets:
            heading_set = {heading.lower() for heading in after[path].headings}
            missing = [section for section in required_sections if section.lower() not in heading_set]
            if missing:
                missing_by_file[path] = missing
        add(
            "required_sections",
            not missing_by_file and bool(output_targets),
            {"checked_files": output_targets, "missing_by_file": missing_by_file},
        )

    required_fields = [str(v) for v in as_list(rules.get("required_output_fields"))]
    if required_fields:
        missing_by_file = {}
        for path in output_targets:
            missing = [field for field in required_fields if not contains_output_field(after[path], field)]
            if missing:
                missing_by_file[path] = missing
        add(
            "required_output_fields",
            not missing_by_file and bool(output_targets),
            {"checked_files": output_targets, "missing_by_file": missing_by_file},
        )

    required_evidence = [str(v) for v in as_list(rules.get("required_evidence_nodes"))]
    if required_evidence:
        changed_resolved_targets = {
            item["resolved"]
            for item in new_links
            if item.get("source") in changed and item.get("resolved")
        }
        missing = []
        expected_resolved = []
        for raw in required_evidence:
            resolved = resolve_expected_note(raw, after)
            expected_resolved.append(resolved or normalize_expected_note(raw))
            if not resolved or resolved not in changed_resolved_targets:
                missing.append(raw)
        add(
            "required_evidence_nodes",
            not missing,
            {
                "expected": expected_resolved,
                "linked_from_changed_notes": sorted(changed_resolved_targets),
                "missing": missing,
            },
        )

    if not results:
        add(
            "no_rules_supplied",
            True,
            {"message": "No explicit rules were supplied; report contains observational evidence only."},
        )
    return results


def write_sample_vault(root: Path) -> Tuple[Path, Path, Path]:
    before = root / "before_vault"
    after = root / "after_vault"
    before_sources = before / "sources"
    after_sources = after / "sources"
    before_sources.mkdir(parents=True, exist_ok=True)
    after_sources.mkdir(parents=True, exist_ok=True)

    (before / "index.md").write_text(
        """---
title: Research Index
---
# Research Index

- [[sources/paper-a]]
""",
        encoding="utf-8",
    )
    paper = """---
title: Paper A
kind: source
---
# Paper A

This source node summarizes a mock research paper used for local auditing examples.
"""
    (before_sources / "paper-a.md").write_text(paper, encoding="utf-8")
    (after_sources / "paper-a.md").write_text(paper, encoding="utf-8")
    (after / "index.md").write_text(
        """---
title: Research Index
---
# Research Index

- [[sources/paper-a]]
- [[synthesis]]
""",
        encoding="utf-8",
    )
    (after / "synthesis.md").write_text(
        """---
title: Synthesis
evidence_status: reviewed
---
# Summary

Claim: Retrieval-augmented synthesis should preserve source links. [[sources/paper-a]]

# Evidence

- [[sources/paper-a]] supports the main finding.
- [[index]] links this synthesis into the vault.

Decision: Keep the synthesis note and cite source nodes.
""",
        encoding="utf-8",
    )
    spec = root / "audit.yaml"
    spec.write_text(
        """task: Build a cited synthesis note
rules:
  required_created_notes:
    - synthesis.md
  required_modified_notes:
    - index.md
  required_frontmatter_fields:
    - title
    - evidence_status
  required_sections:
    - Summary
    - Evidence
  required_output_fields:
    - Decision
  required_evidence_nodes:
    - sources/paper-a.md
  min_new_wikilinks: 2
  max_broken_links: 0
  max_unsupported_claims: 0
""",
        encoding="utf-8",
    )
    return before, after, spec


def load_expectations(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = load_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError("Expectation file must parse to an object.")
    return data


def display_input(value: Optional[Path], fallback: str) -> str:
    if value is None:
        return fallback
    text = value.as_posix()
    try:
        return Path(text).relative_to(Path.cwd()).as_posix()
    except ValueError:
        return text


def build_report(
    before_dir: Path,
    after_dir: Path,
    expectations_path: Path,
    sample_mode: bool,
    original_before: Optional[Path],
    original_after: Optional[Path],
    original_expectations: Optional[Path],
) -> Dict[str, Any]:
    expectations = load_expectations(expectations_path)
    before = snapshot_vault(before_dir)
    after = snapshot_vault(after_dir)
    changes = changed_paths(before, after)
    new_links = collect_new_links(before, after, changes)
    reference_evidence = collect_reference_evidence(after)
    changed = changes["created"] + changes["modified"]
    unsupported_claims = collect_unsupported_claims(after, changed)
    evidence = {
        **reference_evidence,
        "new_wikilinks": [item for item in new_links if item["kind"] == "wikilink"],
        "new_markdown_links": [item for item in new_links if item["kind"] == "markdown"],
        "unsupported_claims": unsupported_claims,
    }
    rules = evaluate_rules(
        expectations,
        before,
        after,
        changes,
        evidence,
        new_links,
        unsupported_claims,
    )
    passed = sum(1 for rule in rules if rule["pass"])
    total = len(rules)
    score = round((passed / total) * 100, 2) if total else 100.0
    return {
        "tool": "TraceVault",
        "version": VERSION,
        "task": expectations.get("task", "Evidence audit"),
        "inputs": {
            "before": display_input(original_before, "built-in-sample"),
            "after": display_input(original_after, "built-in-sample"),
            "expectations": display_input(original_expectations, "built-in-sample"),
            "sample_mode": sample_mode,
            "api_key_present": bool(os.environ.get("TRACEVAULT_API_KEY")),
        },
        "summary": {
            "verdict": "pass" if passed == total else "fail",
            "score": score,
            "passed_rules": passed,
            "total_rules": total,
            "created_notes": len(changes["created"]),
            "modified_notes": len(changes["modified"]),
            "deleted_notes": len(changes["deleted"]),
            "new_wikilinks": len(evidence["new_wikilinks"]),
            "broken_references": len(evidence["broken_references"]),
            "unsupported_claims": len(unsupported_claims),
        },
        "changes": changes,
        "evidence": evidence,
        "rules": rules,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit before/after Markdown vaults against a YAML expectation file."
    )
    parser.add_argument("--before", type=Path, help="Pre-task Markdown vault directory.")
    parser.add_argument("--after", type=Path, help="Post-task Markdown vault directory.")
    parser.add_argument("--expectations", type=Path, help="YAML or JSON audit expectation file.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evidence_audit.json"),
        help="Output JSON path, or '-' for stdout.",
    )
    parser.add_argument(
        "--fail-on-fail",
        action="store_true",
        help="Return exit code 1 when any audit rule fails.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    provided = [args.before, args.after, args.expectations]
    provided_count = sum(value is not None for value in provided)
    sample_mode = provided_count == 0

    temp_dir: Optional[str] = None
    try:
        if provided_count not in {0, 3}:
            raise ValueError(
                "Provide --before, --after, and --expectations together, "
                "or omit all three for sample mode."
            )
        if sample_mode:
            temp_dir = tempfile.mkdtemp(prefix="tracevault-sample-")
            before_dir, after_dir, expectations_path = write_sample_vault(Path(temp_dir))
            original_before = original_after = original_expectations = None
        else:
            before_dir = args.before
            after_dir = args.after
            expectations_path = args.expectations
            original_before = args.before
            original_after = args.after
            original_expectations = args.expectations

        assert before_dir is not None
        assert after_dir is not None
        assert expectations_path is not None
        report = build_report(
            before_dir,
            after_dir,
            expectations_path,
            sample_mode,
            original_before,
            original_after,
            original_expectations,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if str(args.out) == "-":
            print(rendered)
        else:
            args.out.write_text(rendered + "\n", encoding="utf-8")
            print(
                f"TraceVault audit {report['summary']['verdict']} "
                f"({report['summary']['passed_rules']}/{report['summary']['total_rules']} rules). "
                f"Wrote {args.out.as_posix()}."
            )
        if args.fail_on_fail and report["summary"]["verdict"] != "pass":
            return 1
        return 0
    except Exception as exc:
        print(f"TraceVault error: {exc}", file=sys.stderr)
        return 2
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
