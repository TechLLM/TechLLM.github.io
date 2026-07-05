#!/usr/bin/env python3
"""Tiny self-test for the Nodewright reference scanner."""

from __future__ import annotations

from run import SAMPLE_MARKDOWN, analyze_markdown_text, format_jsonl


def test_sample_shape() -> None:
    """Assert the built-in sample returns stable evidence node fields."""

    nodes = analyze_markdown_text(SAMPLE_MARKDOWN, source_identifier="sample.md")
    assert len(nodes) == 2

    required_fields = {
        "node_id",
        "source_identifier",
        "content_hash",
        "section_anchor",
        "section_title",
        "affordances",
        "retrieval_role",
        "recommended_tool",
        "confidence",
        "routing_notes",
        "source_metadata",
    }

    for node in nodes:
        assert required_fields.issubset(node.keys())
        assert node["node_id"].startswith("nw_")
        assert node["source_identifier"] == "sample.md"
        assert isinstance(node["affordances"], list)
        assert isinstance(node["routing_notes"], list)
        assert 0.0 <= node["confidence"] <= 1.0
        assert "source_path" in node["source_metadata"]

    roles = {node["retrieval_role"] for node in nodes}
    assert roles == {"run_code", "execute_checklist"}
    assert "table" in nodes[0]["affordances"]
    assert "code_block" in nodes[0]["affordances"]
    assert "task" in nodes[1]["affordances"]

    jsonl = format_jsonl(nodes)
    assert len(jsonl.strip().splitlines()) == 2


if __name__ == "__main__":
    test_sample_shape()
    print("ok")
