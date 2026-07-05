"""Tiny self-test for the BiasLens RAG reference implementation."""

import run


def main() -> int:
    """Assert that sample diagnostics return the expected shape and categories."""

    report = run.analyze_cases(run.sample_cases(), keyword_limit=5)
    assert report["tool"] == "biaslens-rag"
    assert report["version"] == "0.1.0"
    assert report["summary"] == {
        "cases": 2,
        "correct_evidence_absent": 1,
        "reranker_instability_or_bias": 1,
        "no_failure_signal": 0,
        "mean_selection_stability": 0.75,
        "mean_position_bias_score": 0.5,
    }
    assert len(report["cases"]) == 2
    absent, biased = report["cases"]
    assert absent["query_id"] == "q_absent"
    assert absent["failure_category"] == "correct_evidence_absent"
    assert absent["correct_evidence_present"] is False
    assert biased["query_id"] == "q_present_biased"
    assert biased["failure_category"] == "reranker_instability_or_bias"
    assert biased["correct_evidence_present"] is True
    assert biased["unstable_alternatives"] == ["refund_policy"]
    assert {"term": "billing", "score": 1.0} in biased["keyword_attraction"]
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
