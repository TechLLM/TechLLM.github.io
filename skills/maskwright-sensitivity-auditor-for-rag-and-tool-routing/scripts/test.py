#!/usr/bin/env python3
"""Tiny self-test for the Maskwright reference runner."""

from __future__ import annotations

import run


def main() -> int:
    """Assert the sample analysis has the expected shape and stable headline values."""

    result = run.analyze(run.SAMPLE_DATA)
    assert set(result) == {"summary", "candidate_sensitivity", "span_sensitivity"}
    summary = result["summary"]
    assert summary["correct_id"] == "tool-password-reset"
    assert summary["base_top_id"] == "tool-password-reset"
    assert summary["base_correct_rank"] == 1
    assert isinstance(summary["failure_labels"], list)
    assert len(result["candidate_sensitivity"]) == 3
    assert len(result["span_sensitivity"]) >= 3
    assert {
        "removed_candidate_id",
        "masked_top_id",
        "failure_signal",
        "entropy_change",
    }.issubset(result["candidate_sensitivity"][0])
    assert {
        "candidate_id",
        "span_start",
        "span_text",
        "candidate_score_delta",
        "failure_signal",
    }.issubset(result["span_sensitivity"][0])
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
