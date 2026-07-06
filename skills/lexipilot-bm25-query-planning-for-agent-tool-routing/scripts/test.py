#!/usr/bin/env python3
"""Tiny self-test for LexiPilot's routing core."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import run.py from this directory without requiring package setup."""

    path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("lexipilot_run", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import scripts/run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert the sample route has the expected deterministic shape."""

    run = load_run_module()
    result = run.route_tools(run.SAMPLE_INPUT["request"], run.SAMPLE_INPUT["tools"])

    assert set(result) == {"query_plan", "candidates", "excluded_tools", "metadata"}
    assert result["query_plan"]["required_capabilities"] == ["audit", "bm25", "exclusion", "routing"]
    assert result["candidates"], "expected at least one candidate"
    assert result["candidates"][0]["id"] == "lexical-router"
    assert isinstance(result["candidates"][0]["score"], float)
    assert result["candidates"][0]["excluded"] is False
    assert result["excluded_tools"] == [
        {"id": "email-sender", "name": "Email Sender", "reason": "matched exclusion term: email"}
    ]
    assert result["metadata"] == {
        "algorithm": "bm25-lite",
        "top_k": 3,
        "tool_count": 3,
        "min_score": 0.0,
    }
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
