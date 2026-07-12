#!/usr/bin/env python3
"""Tiny self-test for the DiffSentinel reference implementation."""

import run


def main() -> int:
    """Assert that the built-in sample returns the expected report shape."""
    before = run.normalize_snapshot(run.sample_before_snapshot())
    after = run.normalize_snapshot(run.sample_after_snapshot())
    report = run.evaluate(before, after, run.sample_trace_events(), run.DEFAULT_CONFIG)

    assert report["schema_version"] == "diffsentinel-report-v1"
    assert report["summary"]["status"] == "pass"
    assert report["summary"]["overall_score"] == 100
    assert report["summary"]["counts"] == {
        "created": 1,
        "modified": 1,
        "deleted": 0,
        "renamed": 0,
        "unchanged": 1,
        "violations": 0,
    }
    assert report["state_diff"]["created"] == ["docs/faq.md"]
    assert report["state_diff"]["modified"] == ["docs/guide.md"]
    assert report["violations"] == []
    assert isinstance(report["trace"]["tools"], dict)
    assert isinstance(report["graph"]["added_links"], list)
    assert isinstance(report["findings"], list)
    print("DiffSentinel self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
