#!/usr/bin/env python3
"""Independent offline tests for FidelityLoom's public core function."""

from __future__ import annotations

from run import FidelityError, audit_traces


def test_valid_trace() -> None:
    """A complete trace that preserves representations should pass cleanly."""

    traces = [
        {
            "trace_id": "clean-001",
            "source": {"pressure": {"value": 101.325, "unit": "kPa"}, "mask": [[1, 0], [0, 1]]},
            "tool_args": {"pressure_kpa": 101.325, "mask": [[1, 0], [0, 1]]},
            "tool_result": {"pressure_kpa": 101.325, "mask": [[1, 0], [0, 1]]},
        }
    ]
    contract = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["pressure", "mask"],
        "properties": {
            "pressure": {
                "type": "number",
                "x-source-path": "pressure.value",
                "x-tool-path": "pressure_kpa",
                "x-result-path": "pressure_kpa",
                "x-source-unit-path": "pressure.unit",
                "x-unit": "kPa",
                "x-precision": 6,
            },
            "mask": {
                "type": "array",
                "x-source-path": "mask",
                "x-tool-path": "mask",
                "x-result-path": "mask",
                "x-dimensions": ["row", "column"],
            },
        }
    }
    report = audit_traces(traces, contract)
    assert report["fidelity_report"]["status"] == "pass"
    assert report["fidelity_report"]["findings"] == []
    assert report["adapter_recommendation"]["fields"][0]["field"] == "mask"


def test_invalid_contract_edge_case() -> None:
    """An invalid precision must be rejected before any audit work."""

    traces = [
        {
            "trace_id": "edge-001",
            "source": {"value": 1.0},
            "tool_args": {"value": 1.0},
            "tool_result": {"value": 1.0},
        }
    ]
    bad_contract = {
        "fields": {
            "value": {
                "source_path": "value",
                "tool_path": "value",
                "precision": 0,
            }
        }
    }
    try:
        audit_traces(traces, bad_contract)
    except FidelityError as exc:
        assert "precision must be a positive integer" in str(exc)
    else:
        raise AssertionError("invalid precision was accepted")


def main() -> None:
    """Run tests without requiring a third-party test framework."""

    test_valid_trace()
    test_invalid_contract_edge_case()
    print("2 tests passed")


if __name__ == "__main__":
    main()
