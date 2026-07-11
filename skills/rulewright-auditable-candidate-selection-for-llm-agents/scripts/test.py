#!/usr/bin/env python3
"""Tiny import-based self-test for the Rulewright reference implementation."""

import run


def main() -> None:
    """Assert the core function returns the expected shape on sample data."""
    payload = run.sample_input()
    rules = run.generate_rules(payload)
    matrix = run.evaluate_candidates(payload, rules)
    replay_rules = run.rules_from_yaml(run.rules_to_yaml(rules))
    replay_matrix = run.evaluate_candidates(payload, replay_rules)

    assert isinstance(matrix, dict)
    assert set(matrix) == {"query", "rules_fingerprint", "selected_ids", "candidates"}
    assert matrix["selected_ids"] == ["doc-rules-first"]
    assert replay_matrix["selected_ids"] == matrix["selected_ids"]
    assert replay_matrix["rules_fingerprint"] == matrix["rules_fingerprint"]
    assert len(matrix["candidates"]) == 3
    assert isinstance(matrix["rules_fingerprint"], str)
    assert len(matrix["rules_fingerprint"]) == 16
    first = matrix["candidates"][0]
    assert set(first) == {
        "id",
        "passed",
        "rejected",
        "rejection_reasons",
        "total_score",
        "dimension_scores",
        "weighted_scores",
        "evidence",
    }
    assert first["passed"] is True
    assert first["total_score"] == 0.775
    print("self-test passed")


if __name__ == "__main__":
    main()
