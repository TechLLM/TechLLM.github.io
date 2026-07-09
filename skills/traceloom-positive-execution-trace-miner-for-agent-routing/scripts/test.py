#!/usr/bin/env python3
"""Self-test for the TraceLoom reference implementation."""

import json

import run


def main() -> int:
    """Assert that the sample miner returns the expected positive record shape."""
    records = run.mine_positive_traces(run.sample_trace_events(), run.sample_grader_results())

    assert isinstance(records, list)
    assert len(records) == 1

    record = records[0]
    assert set(record.keys()) == {
        "task_id",
        "run_id",
        "success_condition",
        "tool_sequence",
        "tool_calls",
        "file_patterns",
        "retrieval_paths",
        "routing_signals",
    }
    assert record["task_id"] == "task-alpha"
    assert record["run_id"] == "run-001"
    assert record["success_condition"] == "passed=true; score=1.0"
    assert record["tool_sequence"] == ["file.read", "search.query", "file.write", "test.run"]
    assert record["file_patterns"] == {
        "read": ["src/router.py"],
        "write": ["src/router.py"],
        "touched": ["src/router.py"],
    }
    assert record["retrieval_paths"] == [
        {
            "order": 1,
            "source": "docs/router-policy.md",
            "query_summary": {"chars": 26, "words": 3},
        }
    ]
    assert record["routing_signals"] == {
        "tool_count": 4,
        "retrieval_count": 1,
        "file_count": 1,
        "normalized_tool_path": "file.read>search.query>file.write>test.run",
    }

    json.loads(run.records_to_jsonl(records).splitlines()[0])
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
