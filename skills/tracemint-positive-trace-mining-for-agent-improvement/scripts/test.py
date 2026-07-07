#!/usr/bin/env python3
"""Small import-level self-test for the TraceMint reference CLI."""

from run import SAMPLE_RUNS, mine_positive_traces, render_markdown


def main() -> int:
    """Assert the sample positive trace has the expected public shape."""

    traces = mine_positive_traces(SAMPLE_RUNS)
    assert len(traces) == 1
    trace = traces[0]
    assert set(trace) == {
        "artifacts",
        "event_count",
        "events",
        "evidence",
        "score",
        "task",
        "tools",
        "trace_id",
    }
    assert trace["trace_id"] == "run-pass-001"
    assert trace["event_count"] == 6
    assert trace["tools"] == ["read_file", "edit_file"]
    assert trace["evidence"][0]["source"] == "docs/parser.md"
    assert trace["artifacts"][0]["kind"] == "patch_summary"
    markdown = render_markdown(traces)
    assert "## Trace run-pass-001" in markdown
    assert "### Event Sequence" in markdown
    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
