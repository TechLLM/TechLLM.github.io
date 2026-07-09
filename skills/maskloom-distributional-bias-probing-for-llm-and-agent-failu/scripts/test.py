"""Tiny self-test for the MaskLoom reference implementation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""

    run_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("maskloom_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Run assertions against built-in sample data."""

    run = load_run_module()
    report = run.run_probe(run.SAMPLE_INPUT, trials=6, mask_probability=0.2, seed=11)

    assert report["schema_version"] == "maskloom.report.v1"
    assert report["probe"]["trials_completed"] == 6
    assert report["baseline"]["selected_id"] == "billing"
    assert len(report["selection_distribution"]) == 3
    assert sum(row["count"] for row in report["selection_distribution"]) == 6
    assert isinstance(report["sensitive_spans"], list)
    assert isinstance(report["bias_suspects"], list)
    assert len(report["trials"]) == 6
    assert all("selected_id" in trial for trial in report["trials"])

    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
