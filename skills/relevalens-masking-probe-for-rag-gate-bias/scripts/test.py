#!/usr/bin/env python3
"""Self-test for the RelevaLens offline masking probe."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""

    script_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("relevalens_run", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert the built-in sample returns the expected result shape."""

    run = load_run_module()
    result = run.run_probe(run.SAMPLE_QUERIES, run.SAMPLE_CANDIDATES, run.SAMPLE_SCORES)
    assert set(result) == {"summary", "queries", "candidates"}
    assert result["summary"]["query_count"] == 1
    assert result["summary"]["candidate_count"] == 3
    assert result["summary"]["score_count"] == 12
    assert result["summary"]["flags"] == ["position_skew", "rank_instability"]
    assert len(result["queries"]) == 1
    assert len(result["candidates"]) == 3
    first_candidate = result["candidates"][0]
    assert {
        "query_id",
        "candidate_id",
        "baseline_rank",
        "position",
        "baseline_score",
        "masked_mean",
        "mask_delta",
        "concentration_share",
    }.issubset(first_candidate)
    assert first_candidate["candidate_id"] == "d1"
    assert first_candidate["mask_delta"] == 0.4067
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
