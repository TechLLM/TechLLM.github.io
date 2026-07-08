#!/usr/bin/env python3
"""Tiny import-level self-test for the FaultLoom reference CLI."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


def load_run_module():
    """Import scripts/run.py without requiring package installation."""
    module_path = Path(__file__).with_name("run.py")
    spec = importlib.util.spec_from_file_location("faultloom_run", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import scripts/run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Assert the core benchmark builder returns the expected shape."""
    run_module = load_run_module()
    result = run_module.build_benchmark(copy.deepcopy(run_module.SAMPLE_PAYLOAD))

    suite = result["benchmark_suite"]
    cases = suite["cases"]

    assert suite["name"] == "social-publishing-failures-demo"
    assert suite["version"] == "0.1"
    assert len(cases) == 3
    assert cases[0]["classification"]["category"] == "authentication"
    assert cases[0]["classification"]["retryable"] is False
    assert cases[1]["classification"]["category"] == "rate_limit"
    assert cases[1]["evaluation"]["should_retry"] is True
    assert cases[2]["classification"]["category"] == "media_validation"
    assert cases[0]["source"]["error_excerpt"].find("EAAB_SAMPLE_TOKEN") == -1
    assert "[REDACTED]" in cases[0]["source"]["error_excerpt"]
    assert set(cases[0]) == {
        "id",
        "provider",
        "operation",
        "source",
        "classification",
        "expected_recovery",
        "evaluation",
    }

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
