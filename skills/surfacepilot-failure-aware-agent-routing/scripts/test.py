"""Tiny self-test for the SurfacePilot router."""

from run import SAMPLE_TASK, SAMPLE_TOOLS, analyze_task


def test_sample_shape() -> None:
    """Assert that the built-in sample returns the expected output shape."""

    result = analyze_task(SAMPLE_TASK, SAMPLE_TOOLS)
    assert isinstance(result, dict)
    assert result["task"] == SAMPLE_TASK
    assert result["recommendation"]["route"] == "human_review"
    assert isinstance(result["recommendation"]["confidence"], float)
    assert result["recommendation"]["required_surfaces"] == [
        "file_edit",
        "service_call",
        "data_transform",
        "state_verification",
    ]
    assert result["risk"]["level"] == "high"
    assert set(result["risk"]["surfaces"]) == {
        "retrieval",
        "file_edit",
        "service_call",
        "data_transform",
        "state_verification",
    }
    for surface_result in result["risk"]["surfaces"].values():
        assert set(surface_result) == {
            "score",
            "level",
            "signals",
            "available_tools",
            "missing_capability",
        }
    assert "actions" in result and result["actions"]
    assert result["tools_considered"] == [
        "repo_read",
        "apply_patch",
        "stripe_sandbox",
        "pytest",
    ]
    assert result["policy"]["version"] == "surfacepilot-policy-v1"


if __name__ == "__main__":
    test_sample_shape()
    print("surfacepilot self-test passed")
