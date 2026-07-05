#!/usr/bin/env python3
"""Tiny import-based self-test for QueryLoom."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import run  # noqa: E402


def test_sample_plan_shape() -> None:
    """Assert that the sample plan has the expected shape and core content."""

    plan = run.build_retrieval_plan(run.SAMPLE_QUESTION, run.SAMPLE_DOCUMENTS)

    assert plan["schema_version"] == "1.0"
    assert plan["planner"]["name"] == "queryloom-local-heuristic"
    assert plan["planner"]["external_llm_used"] is False
    assert plan["question"] == run.SAMPLE_QUESTION
    assert plan["corpus"]["document_count"] == 3
    assert plan["rare_term_candidates"]
    assert plan["synonym_slots"]
    assert plan["subqueries"]

    first_subquery = plan["subqueries"][0]
    assert first_subquery["id"] == "q1"
    assert "bm25_query" in first_subquery
    assert "required_terms" in first_subquery
    assert "evidence_requirements" in first_subquery
    assert any(term["term"] == "bm25" for term in plan["rare_term_candidates"])
    assert any(slot["slot"] == "retrieval" for slot in plan["synonym_slots"])


if __name__ == "__main__":
    test_sample_plan_shape()
    print("ok")
