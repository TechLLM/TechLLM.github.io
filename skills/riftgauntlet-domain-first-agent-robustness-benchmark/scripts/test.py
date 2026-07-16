#!/usr/bin/env python3
"""Independent offline tests for the RiftGauntlet public benchmark core."""

from __future__ import annotations

import copy

from run import BUILTIN_SPEC, BUILTIN_TRACES, ValidationError, run_benchmark


def test_realistic_valid_case() -> None:
    """Verify the realistic multi-domain sample and its ranked degradation metrics."""

    result = run_benchmark(BUILTIN_TRACES, BUILTIN_SPEC, worst_limit=5)
    assert result.report["summary"]["perturbed_cases"] == 7
    assert result.report["summary"]["robustness_delta"] == -0.857143
    assert result.report["failure_detection"]["auroc_proxy"] == 0.5
    assert result.report["worst_slices"][0]["scenario"] == "delayed-result"
    unknown = next(item for item in result.report["domains"] if item["domain"] == "unknown")
    assert unknown["perturbed_success_rate"] == 1.0
    assert unknown["source_domains"] == ["finance"]


def test_invalid_duplicate_trace_id() -> None:
    """Verify that ambiguous duplicate trace identifiers fail before replay."""

    invalid_traces = copy.deepcopy(BUILTIN_TRACES)
    invalid_traces[1]["id"] = invalid_traces[0]["id"]
    try:
        run_benchmark(invalid_traces, BUILTIN_SPEC)
    except ValidationError as error:
        assert str(error) == "trace ids must be unique"
    else:
        raise AssertionError("duplicate trace ids should raise ValidationError")


def main() -> None:
    """Run both tests without requiring a third-party test framework."""

    test_realistic_valid_case()
    test_invalid_duplicate_trace_id()
    print("2 tests passed")


if __name__ == "__main__":
    main()
