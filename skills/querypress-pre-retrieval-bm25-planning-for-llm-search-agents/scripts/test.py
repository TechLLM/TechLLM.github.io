#!/usr/bin/env python3
"""Tiny self-test for the QueryPress reference implementation."""

from __future__ import annotations

import run


def test_sample_plan_shape() -> None:
    """Assert that the sample planner output has the expected stable shape."""
    plan = run.build_plan(run.SAMPLE_QUESTION, run.SAMPLE_DOCUMENTS)

    assert set(plan) == {"question", "corpus", "plan", "execution_notes"}
    assert plan["question"] == run.SAMPLE_QUESTION
    assert plan["corpus"]["documents"] == 3
    assert isinstance(plan["corpus"]["tokens"], int)
    assert plan["corpus"]["tokens"] > 0

    nested = plan["plan"]
    assert set(nested) == {
        "rare_term_anchors",
        "ngram_candidates",
        "synonym_slots",
        "exclusion_terms",
        "decomposed_queries",
    }
    assert nested["rare_term_anchors"]
    assert nested["decomposed_queries"]
    assert nested["decomposed_queries"][0]["id"] == "q1"
    assert "query" in nested["decomposed_queries"][0]
    assert "bm25" in [item["term"] for item in nested["rare_term_anchors"]]


if __name__ == "__main__":
    test_sample_plan_shape()
    print("scripts/test.py: ok")
