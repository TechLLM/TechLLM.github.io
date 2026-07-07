#!/usr/bin/env python3
"""Tiny import-based self-test for the ClaimWeaver reference implementation."""

import json

import run


def main() -> int:
    """Assert the core reducer returns the expected stable output shape."""
    result = run.reduce_agent_outputs(run.sample_input())

    assert set(result) == {
        "metadata",
        "task",
        "principles",
        "claims",
        "accepted",
        "needs_review",
        "rejected",
    }
    assert result["metadata"]["tool"] == "ClaimWeaver"
    assert result["metadata"]["evaluator"] == "rule"
    assert result["metadata"]["claim_count"] == len(result["claims"])
    assert result["metadata"]["accepted"] == len(result["accepted"])
    assert result["metadata"]["rejected"] == len(result["rejected"])
    assert result["metadata"]["accepted"] >= 1
    assert result["metadata"]["rejected"] >= 1

    first = result["claims"][0]
    assert set(first) == {
        "claim_id",
        "status",
        "confidence",
        "text",
        "rationale",
        "supporting_agents",
        "supporting_sources",
        "principle_scores",
    }
    assert first["claim_id"] == "cw-001"
    assert first["status"] in {"accepted", "needs_review", "rejected"}
    assert isinstance(first["confidence"], float)
    assert first["supporting_sources"]
    assert first["principle_scores"]

    json.dumps(result)
    print("ClaimWeaver self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
