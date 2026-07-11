#!/usr/bin/env python3
"""Tiny import-based self-test for the TraceShepherd reference implementation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import run


def main() -> int:
    """Assert that the core grader returns the expected report shape."""

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        output_file = workspace / "docs" / "agent-report.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(run.SAMPLE_FILE_CONTENT, encoding="utf-8")

        report = run.grade_execution(run.sample_events(), run.sample_manifest(), workspace)

    assert isinstance(report, dict)
    assert report["tool"] == "traceshepherd"
    assert report["version"] == run.VERSION
    assert report["status"] == "pass"
    assert report["summary"] == {"checks": 10, "passed": 10, "failed": 0}
    assert set(report) == {
        "tool",
        "version",
        "status",
        "summary",
        "evidence",
        "files",
        "policy",
        "errors",
    }
    assert report["evidence"]["missing_events"] == []
    assert report["policy"]["unexpected_modified_files"] == []
    assert report["policy"]["forbidden_modified_files"] == []
    assert len(report["files"]) == 1
    assert report["files"][0]["path"] == "docs/agent-report.md"
    assert report["files"][0]["pass"] is True
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
