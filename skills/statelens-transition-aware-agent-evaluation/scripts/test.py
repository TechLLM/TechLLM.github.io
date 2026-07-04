"""Tiny self-test for the StateLens reference implementation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import run


def test_sample_report_shape() -> None:
    """Assert that the built-in sample returns the expected report shape."""
    with tempfile.TemporaryDirectory(prefix="statelens_test_") as temp_dir:
        paths = run.write_sample_case(Path(temp_dir))
        spec = run.load_spec(paths["spec"])
        report = run.evaluate_state_transition(
            paths["before"],
            paths["after"],
            spec,
            trace_path=paths["trace"],
        )

    assert set(report) == {"task_id", "pass", "summary", "checks", "diffs"}
    assert report["task_id"] == "demo-note-update"
    assert report["pass"] is True
    assert report["summary"]["confidence"] == "high"
    assert report["summary"]["checks_failed"] == 0
    assert report["summary"]["checks_passed"] == 10
    assert report["summary"]["files_modified"] == 2
    assert report["summary"]["unexpected_changes"] == 0
    assert isinstance(report["checks"], list)
    assert all("name" in check and "pass" in check and "details" in check for check in report["checks"])
    assert report["diffs"]["added"] == []
    assert report["diffs"]["deleted"] == []
    assert report["diffs"]["modified"] == ["metadata.json", "notes/summary.md"]
    assert len(report["diffs"]["file_diffs"]) == 2


if __name__ == "__main__":
    test_sample_report_shape()
    print("scripts/test.py: ok")
