#!/usr/bin/env python3
"""Tiny self-test for the TraceTrellis reference grader."""

import run


def test_sample_shape() -> None:
    """Assert that the bundled sample returns the expected report shape."""
    report = run.grade_runs(run.SAMPLE_TRACES, run.SAMPLE_MANIFEST)
    assert report["tool"] == "rag-evidence-grader"
    assert report["version"] == "0.1.0"
    assert report["summary"]["cases"] == 1
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 0
    assert set(report["summary"]["average_scores"]) == {
        "retrieval",
        "action",
        "data_accuracy",
        "overall",
    }
    case = report["cases"][0]
    assert case["run_id"] == "refund-window"
    assert case["passed"] is True
    assert case["scores"] == {
        "retrieval": 1.0,
        "action": 1.0,
        "data_accuracy": 1.0,
        "overall": 1.0,
    }
    assert case["documents"]["required_missing"] == []
    assert case["documents"]["forbidden_found"] == []
    assert case["actions"]["required_missing"] == []
    assert case["facts"]["missing"] == []
    assert case["failures"] == []


if __name__ == "__main__":
    test_sample_shape()
    print("scripts/test.py: ok")
