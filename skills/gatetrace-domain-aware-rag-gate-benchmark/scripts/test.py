#!/usr/bin/env python3
"""Tiny import-based self-test for the GateTrace reference implementation."""

import run as gatetrace


def test_sample_report_shape() -> None:
    """Assert that the built-in sample returns the expected stable shape."""
    report = gatetrace.build_report(gatetrace.sample_records())
    expected_top_level = {
        "summary",
        "overall",
        "query_slices",
        "document_slices",
        "missing_evidence",
        "false_passes",
        "false_blocks",
        "ood_queries",
    }
    assert set(report) == expected_top_level
    assert report["summary"]["query_count"] == 4
    assert report["summary"]["document_count"] == 9
    assert report["summary"]["missing_evidence_query_count"] == 1
    assert report["summary"]["false_pass_count"] == 2
    assert report["summary"]["false_block_count"] == 1
    assert report["overall"]["retrieval_recall"] == 0.8
    assert report["overall"]["retrieval_precision"] == 0.5556
    assert "domain_tag" in report["query_slices"]
    assert "doc_type" in report["document_slices"]


def main() -> int:
    """Run the test without requiring a test framework."""
    test_sample_report_shape()
    print("GateTrace self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
