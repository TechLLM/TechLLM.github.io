#!/usr/bin/env python3
"""Independent offline tests for the public ParallaxPack core function."""

import json
from pathlib import Path

import run


def test_realistic_example():
    """Assert that the realistic example exactly matches its checked-in output."""
    root = Path(__file__).resolve().parents[1]
    with (root / "examples" / "input.json").open(encoding="utf-8") as handle:
        data = json.load(handle)
    with (root / "examples" / "expected-output.json").open(encoding="utf-8") as handle:
        expected = json.load(handle)
    actual = run.rerank_evidence(data)
    assert actual == expected
    assert actual["summary"] == {
        "candidate_count": 6,
        "selected_count": 4,
        "excluded_count": 2,
    }
    assert actual["baseline_comparison"]["parallaxpack"]["metrics"]["community_count"] >= 3


def test_duplicate_id_is_rejected():
    """Assert that an invalid duplicate candidate ID fails validation."""
    invalid = {
        "query": "incident",
        "graph": {"edges": []},
        "notes": [
            {
                "id": "duplicate",
                "title": "First",
                "text": "incident",
                "community": "ops",
                "updated_at": "2026-01-01",
            },
            {
                "id": "duplicate",
                "title": "Second",
                "text": "incident",
                "community": "support",
                "updated_at": "2026-01-02",
            },
        ],
    }
    try:
        run.rerank_evidence(invalid)
    except run.ValidationError as exc:
        assert "duplicate note id" in str(exc)
    else:
        raise AssertionError("duplicate note IDs must raise ValidationError")


if __name__ == "__main__":
    test_realistic_example()
    test_duplicate_id_is_rejected()
    print("2 tests passed")

