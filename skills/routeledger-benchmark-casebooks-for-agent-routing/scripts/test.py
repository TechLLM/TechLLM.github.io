#!/usr/bin/env python3
"""Tiny self-test for the RouteLedger runner."""

import run


def main() -> int:
    """Assert that the built-in sample produces the expected manifest shape."""
    manifest = run.build_casebook(run.SAMPLE_RECORDS, seed=13)
    assert manifest["tool"] == "RouteLedger"
    assert manifest["version"] == run.VERSION
    assert manifest["record_count"] == 6
    assert manifest["valid_record_count"] == 6
    assert manifest["invalid_record_count"] == 0
    assert set(manifest["splits"]) == {"train", "validation", "test"}
    assert len(manifest["cases"]) == 6
    assert all("route_slice" in case for case in manifest["cases"])
    assert all(case["split"] in {"train", "validation", "test"} for case in manifest["cases"])
    assert "coverage" in manifest and "domain" in manifest["coverage"]
    assert isinstance(manifest["weak_slices"], list)
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
