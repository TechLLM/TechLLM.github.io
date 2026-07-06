"""Tiny self-test for the RouteLens route-audit reference implementation."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import run  # noqa: E402


def test_sample_report_shape() -> None:
    """Assert that the built-in sample returns the expected report shape."""

    report = run.audit_records(run.SAMPLE_RECORDS)
    assert report["schema_version"] == "routelens.audit.v1"
    assert report["summary"] == {
        "total_queries": 6,
        "successes": 3,
        "failures": 3,
        "fallback_used": 3,
        "average_quality_score": 0.715,
        "average_subset_quality_gap": 0.14,
    }
    assert isinstance(report["domain_failure_rates"], list)
    assert isinstance(report["routing_confusion_matrix"], list)
    assert isinstance(report["subset_vs_full_model_gaps"], list)
    assert isinstance(report["index_model_quality"], list)
    assert isinstance(report["degradation_reports"], list)
    assert report["domain_failure_rates"][0]["domain"] == "support"
    assert report["degradation_reports"][0]["selected_index"] == "general_docs"


if __name__ == "__main__":
    test_sample_report_shape()
    print("scripts/test.py: ok")
