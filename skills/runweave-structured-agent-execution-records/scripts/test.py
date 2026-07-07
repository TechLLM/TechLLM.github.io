"""Tiny self-test for the RunWeave reference CLI module."""

from __future__ import annotations

import run


def test_sample_record_shape() -> None:
    """Assert that the built-in sample returns the expected normalized shape."""
    record = run.build_agent_run_record(
        run.SAMPLE_LOG,
        run.SAMPLE_PLAN,
        source={"log": "builtin:sample", "plan": "builtin:sample"},
    )

    assert record["schema_version"] == "runweave.agent_run_record.v1"
    assert record["run_id"] == "sample-run"
    assert record["summary"] == {
        "planned_steps": 2,
        "executed_steps": 2,
        "matched_steps": 2,
        "failed_steps": 1,
        "missing_planned_steps": 0,
        "repair_candidates": 1,
    }
    assert len(record["planned_steps"]) == 2
    assert len(record["executed_steps"]) == 2
    assert len(record["timeline"]) == 5
    assert len(record["failures"]) == 1
    assert record["failures"][0]["executed_step_id"] == "exec-002"
    assert record["failures"][0]["planned_step_id"] == "test"
    assert record["repair_candidates"][0]["failure_step_id"] == "exec-002"
    assert "patch the code" in record["repair_candidates"][0]["command_template"]


if __name__ == "__main__":
    test_sample_record_shape()
    print("ok")
