"""Tiny import-based self-test for the Tracewright reference CLI."""

from __future__ import annotations

import copy
import sys

import run


def test_sample_passes() -> None:
    """Assert that the built-in passing sample returns the expected report shape."""

    report = run.grade_artifacts(run.SAMPLE_SPEC, run.SAMPLE_ARTIFACTS)
    assert set(report) == {"task_id", "passed", "score", "summary", "checks"}
    assert report["task_id"] == "sample-agent-edit"
    assert report["passed"] is True
    assert report["score"] == 1.0
    assert report["summary"] == {"passed": 13, "failed": 0, "total": 13}
    assert isinstance(report["checks"], list)
    assert len(report["checks"]) == 13
    for check in report["checks"]:
        assert set(check) == {"id", "category", "passed", "message"}
        assert isinstance(check["id"], str)
        assert isinstance(check["category"], str)
        assert isinstance(check["passed"], bool)
        assert isinstance(check["message"], str)


def test_sample_failure_detected() -> None:
    """Assert that a missing required file is reported as a failure."""

    artifacts = copy.deepcopy(run.SAMPLE_ARTIFACTS)
    artifacts["workspace_files"] = {}
    report = run.grade_artifacts(run.SAMPLE_SPEC, artifacts)
    assert report["passed"] is False
    assert report["summary"]["failed"] >= 1
    assert any(check["id"] == "file.required:src/feature.py" and not check["passed"] for check in report["checks"])


def main() -> int:
    """Run the tiny self-test suite."""

    test_sample_passes()
    test_sample_failure_detected()
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
