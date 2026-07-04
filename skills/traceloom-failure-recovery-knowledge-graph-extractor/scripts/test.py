#!/usr/bin/env python3
"""Tiny self-test for the TraceLoom reference extractor."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""
    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("traceloom_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert the sample extraction returns the expected public shape."""
    run = load_run_module()
    result = run.extract_trace(run.SAMPLE_TRACE, "sample-trace")
    assert isinstance(result, dict)
    for key in ("trace_id", "source", "summary", "failures", "wikilinks", "nodes", "edges", "markdown"):
        assert key in result, f"missing key: {key}"
    assert result["trace_id"].startswith("trace-")
    assert result["source"] == "sample-trace"
    assert result["summary"] == (
        "Recovered 1 of 1 detected failure(s). "
        "Main pattern: missing_dependency repaired with python -m pip install pyyaml."
    )
    assert len(result["failures"]) == 1
    failure = result["failures"][0]
    assert failure["error_signature"] == "ModuleNotFoundError: No module named 'yaml'"
    assert failure["likely_cause"] == "missing_dependency"
    assert failure["failed_command"] == "python worker.py"
    assert failure["recovery_command"] == "python -m pip install pyyaml"
    assert failure["resume_point"] == "python worker.py"
    assert failure["outcome"] == "recovered"
    assert any(node["type"] == "failure" for node in result["nodes"])
    assert any(edge["type"] == "RECOVERED_FROM" for edge in result["edges"])
    assert "[[missing dependency]]" in result["wikilinks"]
    assert "# TraceLoom Recovery Note" in result["markdown"]
    print("TraceLoom self-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
