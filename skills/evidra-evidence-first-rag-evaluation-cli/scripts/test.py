#!/usr/bin/env python3
"""Tiny self-test for the Evidra reference evaluator."""

from __future__ import annotations

import run


def main() -> int:
    """Assert the sample evaluation returns the expected report shape."""
    events, spec, answer_text = run.sample_inputs()
    report = run.evaluate_run(events, spec, answer_text)
    expected_top_level = {
        "evaluation_id",
        "passed",
        "scores",
        "counts",
        "by_domain",
        "by_document_type",
        "findings",
    }
    assert expected_top_level.issubset(report.keys()), report
    assert report["evaluation_id"] == "sample-benefits-rag", report
    assert report["passed"] is True, report
    assert report["scores"]["overall"] == 1.0, report
    assert report["counts"]["required_documents"] == 2, report
    assert report["counts"]["covered_citations"] == 2, report
    assert report["counts"]["forbidden_sources_used"] == 0, report
    assert report["by_domain"]["benefits"]["retrieval_hit_rate"] == 1.0, report
    assert report["findings"] == [], report
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
