#!/usr/bin/env python3
"""Tiny LedgerSpan self-test for the importable core function."""

from pathlib import Path
import importlib.util


RUN_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("ledgerspan_run", RUN_PATH)
assert SPEC and SPEC.loader
run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run)


def test_sample_shape() -> None:
    """Assert the sample ledger has the expected stable shape."""

    ledger = run.create_evidence_ledger(
        run.sample_before_files(),
        run.sample_after_files(),
        run.sample_commands(),
        run.sample_tool_traces(),
        run.sample_checklist(),
        {"run_id": "sample-run-001", "actor": "sample-agent"},
    )

    assert ledger["ledger_version"] == "0.1.0"
    assert ledger["run"]["id"] == "sample-run-001"
    assert set(ledger.keys()) == {
        "ledger_version",
        "run",
        "workspace",
        "changes",
        "commands",
        "tool_calls",
        "artifacts",
        "verification",
    }
    assert len(ledger["changes"]["created"]) == 1
    assert len(ledger["changes"]["modified"]) == 1
    assert len(ledger["changes"]["deleted"]) == 1
    assert len(ledger["changes"]["renamed"]) == 1
    assert ledger["commands"]["summary"]["total"] == 1
    assert ledger["tool_calls"]["summary"]["by_kind"]["search"] == 1
    assert ledger["artifacts"][0]["path"] == "docs/evidence.md"
    assert ledger["verification"]["status"] == "pass"
    assert ledger["verification"]["failed"] == 0


if __name__ == "__main__":
    test_sample_shape()
    print("scripts/test.py: ok")
