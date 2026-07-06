#!/usr/bin/env python3
"""Tiny self-test for the FacetRecall reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py from this directory."""

    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("facetrecall_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that the sample benchmark returns the expected shape and values."""

    run = load_run_module()
    result = run.evaluate(run.sample_queries(), run.sample_metadata())

    assert set(result) == {
        "overall",
        "slices",
        "missing_context_failures",
        "false_passes",
        "warnings",
    }
    assert result["overall"]["query_count"] == 5
    assert result["overall"]["recall"] == 0.6
    assert result["overall"]["hit_rate"] == 0.6
    assert result["overall"]["false_pass_rate"] == 0.6
    assert result["overall"]["missing_context_failure_rate"] == 0.4
    assert len(result["slices"]) == 19
    assert [row["query_id"] for row in result["missing_context_failures"]] == ["q2", "q5"]
    assert [row["query_id"] for row in result["false_passes"]] == ["q2", "q3", "q5"]
    assert result["warnings"] == []

    markdown = run.render_markdown(result)
    assert "# FacetRecall Report" in markdown
    assert "| modality | table | 1 | 0.000 | 1.000 | 1 |" in markdown
    print("FacetRecall self-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
