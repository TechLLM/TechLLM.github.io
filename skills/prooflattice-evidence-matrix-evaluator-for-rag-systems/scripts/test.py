"""Tiny self-test for the ProofLattice reference evaluator."""

import run


def main() -> int:
    """Assert that the sample evaluator output has the expected shape."""
    result = run.evaluate_case(run.sample_input())

    assert set(result) == {"checklist", "evidence_map"}
    checklist = result["checklist"]
    evidence_map = result["evidence_map"]

    assert checklist["overall_status"] == "pass"
    assert isinstance(checklist["overall_score"], float)
    assert len(checklist["principles"]) == 6
    assert {item["name"] for item in checklist["principles"]} == {
        "directness",
        "evidence_coverage",
        "citation_support",
        "omission_risk",
        "freshness",
        "factual_alignment",
    }

    assert evidence_map["evaluation_id"] == checklist["evaluation_id"]
    assert len(evidence_map["claim_nodes"]) == 2
    assert len(evidence_map["document_nodes"]) == 2
    assert len(evidence_map["edges"]) == 2
    assert all(claim["supported"] for claim in evidence_map["claim_nodes"])
    assert all(claim["citation_supported"] for claim in evidence_map["claim_nodes"])

    print("scripts/test.py: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
