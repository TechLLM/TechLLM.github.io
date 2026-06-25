#!/usr/bin/env python3
"""State contract helper for schema templates and lightweight validation.

No external dependencies. This is not a full JSON Schema validator; it enforces
common contract checks used by the state-contract-designer skill.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CORE_FIELDS = [
    "schema_version",
    "trace_id",
    "intent",
    "evidence_type",
    "support_score",
    "risk",
    "next_action",
]

EVIDENCE_TYPES = [
    "none",
    "retrieval",
    "user_provided",
    "tool_output",
    "code_inspection",
    "web_source",
    "mixed",
]

RISKS = ["low", "medium", "high", "blocked"]
NEXT_ACTIONS = ["answer", "retrieve", "ask_user", "execute", "review", "publish", "escalate", "stop"]


def load_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to read JSON from {path}: {exc}")


def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def template() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OpenClawStatePacket",
        "type": "object",
        "additionalProperties": False,
        "required": CORE_FIELDS,
        "properties": {
            "schema_version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
            "trace_id": {"type": "string", "minLength": 3, "maxLength": 120},
            "intent": {"type": "string", "minLength": 3, "maxLength": 80},
            "evidence_type": {"type": "string", "enum": EVIDENCE_TYPES},
            "support_score": {"type": "number", "minimum": 0, "maximum": 1},
            "risk": {"type": "string", "enum": RISKS},
            "next_action": {"type": "string", "enum": NEXT_ACTIONS},
            "source_refs": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["claim", "support_score", "source_refs"],
                    "properties": {
                        "claim": {"type": "string", "maxLength": 240},
                        "support_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "source_refs": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "open_questions": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "constraints": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "routing_hint": {"type": "string", "maxLength": 80},
            "artifact_refs": {"type": "array", "items": {"type": "string", "maxLength": 240}},
            "expires_at": {"type": ["string", "null"]},
        },
    }


def lint_schema(schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for field in CORE_FIELDS:
        if field not in required:
            errors.append(f"missing required core field: {field}")
        if field not in props:
            errors.append(f"missing properties entry for core field: {field}")

    if schema.get("type") != "object":
        errors.append("schema type should be object")
    if schema.get("additionalProperties") is not False:
        errors.append("set additionalProperties=false to prevent prose-like drift")

    score = props.get("support_score", {})
    if score.get("minimum") != 0 or score.get("maximum") != 1:
        errors.append("support_score should define minimum=0 and maximum=1")

    for enum_field, values in [("evidence_type", EVIDENCE_TYPES), ("risk", RISKS), ("next_action", NEXT_ACTIONS)]:
        enum_values = props.get(enum_field, {}).get("enum")
        if not enum_values:
            errors.append(f"{enum_field} should use enum values")
        elif not set(enum_values).issubset(set(values)):
            errors.append(f"{enum_field} contains non-standard enum values: {enum_values}")

    return errors


def validate_packet(packet: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for field in CORE_FIELDS:
        if field not in packet:
            errors.append(f"missing field: {field}")

    if "evidence_type" in packet and packet["evidence_type"] not in EVIDENCE_TYPES:
        errors.append(f"invalid evidence_type: {packet['evidence_type']}")
    if "risk" in packet and packet["risk"] not in RISKS:
        errors.append(f"invalid risk: {packet['risk']}")
    if "next_action" in packet and packet["next_action"] not in NEXT_ACTIONS:
        errors.append(f"invalid next_action: {packet['next_action']}")

    score = packet.get("support_score")
    if not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
        errors.append("support_score must be a number from 0 to 1")

    source_refs = packet.get("source_refs", [])
    if source_refs is None:
        source_refs = []
    if not isinstance(source_refs, list):
        errors.append("source_refs must be an array when present")

    if packet.get("evidence_type") not in (None, "none") and not source_refs:
        errors.append("source_refs required when evidence_type is not none")

    if packet.get("next_action") == "publish" and packet.get("risk") in ("high", "blocked"):
        errors.append("publish is not allowed when risk is high or blocked")

    if packet.get("next_action") == "publish" and isinstance(score, (int, float)) and score < 0.85:
        errors.append("publish requires support_score >= 0.85")

    if packet.get("risk") == "blocked" and packet.get("next_action") not in ("ask_user", "retrieve", "escalate", "stop"):
        errors.append("blocked packets should ask_user, retrieve, escalate, or stop")

    claims = packet.get("claims", [])
    if claims is not None:
        if not isinstance(claims, list):
            errors.append("claims must be an array when present")
        else:
            for i, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    errors.append(f"claims[{i}] must be an object")
                    continue
                if claim.get("support_score", 0) < 0.7 and packet.get("next_action") == "publish":
                    errors.append(f"claims[{i}] has weak support for publish")
                if claim.get("support_score", 0) >= 0.4 and not claim.get("source_refs"):
                    errors.append(f"claims[{i}] needs source_refs")

    return errors


def compact_trace(packet: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["trace_id", "intent", "evidence_type", "support_score", "risk", "next_action", "routing_hint"]
    out = {k: packet.get(k) for k in keys if k in packet}
    out["source_ref_count"] = len(packet.get("source_refs") or [])
    out["claim_count"] = len(packet.get("claims") or [])
    out["open_question_count"] = len(packet.get("open_questions") or [])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="State contract template and validation helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template", help="print a starter JSON Schema")

    lint = sub.add_parser("lint-schema", help="lint a schema for state-contract requirements")
    lint.add_argument("schema")

    validate = sub.add_parser("validate-packet", help="validate a state packet")
    validate.add_argument("packet")

    trace = sub.add_parser("trace", help="print compact trace fields from a packet")
    trace.add_argument("packet")

    args = parser.parse_args()

    if args.cmd == "template":
        print_json(template())
        return 0

    if args.cmd == "lint-schema":
        errors = lint_schema(load_json(args.schema))
    elif args.cmd == "validate-packet":
        errors = validate_packet(load_json(args.packet))
    elif args.cmd == "trace":
        print_json(compact_trace(load_json(args.packet)))
        return 0
    else:
        raise AssertionError(args.cmd)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
