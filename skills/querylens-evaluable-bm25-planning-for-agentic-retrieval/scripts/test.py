#!/usr/bin/env python3
"""Tiny self-test for the QueryLens reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


RUN_PATH = Path(__file__).parent / "run.py"
SPEC = importlib.util.spec_from_file_location("querylens_run", RUN_PATH)
assert SPEC is not None and SPEC.loader is not None
run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run)


def test_sample_plan_shape() -> None:
    """Assert the sample data returns the expected plan shape and core terms."""

    result = run.run_selftest()
    assert set(result) == {"question", "corpus", "plan", "diagnostics"}
    assert result["corpus"]["document_count"] == 3
    assert result["corpus"]["source"] == "built-in-sample"

    plan = result["plan"]
    assert set(plan) == {
        "bm25_query",
        "include_terms",
        "optional_expansion_terms",
        "exclusion_terms",
        "preserved_constraints",
        "verification_checklist",
    }
    assert isinstance(plan["bm25_query"], str) and plan["bm25_query"]
    assert isinstance(plan["include_terms"], list) and plan["include_terms"]
    assert {"term", "kind", "idf", "reason"} <= set(plan["include_terms"][0])
    assert "hybrid retrieval" in {item["term"] for item in plan["include_terms"]}
    assert "local corpus" in {item["term"] for item in plan["include_terms"]}
    assert "external apis" in plan["exclusion_terms"]
    assert any(item["type"] == "negation" for item in plan["preserved_constraints"])
    assert isinstance(result["diagnostics"]["question_terms_considered"], list)


if __name__ == "__main__":
    test_sample_plan_shape()
    print("ok")
