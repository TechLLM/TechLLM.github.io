#!/usr/bin/env python3
"""Tiny self-test for the RouteGlyph reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""

    module_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("routeglyph_run", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import scripts/run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that the sample data returns the expected RouteGlyph shape."""

    run = load_run_module()
    plan = run.route_query(run.SAMPLE_QUERY, run.SAMPLE_CATALOG, synonyms=run.DEFAULT_SYNONYMS)
    assert plan["plan_version"] == "routeglyph.v1"
    assert plan["tokenizer"] == "routeglyph-tokenizer.v1"
    assert plan["query"] == run.SAMPLE_QUERY
    assert isinstance(plan["query_terms"], list) and "bm25" in plan["query_terms"]
    assert isinstance(plan["required_constraints"], list)
    assert isinstance(plan["candidates"], list) and len(plan["candidates"]) == 4
    top = plan["candidates"][0]
    assert top["tool_id"] == "route_planner"
    assert top["rank"] == 1
    assert isinstance(top["score"], float)
    assert "bm25" in top["rare_terms"]
    assert isinstance(top["matched_terms"], list) and top["matched_terms"]
    assert isinstance(top["synonyms"], list)
    assert set(top["exclusions"]) == {"configured", "triggered"}
    assert set(top["constraints"]) == {"required", "matched", "missing"}
    assert isinstance(top["rationales"], list) and top["rationales"]
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
