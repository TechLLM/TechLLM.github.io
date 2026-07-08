#!/usr/bin/env python3
"""Tiny self-test for the DiffSentinel reference implementation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""

    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("diffsentinel_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that the built-in sample returns the expected report shape."""

    run = load_run_module()
    report = run.run_selftest()
    assert isinstance(report, dict)
    assert set(report) == {
        "pass",
        "score",
        "earned_points",
        "max_score",
        "summary",
        "checks",
        "warnings",
        "metadata",
    }
    assert report["pass"] is True
    assert report["score"] == 1.0
    assert report["earned_points"] == 13
    assert report["max_score"] == 13
    assert report["summary"] == {"passed": 13, "failed": 0, "warnings": 0}
    assert isinstance(report["checks"], list)
    assert len(report["checks"]) == 13
    assert all(check["status"] == "pass" for check in report["checks"])
    assert report["warnings"] == []
    assert report["metadata"]["schema_version"] == "1.0"
    assert report["metadata"]["created_count"] == 2
    assert report["metadata"]["deleted_count"] == 1
    assert report["metadata"]["modified_count"] == 1
    assert report["metadata"]["unchanged_count"] == 1
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
