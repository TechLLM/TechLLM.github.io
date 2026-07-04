"""SurfacePilot command-line router for failure-aware agent routing.

The module scores an agent task across execution surfaces and returns a
deterministic JSON routing recommendation. It intentionally uses only the
Python standard library so the skill can run without installation steps.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


SURFACE_NAMES = [
    "retrieval",
    "file_edit",
    "service_call",
    "data_transform",
    "state_verification",
]

SAMPLE_TASK = (
    "Update the billing migration script, call Stripe sandbox to verify "
    "invoices, and summarize the changed rows."
)

SAMPLE_TOOLS = [
    {"name": "repo_read", "surfaces": ["retrieval"], "risk": "low"},
    {"name": "apply_patch", "surfaces": ["file_edit"], "risk": "high"},
    {"name": "stripe_sandbox", "surfaces": ["service_call"], "risk": "medium"},
    {"name": "pytest", "surfaces": ["state_verification"], "risk": "low"},
]

DEFAULT_POLICY: Dict[str, Any] = {
    "version": "surfacepilot-policy-v1",
    "tool_risk": {"low": 0.02, "medium": 0.08, "high": 0.15},
    "thresholds": {
        "cautious_execution": 0.30,
        "verification_first": 0.50,
        "sandboxing": 0.60,
        "human_review": 0.75,
    },
    "surfaces": {
        "retrieval": {
            "base_risk": 0.10,
            "missing_tool_penalty": 0.30,
            "keywords": [
                "search",
                "lookup",
                "look up",
                "find",
                "retrieve",
                "docs",
                "documentation",
                "web",
                "source",
                "citation",
                "repository",
            ],
            "tool_patterns": ["search", "retrieve", "read", "grep", "rg", "web", "docs"],
        },
        "file_edit": {
            "base_risk": 0.20,
            "missing_tool_penalty": 0.35,
            "keywords": [
                "edit",
                "modify",
                "change",
                "changed",
                "write",
                "patch",
                "commit",
                "delete",
                "refactor",
                "fix",
                "implement",
                "update",
            ],
            "tool_patterns": ["write", "patch", "edit", "apply", "git", "file"],
        },
        "service_call": {
            "base_risk": 0.25,
            "missing_tool_penalty": 0.40,
            "keywords": [
                "api",
                "service",
                "deploy",
                "send",
                "email",
                "payment",
                "stripe",
                "slack",
                "github",
                "post",
                "call",
                "webhook",
                "sandbox",
            ],
            "tool_patterns": [
                "api",
                "http",
                "curl",
                "service",
                "stripe",
                "slack",
                "github",
                "deploy",
                "sandbox",
            ],
        },
        "data_transform": {
            "base_risk": 0.15,
            "missing_tool_penalty": 0.20,
            "keywords": [
                "convert",
                "transform",
                "parse",
                "csv",
                "json",
                "schema",
                "migration",
                "extract",
                "normalize",
                "summarize",
                "rows",
            ],
            "tool_patterns": ["python", "jq", "csv", "json", "sql", "transform", "migration"],
        },
        "state_verification": {
            "base_risk": 0.18,
            "missing_tool_penalty": 0.35,
            "keywords": [
                "verify",
                "test",
                "assert",
                "validate",
                "check",
                "state",
                "regression",
                "qa",
                "screenshot",
            ],
            "tool_patterns": ["test", "pytest", "verify", "check", "browser", "lint", "qa"],
        },
    },
    "route_actions": {
        "direct_execution": ["Run directly with normal logging."],
        "cautious_execution": [
            "Run with explicit step logging.",
            "Keep state-changing steps reversible where possible.",
        ],
        "verification_first": [
            "Write or select verification steps before execution.",
            "Run validation after each state-changing step.",
        ],
        "sandboxing": [
            "Use sandbox or dry-run mode for service calls.",
            "Block production credentials and irreversible operations.",
        ],
        "human_review": [
            "Require human approval before state-changing steps.",
            "Separate planning from execution.",
            "Run verification after each execution surface completes.",
        ],
    },
}


class SurfacePilotError(ValueError):
    """Raised when user input cannot be parsed or routed."""


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse the small YAML subset used for SurfacePilot policy files.

    Supported syntax is nested mappings, scalar values, and scalar lists using
    two-space indentation. This is intentionally not a full YAML parser.
    """

    tokens: List[Tuple[int, str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip(" "))]:
            raise SurfacePilotError(f"YAML line {line_number}: tabs are not supported")
        stripped = raw_line.split(" #", 1)[0].rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        tokens.append((indent, stripped.strip()))

    if not tokens:
        return {}

    def parse_scalar(value: str) -> Any:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none"}:
            return None
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        if tokens[index][1].startswith("- "):
            return parse_list(index, indent)
        return parse_dict(index, indent)

    def parse_dict(index: int, indent: int) -> Tuple[Dict[str, Any], int]:
        result: Dict[str, Any] = {}
        while index < len(tokens):
            current_indent, content = tokens[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SurfacePilotError(f"YAML indentation error near: {content}")
            if content.startswith("- "):
                break
            if ":" not in content:
                raise SurfacePilotError(f"YAML mapping entry needs ':': {content}")
            key, raw_value = content.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if not key:
                raise SurfacePilotError(f"YAML mapping entry has an empty key: {content}")
            if raw_value:
                result[key] = parse_scalar(raw_value)
                index += 1
                continue
            if index + 1 >= len(tokens) or tokens[index + 1][0] <= current_indent:
                result[key] = {}
                index += 1
                continue
            result[key], index = parse_block(index + 1, tokens[index + 1][0])
        return result, index

    def parse_list(index: int, indent: int) -> Tuple[List[Any], int]:
        result: List[Any] = []
        while index < len(tokens):
            current_indent, content = tokens[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SurfacePilotError(f"YAML indentation error near: {content}")
            if not content.startswith("- "):
                break
            item = content[2:].strip()
            if not item:
                if index + 1 >= len(tokens):
                    raise SurfacePilotError("YAML list item is empty")
                value, index = parse_block(index + 1, tokens[index + 1][0])
                result.append(value)
                continue
            result.append(parse_scalar(item))
            index += 1
        return result, index

    parsed, next_index = parse_block(0, tokens[0][0])
    if next_index != len(tokens):
        raise SurfacePilotError(f"YAML parser stopped early near: {tokens[next_index][1]}")
    if not isinstance(parsed, dict):
        raise SurfacePilotError("YAML policy root must be a mapping")
    return parsed


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a recursive merge where override values replace base values."""

    merged: Dict[str, Any] = deepcopy(dict(base))
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_policy(path: Optional[str]) -> Tuple[Dict[str, Any], str]:
    """Load the default policy plus optional YAML overrides."""

    env_path = os.environ.get("SURFACEPILOT_POLICY")
    policy_path = path or env_path
    if not policy_path:
        return deepcopy(DEFAULT_POLICY), "default"

    try:
        text = Path(policy_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SurfacePilotError(f"Could not read policy file '{policy_path}': {exc}") from exc

    overrides = parse_simple_yaml(text)
    return deep_merge(DEFAULT_POLICY, overrides), policy_path


def infer_tool_surfaces(tool_name: str, policy: Mapping[str, Any]) -> List[str]:
    """Infer likely execution surfaces from a tool name and policy patterns."""

    lowered = tool_name.lower()
    inferred: List[str] = []
    surfaces = policy.get("surfaces", {})
    for surface in SURFACE_NAMES:
        config = surfaces.get(surface, {})
        patterns = config.get("tool_patterns", [])
        if any(str(pattern).lower() in lowered for pattern in patterns):
            inferred.append(surface)
    return inferred


def normalize_tools(tools: Any, policy: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Normalize user-provided tool metadata into name, surfaces, and risk fields."""

    if tools is None:
        return []
    if not isinstance(tools, list):
        raise SurfacePilotError("'tools' must be a list")

    normalized: List[Dict[str, Any]] = []
    for index, tool in enumerate(tools):
        if isinstance(tool, str):
            name = tool
            surfaces = infer_tool_surfaces(name, policy)
            risk = "medium"
        elif isinstance(tool, Mapping):
            name_value = tool.get("name")
            if not isinstance(name_value, str) or not name_value.strip():
                raise SurfacePilotError(f"Tool at index {index} needs a non-empty string name")
            name = name_value.strip()
            raw_surfaces = tool.get("surfaces")
            if raw_surfaces is None:
                surfaces = infer_tool_surfaces(name, policy)
            elif isinstance(raw_surfaces, list):
                surfaces = [str(surface) for surface in raw_surfaces if str(surface) in SURFACE_NAMES]
            else:
                raise SurfacePilotError(f"Tool '{name}' surfaces must be a list")
            risk = str(tool.get("risk", "medium")).lower()
        else:
            raise SurfacePilotError(f"Tool at index {index} must be a string or object")

        if risk not in policy.get("tool_risk", {}):
            raise SurfacePilotError(
                f"Tool '{name}' has unsupported risk '{risk}'; use low, medium, or high"
            )
        normalized.append({"name": name, "surfaces": surfaces, "risk": risk})
    return normalized


def keyword_hits(task: str, keywords: Sequence[Any]) -> List[str]:
    """Return policy keywords that are present in the task text."""

    lowered = task.lower()
    hits: List[str] = []
    for keyword in keywords:
        word = str(keyword).lower().strip()
        if not word:
            continue
        if " " in word:
            matched = word in lowered
        else:
            matched = re.search(r"\b" + re.escape(word) + r"\b", lowered) is not None
        if matched and word not in hits:
            hits.append(word)
    return hits


def risk_level(score: float) -> str:
    """Convert a numeric score into a display level."""

    if score >= 0.70:
        return "high"
    if score >= 0.35:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def surface_tools(
    surface: str, tools: Sequence[Mapping[str, Any]], policy: Mapping[str, Any]
) -> List[Mapping[str, Any]]:
    """Return tools that explicitly or implicitly match an execution surface."""

    config = policy.get("surfaces", {}).get(surface, {})
    patterns = [str(pattern).lower() for pattern in config.get("tool_patterns", [])]
    matched: List[Mapping[str, Any]] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        lowered = name.lower()
        explicit = surface in tool.get("surfaces", [])
        implicit = any(pattern in lowered for pattern in patterns)
        if explicit or implicit:
            matched.append(tool)
    return matched


def analyze_task(
    task: str,
    tools: Optional[Sequence[Mapping[str, Any]]] = None,
    policy: Optional[Mapping[str, Any]] = None,
    policy_source: str = "default",
) -> Dict[str, Any]:
    """Score a task and return a structured routing recommendation."""

    if not isinstance(task, str) or not task.strip():
        raise SurfacePilotError("Task must be a non-empty string")

    active_policy = deepcopy(dict(policy or DEFAULT_POLICY))
    normalized_tools = normalize_tools(list(tools or []), active_policy)
    tool_risk = active_policy.get("tool_risk", {})
    surface_results: Dict[str, Dict[str, Any]] = {}
    required_surfaces: List[str] = []

    for surface in SURFACE_NAMES:
        config = active_policy.get("surfaces", {}).get(surface, {})
        hits = keyword_hits(task, config.get("keywords", []))
        matched_tools = surface_tools(surface, normalized_tools, active_policy)
        matched_tool_names = [str(tool["name"]) for tool in matched_tools]
        missing_capability = bool(hits) and not matched_tools
        max_tool_risk = 0.0
        if matched_tools:
            max_tool_risk = max(float(tool_risk[str(tool["risk"])]) for tool in matched_tools)

        if hits:
            required_surfaces.append(surface)
            keyword_score = min(0.45, 0.12 * len(hits))
            score = float(config.get("base_risk", 0.0)) + keyword_score + max_tool_risk
            if missing_capability:
                score += float(config.get("missing_tool_penalty", 0.0))
        else:
            score = 0.0

        score = round(min(1.0, score), 2)
        signals = [f"keyword:{hit}" for hit in hits]
        if missing_capability:
            signals.append("missing_tool_for_surface")
        if matched_tool_names:
            signals.append("tool_available")

        surface_results[surface] = {
            "score": score,
            "level": risk_level(score),
            "signals": signals,
            "available_tools": matched_tool_names,
            "missing_capability": missing_capability,
        }

    max_surface = max((data["score"] for data in surface_results.values()), default=0.0)
    breadth_penalty = max(0, len(required_surfaces) - 1) * 0.05
    overall = round(min(1.0, max_surface + breadth_penalty), 2)
    route, reason = choose_route(surface_results, required_surfaces, overall, active_policy)
    actions = build_actions(route, surface_results, active_policy)
    confidence = round(min(0.95, 0.55 + overall * 0.35 + len(required_surfaces) * 0.03), 2)

    return {
        "task": task,
        "recommendation": {
            "route": route,
            "confidence": confidence,
            "reason": reason,
            "required_surfaces": required_surfaces,
        },
        "risk": {
            "overall": overall,
            "level": risk_level(overall),
            "surfaces": surface_results,
        },
        "actions": actions,
        "tools_considered": [str(tool["name"]) for tool in normalized_tools],
        "policy": {
            "source": policy_source,
            "version": str(active_policy.get("version", "surfacepilot-policy-v1")),
        },
    }


def choose_route(
    surface_results: Mapping[str, Mapping[str, Any]],
    required_surfaces: Sequence[str],
    overall: float,
    policy: Mapping[str, Any],
) -> Tuple[str, str]:
    """Choose a route from scores, missing capabilities, and thresholds."""

    thresholds = policy.get("thresholds", {})
    missing_high = any(
        surface_results[surface]["missing_capability"]
        and float(surface_results[surface]["score"]) >= 0.55
        for surface in required_surfaces
    )

    if missing_high or overall >= float(thresholds.get("human_review", 0.75)):
        route = "human_review"
    elif float(surface_results["service_call"]["score"]) >= float(thresholds.get("sandboxing", 0.60)):
        route = "sandboxing"
    elif (
        float(surface_results["state_verification"]["score"]) > 0
        or overall >= float(thresholds.get("verification_first", 0.50))
    ):
        route = "verification_first"
    elif overall >= float(thresholds.get("cautious_execution", 0.30)):
        route = "cautious_execution"
    else:
        route = "direct_execution"

    ranked = sorted(
        required_surfaces,
        key=lambda name: (-float(surface_results[name]["score"]), name),
    )
    if ranked:
        top = ", ".join(
            f"{name}={surface_results[name]['score']:.2f}" for name in ranked[:3]
        )
        reason = f"Highest risk surfaces: {top}."
    else:
        reason = "No execution-surface keywords were detected."
    return route, reason


def build_actions(
    route: str, surface_results: Mapping[str, Mapping[str, Any]], policy: Mapping[str, Any]
) -> List[str]:
    """Build deterministic operator actions for the chosen route."""

    configured = policy.get("route_actions", {}).get(route, [])
    actions = [str(action) for action in configured]
    missing = [
        surface
        for surface, data in surface_results.items()
        if bool(data.get("missing_capability"))
    ]
    if missing:
        actions.append("Add or enable tools for: " + ", ".join(missing) + ".")
    return actions


def read_input_file(path: str) -> Tuple[str, List[Any]]:
    """Read a JSON input file and return task plus tools."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SurfacePilotError(f"Could not read input file '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SurfacePilotError(f"Input file '{path}' is not valid JSON: {exc}") from exc

    if not isinstance(payload, Mapping):
        raise SurfacePilotError("Input file root must be a JSON object")
    task = payload.get("task")
    tools = payload.get("tools", [])
    if not isinstance(task, str):
        raise SurfacePilotError("Input file needs a string 'task' field")
    if not isinstance(tools, list):
        raise SurfacePilotError("Input file 'tools' field must be a list")
    return task, tools


def parse_tools_json(text: str) -> List[Any]:
    """Parse a JSON tool list from a CLI argument."""

    try:
        tools = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SurfacePilotError(f"--tools-json is not valid JSON: {exc}") from exc
    if not isinstance(tools, list):
        raise SurfacePilotError("--tools-json must decode to a list")
    return tools


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Route LLM agent tasks by execution-surface failure risk."
    )
    parser.add_argument("--input", help="JSON file with task and tools fields.")
    parser.add_argument("--task", help="Task prompt to analyze.")
    parser.add_argument(
        "--tools-json",
        help="JSON list of tool metadata objects. Ignored when --input is used.",
    )
    parser.add_argument(
        "--policy",
        help="Optional YAML policy file. Can also be set with SURFACEPILOT_POLICY.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in sample with no API keys or network access.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and print JSON output."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        policy, policy_source = load_policy(args.policy)
        if args.selftest or (not args.input and not args.task):
            task = SAMPLE_TASK
            tools = SAMPLE_TOOLS
        elif args.input:
            task, tools = read_input_file(args.input)
        else:
            task = args.task
            tools = parse_tools_json(args.tools_json) if args.tools_json else []

        result = analyze_task(task, tools, policy, policy_source)
    except SurfacePilotError as exc:
        print(f"surfacepilot: error: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
