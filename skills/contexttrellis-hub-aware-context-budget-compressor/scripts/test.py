#!/usr/bin/env python3
"""Tiny self-test for the ContextTrellis reference implementation."""

from __future__ import annotations

import run


def test_sample_bundle_shape() -> None:
    """Assert that sample data returns the expected bundle shape."""

    bundle = run.build_context_bundle(
        run.SAMPLE_VAULT,
        requested_tokens=620,
        reserve_tokens=80,
        input_label="test-sample",
    )
    assert bundle["bundle_version"] == "0.1"
    assert bundle["mode"] == "selftest"
    assert bundle["budget"]["used_tokens"] <= bundle["budget"]["available_tokens"]
    assert bundle["graph"]["notes"] == 5
    assert bundle["graph"]["edges"] == 4
    assert bundle["graph"]["hubs"] == ["Architecture.md"]
    assert set(bundle["graph"]["long_tail"]) == {
        "API Polling.md",
        "CLI Commands.md",
        "Dry Run Log.md",
        "Error Handling.md",
    }
    assert bundle["items"][0]["id"] == "Architecture.md"
    assert bundle["items"][0]["role"] == "hub_summary"
    assert {item["role"] for item in bundle["items"]} >= {"hub_summary", "preserved_detail"}
    assert all({"id", "role", "action", "tokens", "reason"} <= set(item) for item in bundle["decisions"])


if __name__ == "__main__":
    test_sample_bundle_shape()
    print("ok")
