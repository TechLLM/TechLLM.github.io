#!/usr/bin/env python3
"""Tiny import-based self-test for the GateWeave reference CLI."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run  # noqa: E402


def test_sample_report_shape() -> None:
    """Assert the built-in sample returns the expected report shape and metrics."""

    report = run.sample_report()
    assert report["protocol"] == "gateweave-v0"
    assert report["threshold"] == 0.5
    assert report["labels"]["rows"] == 8
    assert [scorer["name"] for scorer in report["scorers"]] == ["baseline", "candidate"]

    baseline = report["scorers"][0]
    candidate = report["scorers"][1]
    assert baseline["aggregate"]["precision"] == 0.666667
    assert baseline["aggregate"]["recall"] == 0.5
    assert baseline["aggregate"]["f1"] == 0.571429
    assert baseline["worst_slice"]["column"] == "domain"
    assert baseline["worst_slice"]["value"] == "sales"
    assert candidate["aggregate"]["f1"] == 0.75
    assert candidate["missing_field_stress"][0]["stress_score"] == 0.666667

    comparison = report["comparisons"][0]
    assert comparison == {
        "metric": "aggregate_f1",
        "best": ["candidate"],
        "scores": {"baseline": 0.571429, "candidate": 0.75},
    }


def main() -> int:
    """Run tests without requiring a test framework."""

    test_sample_report_shape()
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
