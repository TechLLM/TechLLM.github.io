#!/usr/bin/env python3
"""Tiny self-test for the RiftLens CLI module."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""
    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("riftlens_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load scripts/run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that core evaluation returns the expected deterministic shape."""
    run = load_run_module()
    result = run.evaluate_records(run.SAMPLE_RECORDS, threshold=0.6)
    assert result["query_count"] == 3
    assert result["domain_count"] == 4
    assert result["worst_domain"] == "api_reference"
    assert round(result["worst_domain_gap"], 3) == 1.0
    assert set(result.keys()) == {
        "threshold",
        "top_k",
        "query_count",
        "domain_count",
        "overall",
        "domains",
        "best_domain",
        "worst_domain",
        "worst_domain_gap",
        "flags",
    }
    api_row = next(row for row in result["domains"] if row["domain"] == "api_reference")
    assert api_row["relevant_items"] == 1
    assert api_row["passed_items"] == 0
    assert api_row["hit_rate"] == 0.0
    markdown = run.render_markdown(result)
    assert markdown.startswith("# RiftLens Domain Collapse Report\n")
    assert "| api_reference | 66.7% | 0.0% | 0.0% | 100.0% | 1 | 0 |" in markdown
    print("RiftLens self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
