#!/usr/bin/env python3
"""Tiny self-test for the TraceBloom reference implementation."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run  # noqa: E402


def main() -> int:
    """Assert the core dataset builder returns the expected shape."""

    result = run.build_dataset_from_texts(
        run.SAMPLE_ANSWERS,
        run.SAMPLE_RETRIEVAL_LOG,
        input_ref="test.md",
        default_confidence=0.95,
        max_negatives_per_query=3,
    )

    assert set(result) == {"records", "review_queue", "summary"}
    assert result["summary"] == {
        "queries": 1,
        "positives": 2,
        "implicit_negative_candidates": 2,
        "review_items": 1,
    }
    assert len(result["records"]) == 4
    assert result["records"][0]["label"] == "positive"
    assert result["records"][0]["query_id"] == "q-001"
    assert {"query_id", "query", "doc_id", "label", "confidence", "evidence"} <= set(result["records"][0])
    assert result["records"][-1]["label"] == "implicit_negative_candidate"
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
