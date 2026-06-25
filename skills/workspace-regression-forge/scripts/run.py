#!/usr/bin/env python3
"""Forge <internal> regression test cases for Claude Code/OpenClaw skills."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
EXCLUDE_SUFFIXES = {".pyc", ".DS_Store"}


def copy_sample(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)

    def ignore(_dir: str, names: list[str]) -> set[str]:
        skipped: set[str] = set()
        for name in names:
            if name in EXCLUDE_DIRS or any(name.endswith(s) for s in EXCLUDE_SUFFIXES):
                skipped.add(name)
        return skipped

    if src.is_dir():
        shutil.copytree(src, dst, ignore=ignore)
    else:
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst / src.name)


def parse_pair(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("expected PATH:TEXT")
    left, right = value.split(":", 1)
    if not left or not right:
        raise argparse.ArgumentTypeError("expected non-empty PATH:TEXT")
    return left, right


def rel_safe(root: Path, rel: str) -> Path:
    target = (root / rel).resolve()
    root_resolved = root.resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f"path escapes workspace: {rel}")
    return target


def write_pytest(out: Path, expect_files: list[str], expect_contains: list[tuple[str, str]], forbid_contains: list[tuple[str, str]]) -> None:
    checks = out / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    lines = [
        "from pathlib import Path",
        "",
        "ROOT = Path(__file__).resolve().parents[1] / 'workspace'",
        "",
        "def read(rel):",
        "    return (ROOT / rel).read_text(encoding='utf-8')",
        "",
    ]
    for i, rel in enumerate(expect_files):
        lines += [
            f"def test_expected_file_exists_{i}():",
            f"    assert (ROOT / {rel!r}).exists()",
            "",
        ]
    for i, (rel, text) in enumerate(expect_contains):
        lines += [
            f"def test_expected_text_{i}():",
            f"    assert {text!r} in read({rel!r})",
            "",
        ]
    for i, (rel, text) in enumerate(forbid_contains):
        lines += [
            f"def test_forbidden_text_absent_{i}():",
            f"    path = ROOT / {rel!r}",
            "    assert not path.exists() or " + repr(text) + " not in path.read_text(encoding='utf-8')",
            "",
        ]
    if len(lines) <= 7:
        lines += [
            "def test_workspace_exists():",
            "    assert ROOT.exists()",
            "",
        ]
    (checks / "test_workspace.py").write_text("\n".join(lines), encoding="utf-8")


def write_bash(out: Path, expect_files: list[str], expect_contains: list[tuple[str, str]], forbid_contains: list[tuple[str, str]]) -> None:
    checks = out / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "ROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)/workspace\"",
    ]
    for rel in expect_files:
        lines.append(f"test -e \"$ROOT/{rel}\"")
    for rel, text in expect_contains:
        lines.append(f"grep -F {json.dumps(text)} \"$ROOT/{rel}\" >/dev/null")
    for rel, text in forbid_contains:
        lines.append(f"if [ -e \"$ROOT/{rel}\" ]; then ! grep -F {json.dumps(text)} \"$ROOT/{rel}\" >/dev/null; fi")
    lines.append("echo ok")
    path = checks / "check.sh"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)


def forge(args: argparse.Namespace) -> None:
    task_path = Path(args.task).expanduser().resolve()
    sample_path = Path(args.sample).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    workspace = out / "workspace"

    if not task_path.exists():
        raise SystemExit(f"task file not found: {task_path}")
    if not sample_path.exists():
        raise SystemExit(f"sample path not found: {sample_path}")

    out.mkdir(parents=True, exist_ok=True)
    task_text = task_path.read_text(encoding="utf-8")
    (out / "task.md").write_text(task_text, encoding="utf-8")
    copy_sample(sample_path, workspace)

    for rel in args.expect_file:
        rel_safe(workspace, rel)
    for rel, _ in args.expect_contains + args.forbid_contains:
        rel_safe(workspace, rel)

    acceptance = ["# Acceptance Criteria", ""]
    acceptance += [f"- File exists: `{rel}`" for rel in args.expect_file]
    acceptance += [f"- `{rel}` contains `{text}`" for rel, text in args.expect_contains]
    acceptance += [f"- `{rel}` does not contain `{text}`" for rel, text in args.forbid_contains]
    if len(acceptance) == 2:
        acceptance.append("- Workspace exists and target task completes without modifying the original sample.")
    (out / "acceptance.md").write_text("\n".join(acceptance) + "\n", encoding="utf-8")

    if args.mode == "pytest":
        write_pytest(out, args.expect_file, args.expect_contains, args.forbid_contains)
        check_command = "pytest checks"
    else:
        write_bash(out, args.expect_file, args.expect_contains, args.forbid_contains)
        check_command = "bash checks/check.sh"

    manifest = {
        "name": out.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "sample_source": str(sample_path),
        "workspace": "workspace",
        "task": "task.md",
        "acceptance": "acceptance.md",
        "check_command": check_command,
        "expect_file": args.expect_file,
        "expect_contains": [{"path": p, "text": t} for p, t in args.expect_contains],
        "forbid_contains": [{"path": p, "text": t} for p, t in args.forbid_contains],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "check_command": check_command}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Forge workspace regression test cases")
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("forge")
    f.add_argument("--task", required=True, help="Markdown file containing the agent task")
    f.add_argument("--sample", required=True, help="Sample workspace file or directory to copy")
    f.add_argument("--out", required=True, help="Output test case directory")
    f.add_argument("--mode", choices=["pytest", "bash"], default="pytest")
    f.add_argument("--expect-file", action="append", default=[])
    f.add_argument("--expect-contains", type=parse_pair, action="append", default=[])
    f.add_argument("--forbid-contains", type=parse_pair, action="append", default=[])
    f.set_defaults(func=forge)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
