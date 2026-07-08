#!/usr/bin/env python3
"""Tiny self-test for the PathLoom reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""
    module_path = Path(__file__).resolve().parent / "run.py"
    spec = importlib.util.spec_from_file_location("pathloom_run", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that the sample trace returns the expected output shape."""
    run = load_run_module()
    result = run.prioritize_trace(run.SAMPLE_TRACE)

    assert set(result) == {"summary", "items", "edges", "recommendations"}
    assert result["summary"]["item_count"] == 8
    assert result["summary"]["edge_count"] >= 6
    assert isinstance(result["items"], list)
    assert result["items"][0]["id"] == "t2"
    assert result["items"][1]["id"] == "o1"
    assert result["items"][2]["id"] == "c1"
    assert result["items"][0]["recommendation"] == "prefetch"
    assert {"prefetch", "keep", "delay", "prune"} == set(result["recommendations"])
    assert any(item["id"] == "m2" for item in result["recommendations"]["prune"])

    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
