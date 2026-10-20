#!/usr/bin/env python3
"""Independent tests for LazarusClip.

Imports scripts/run.py and exercises the same public ``recover`` function the
CLI uses: one realistic valid case checked byte-for-byte against the committed
expected output, plus invalid and edge cases. Fully offline and deterministic.

Run with: python scripts/test.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXAMPLES = ROOT / "examples"
INPUTS = EXAMPLES / "input"
OUTPUTS = EXAMPLES / "output"

_spec = importlib.util.spec_from_file_location("lazarusclip_run", HERE / "run.py")
if _spec is None or _spec.loader is None:
    raise SystemExit("error: could not load scripts/run.py next to this test")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)


def _load(path: Path) -> dict:
    """Load a JSON file, failing with a clear message if it is missing."""
    if not path.is_file():
        raise SystemExit(f"error: missing fixture {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def _pair(name: str) -> tuple[dict, dict]:
    """Load the ``<name>.input.json`` / ``<name>.output.json`` example pair."""
    return (
        _load(INPUTS / f"{name}.input.json"),
        _load(OUTPUTS / f"{name}.output.json"),
    )


def test_every_input_example_has_a_matching_output() -> None:
    """Each examples/input/<name>.input.json has an examples/output counterpart."""
    inputs = sorted(p.name[: -len(".input.json")] for p in INPUTS.glob("*.input.json"))
    outputs = sorted(p.name[: -len(".output.json")] for p in OUTPUTS.glob("*.output.json"))
    assert inputs, "no example inputs found under examples/input"
    assert inputs == outputs, f"unpaired examples: inputs={inputs} outputs={outputs}"


def test_all_example_pairs_reproduce_their_output() -> None:
    """Running recover() on every example input reproduces its committed output."""
    for path in sorted(INPUTS.glob("*.input.json")):
        name = path.name[: -len(".input.json")]
        trace, expected = _pair(name)
        assert run.recover(trace) == expected, f"{name}: record does not match examples/output"


def test_valid_tool_failure_matches_expected() -> None:
    """A realistic failed run reproduces the committed expected record exactly."""
    trace, expected = _pair("trace_tool_failure")
    actual = run.recover(trace)

    assert actual == expected, "recovered record does not match examples/output"
    assert actual["fatal_step_index"] == 8, actual["fatal_step_index"]
    assert actual["suggested_label"] == "recoverable", actual["suggested_label"]
    assert actual["pre_failure_subgraph"]["step_count"] == 8
    assert actual["masked_tail"]["step_count"] == 3
    assert actual["mask_hints"]["mask_step_indices"] == [8, 9, 10]
    # The prefix and the tail must partition the trace with no overlap.
    keep = actual["mask_hints"]["keep_step_indices"]
    mask = actual["mask_hints"]["mask_step_indices"]
    assert keep + mask == list(range(actual["step_count"]))


def test_clean_run_has_no_boundary() -> None:
    """A successful run yields no fatal boundary and an empty masked tail."""
    trace, expected = _pair("trace_clean_run")
    actual = run.recover(trace)

    assert actual == expected, "clean-run record does not match examples/output"
    assert actual["fatal_step_index"] is None
    assert actual["suggested_label"] == "clean"
    assert actual["masked_tail"]["step_count"] == 0


def test_deterministic_across_calls_and_passes() -> None:
    """Offline recovery is deterministic and pass count does not move the verdict."""
    trace, _ = _pair("trace_tool_failure")
    first, second = run.recover(trace), run.recover(trace)
    assert first == second, "offline recovery is not deterministic"
    assert run.recover(trace, passes=7)["fatal_step_index"] == first["fatal_step_index"]


def test_early_failure_is_poisoned() -> None:
    """A trace that fails before any reasoning has no salvageable prefix."""
    record = run.recover(
        {
            "trace_id": "edge-early-failure",
            "steps": [
                {"role": "user", "type": "message", "content": "Fetch the dashboard."},
                {"role": "tool", "type": "tool_result", "status": "error",
                 "content": "HTTP 500 internal server error"},
            ],
        }
    )
    assert record["fatal_step_index"] == 1, record["fatal_step_index"]
    assert record["suggested_label"] == "poisoned", record["suggested_label"]


def test_invalid_traces_are_rejected() -> None:
    """Malformed input raises TraceValidationError instead of producing a record."""
    bad_inputs = [
        ({"steps": []}, "empty step list"),
        ({"steps": "not-a-list"}, "steps of the wrong type"),
        ({"trace_id": "x"}, "missing steps key"),
        ({"steps": [{"content": "no role here"}]}, "step without a role"),
        ({"steps": ["just a string"]}, "non-object step"),
        (42, "scalar instead of a trace"),
    ]
    for payload, description in bad_inputs:
        try:
            run.recover(payload)
        except run.TraceValidationError:
            continue
        raise AssertionError(f"expected TraceValidationError for {description}")


def test_invalid_options_are_rejected() -> None:
    """Bad option values raise ValueError before any work is done."""
    trace = {"steps": [{"role": "user", "content": "hi"}]}
    for kwargs in ({"judge": "not-a-backend"}, {"passes": 0}, {"min_prefix_steps": -1}):
        try:
            run.recover(trace, **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {kwargs}")


def test_cli_exits_nonzero_on_invalid_input() -> None:
    """The CLI reports a non-zero exit code for a missing input file."""
    assert run.main(["--input", "examples/input/does-not-exist.input.json"]) == 2


def test_batch_triage_summarizes_labels() -> None:
    """Batch mode processes every example trace and counts the labels."""
    paths = sorted(INPUTS.glob("*.json"))
    assert paths, "no example traces found"
    result = run.recover_batch(paths)
    assert result["processed"] == len(paths)
    assert result["failed"] == 0
    assert result["label_counts"]["recoverable"] >= 1
    assert result["label_counts"]["clean"] >= 1
    assert [r["source"] for r in result["records"]] == [p.name for p in paths]


def main() -> int:
    """Run every test function and report results."""
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"[FAIL] {test.__name__}: {exc}")
        else:
            print(f"[PASS] {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
