#!/usr/bin/env python3
"""Tiny self-test for the SurfacePilot reference implementation."""

import run


def main() -> int:
    """Assert that the core profiler returns the expected shape on sample data."""
    profile = run.build_profile(run.sample_events())

    assert set(profile) == {"summary", "matrix", "patterns", "routing_policy"}
    assert profile["summary"]["events"] == 5
    assert profile["summary"]["passed"] == 1
    assert profile["summary"]["failed"] == 4
    assert isinstance(profile["matrix"], list)
    assert "signal" in profile["matrix"][0]
    assert isinstance(profile["patterns"], list)
    assert isinstance(profile["routing_policy"]["rules"], list)

    first_rule = profile["routing_policy"]["rules"][0]
    assert set(first_rule) == {"id", "match", "when", "action", "evidence"}
    assert "task_type" in first_rule["match"]
    assert "surface" in first_rule["match"]
    assert first_rule["evidence"]["failures"] >= 1

    signals = {pattern["signal"] for pattern in profile["patterns"]}
    assert "stale_retrieval" in signals
    assert "malformed_api_call" in signals

    rendered = run.render_profile(profile, "yaml")
    assert rendered.startswith("summary:\n")
    assert "routing_policy:" in rendered

    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
