#!/usr/bin/env python3
"""Tiny self-test for the BiasLens RAG reference implementation."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run as biaslens_run  # noqa: E402


def test_sample_report_shape() -> None:
    """Assert the sample report has the expected deterministic shape."""

    report = biaslens_run.diagnose(
        query=biaslens_run.SAMPLE_QUERY,
        candidates=biaslens_run.SAMPLE_CANDIDATES,
    )

    assert report["query"] == biaslens_run.SAMPLE_QUERY
    assert report["candidate_count"] == 4
    assert report["trials_per_candidate"] == 5
    assert report["baseline_ranking"][0]["id"] == "kb-001"
    assert set(report["failure_modes"]) == {
        "knowledge_gap",
        "ambiguity_bias",
        "precision_bias",
        "position_bias",
    }
    assert isinstance(report["diagnostics"], list)
    assert len(report["diagnostics"]) == 4

    first = report["diagnostics"][0]
    expected_keys = {
        "id",
        "original_position",
        "baseline_score",
        "mean_perturbed_score",
        "score_stddev",
        "score_drop",
        "keyword_reliance",
        "partial_evidence_volatility",
        "position_sensitivity",
        "coverage",
        "matched_terms",
        "missing_terms",
        "diagnostic_label",
        "notes",
    }
    assert set(first) == expected_keys
    assert first["diagnostic_label"] in {
        "knowledge-gap",
        "ambiguity-bias",
        "precision-bias",
        "stable-evidence",
    }
    assert isinstance(report["recommendations"], list)
    assert report["metadata"]["engine"] == "biaslens-rag-lexical-probe"


if __name__ == "__main__":
    test_sample_report_shape()
    print("scripts/test.py: ok")
