"""Tiny self-test for the SliceLens CLI module."""

from __future__ import annotations

import run


def main() -> None:
    """Assert the built-in sample returns the expected analysis shape."""
    report = run.analyze_rows(run.sample_rows())

    expected_top_level = {
        "row_count",
        "overall_mean",
        "score_column",
        "source_column",
        "target_column",
        "slice_columns",
        "min_count",
        "transfer_matrix",
        "worst_slice",
        "domain_gaps",
        "slice_tables",
        "missing_field_degradation",
        "warnings",
    }
    assert expected_top_level.issubset(report.keys())
    assert report["row_count"] == 12
    assert report["overall_mean"] == 0.653
    assert report["worst_slice"] == {
        "dimension": "condition",
        "value": "missing_metadata",
        "count": 3,
        "mean": 0.413,
    }
    assert report["transfer_matrix"]["rows"] == ["finance", "legal", "medical"]
    assert report["transfer_matrix"]["columns"] == ["finance", "legal", "medical"]
    assert report["transfer_matrix"]["values"]["finance"]["finance"] == {
        "mean": 0.895,
        "count": 2,
    }
    assert report["domain_gaps"][0]["source_domain"] == "finance"
    assert report["domain_gaps"][0]["gap"] == 0.41
    assert "document_type" in report["slice_tables"]
    assert report["missing_field_degradation"][3]["field"] == "document_type"
    assert report["missing_field_degradation"][3]["missing_count"] == 1

    rendered = run.render_markdown(report)
    assert "# SliceLens Evaluation Report" in rendered
    assert "| condition | missing_metadata | 0.413 | 3 |" in rendered
    print("scripts/test.py: OK")


if __name__ == "__main__":
    main()
