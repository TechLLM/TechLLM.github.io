#!/usr/bin/env python3
"""Tiny self-test for the ShardRelay reference implementation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_run_module():
    """Load scripts/run.py without requiring package installation."""

    path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("shardrelay_run", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert that the core scheduler returns the expected shape."""

    run = load_run_module()
    result = run.schedule_contexts(run.sample_stages(), run.sample_shards())
    assert result["tool"] == "ShardRelay"
    assert result["version"] == "0.1.0"
    assert "contexts" in result
    assert len(result["stages"]) == 2
    compact = run.summarize_for_stdout(result)
    assert compact == {
        "stages": [
            {"id": "stage_001", "selected_shards": ["project_brief", "dag_notes"]},
            {"id": "stage_002", "selected_shards": ["handoff_log", "project_brief"]},
        ]
    }
    for stage in result["stages"]:
        assert stage["output_file"] in result["contexts"]
        assert stage["selected_shards"]
        assert stage["estimated_tokens"] <= stage["budget"]
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
