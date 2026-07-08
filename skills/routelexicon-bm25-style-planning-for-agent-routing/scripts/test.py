#!/usr/bin/env python3
"""Tiny import-based self-test for RouteLexicon."""

from __future__ import annotations

import run


def main() -> int:
    """Assert that the sample route has the expected machine-readable shape."""
    result = run.route_request(run.SAMPLE_REQUEST, run.SAMPLE_MANIFEST, top_k=2)

    assert isinstance(result, dict)
    assert result["version"] == "0.1.0"
    assert result["request"] == run.SAMPLE_REQUEST
    assert isinstance(result["query_terms"], list)
    assert result["ranked_agents"][0]["agent_id"] == "research-agent"
    assert result["routing_plan"]["selected_agent_ids"][0] == "research-agent"

    first = result["ranked_agents"][0]
    assert set(first) == {
        "agent_id",
        "name",
        "score",
        "matched_terms",
        "rare_terms",
        "excluded_by",
        "weights",
        "rationale",
    }
    assert set(first["weights"]) == {
        "bm25",
        "keyword_boost",
        "exclusion_penalty",
        "final",
    }
    assert all("term" in item and "idf" in item and "tf" in item for item in first["matched_terms"])
    assert isinstance(result["routing_plan"]["decomposed_subqueries"], list)
    assert result["routing_plan"]["decomposed_subqueries"][0]["id"] == "q1"

    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
