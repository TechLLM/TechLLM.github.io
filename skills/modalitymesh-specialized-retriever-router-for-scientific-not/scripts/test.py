#!/usr/bin/env python3
"""Tiny self-test for the ModalityMesh reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""
    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("modalitymesh_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert the built-in sample produces the expected manifest shape."""
    run = load_run_module()
    manifest = run.build_manifest_from_texts(run.SAMPLE_NOTES, policy="balanced")

    assert manifest["schema_version"] == "1.0"
    assert manifest["generator"] == "modalitymesh"
    assert manifest["policy"] == "balanced"
    assert manifest["source_count"] == 1
    assert manifest["modalities"] == ["table", "formula", "code", "citation", "timeline", "benchmark"]

    file_record = manifest["files"][0]
    assert file_record["path"] == "scientific_notes.md"
    assert file_record["tags"] == ["table", "formula", "code", "citation", "timeline", "benchmark"]
    assert "table-structure" in file_record["recommended_scorers"]
    assert "symbolic-formula" in file_record["recommended_scorers"]
    assert "code-semantic" in file_record["recommended_scorers"]
    assert "citation-graph" in file_record["recommended_scorers"]
    assert "temporal-date" in file_record["recommended_scorers"]
    assert "benchmark-reranker" in file_record["recommended_scorers"]

    evidence = file_record["evidence"]
    assert len(evidence) == 6
    for item in evidence:
        assert set(item) == {"modality", "block_type", "line_start", "line_end", "reason", "snippet"}
        assert isinstance(item["line_start"], int)
        assert isinstance(item["line_end"], int)
        assert item["line_start"] <= item["line_end"]
        assert item["snippet"]

    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
