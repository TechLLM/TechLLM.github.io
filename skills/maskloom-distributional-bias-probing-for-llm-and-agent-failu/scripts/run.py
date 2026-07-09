"""MaskLoom reference CLI for distributional masking probes.

The script runs deterministic masking trials over a prompt and candidate texts,
then reports how selection outcomes shift. It has a built-in lexical selector
for offline use and an optional command-template mode for probing a local model
or agent runner.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple


MASK = "[MASK]"
REPORT_SCHEMA_VERSION = "maskloom.report.v1"

SAMPLE_INPUT: Dict[str, Any] = {
    "prompt": "Which route should handle invoice refund requests?",
    "candidates": [
        {
            "id": "billing",
            "text": "Billing tool handles invoices, refunds, and receipts.",
        },
        {
            "id": "support",
            "text": "Support route handles login issues and account troubleshooting.",
        },
        {
            "id": "sales",
            "text": "Sales route handles upgrades, pricing questions, and demos.",
        },
    ],
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "which",
}


class MaskProbeError(ValueError):
    """Raised when probe input or command execution is invalid."""


def normalize_token(token: str) -> str:
    """Return a small deterministic token normalization for lexical probing."""

    value = token.lower()
    if value == "mask":
        return ""
    if len(value) > 4 and value.endswith("ies"):
        value = value[:-3] + "y"
    elif len(value) > 3 and value.endswith("s"):
        value = value[:-1]
    return value


def tokenize(text: str) -> List[str]:
    """Tokenize text into normalized content terms."""

    terms: List[str] = []
    for raw in re.findall(r"[A-Za-z0-9_]+", text):
        term = normalize_token(raw)
        if term and term not in STOPWORDS:
            terms.append(term)
    return terms


def normalize_candidates(raw_candidates: Sequence[Any]) -> List[Dict[str, str]]:
    """Validate and normalize candidate definitions."""

    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise MaskProbeError("Input must include a non-empty 'candidates' list.")

    candidates: List[Dict[str, str]] = []
    seen_ids = set()
    for index, raw in enumerate(raw_candidates, start=1):
        if isinstance(raw, str):
            candidate_id = f"candidate_{index}"
            text = raw
        elif isinstance(raw, Mapping):
            candidate_id = str(raw.get("id") or f"candidate_{index}")
            text = raw.get("text")
            if text is None:
                raise MaskProbeError(f"Candidate {candidate_id!r} is missing required field 'text'.")
            text = str(text)
        else:
            raise MaskProbeError(f"Candidate {index} must be a string or object with 'id' and 'text'.")

        candidate_id = candidate_id.strip()
        text = text.strip()
        if not candidate_id:
            raise MaskProbeError(f"Candidate {index} has an empty id.")
        if candidate_id in seen_ids:
            raise MaskProbeError(f"Duplicate candidate id: {candidate_id}")
        if not text:
            raise MaskProbeError(f"Candidate {candidate_id!r} has empty text.")
        seen_ids.add(candidate_id)
        candidates.append({"id": candidate_id, "text": text})
    return candidates


def load_probe_input(path: str | Path) -> Dict[str, Any]:
    """Load and validate a probe input JSON file."""

    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise MaskProbeError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MaskProbeError(f"Input file is not valid JSON: {exc}") from exc

    if not isinstance(data, MutableMapping):
        raise MaskProbeError("Input JSON must be an object.")
    return dict(data)


def validate_probe_input(data: Mapping[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """Validate the top-level probe input and return prompt plus candidates."""

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise MaskProbeError("Input must include a non-empty string field 'prompt'.")
    candidates = normalize_candidates(data.get("candidates", []))
    return prompt.strip(), candidates


def score_candidates(prompt: str, candidates: Sequence[Mapping[str, str]]) -> Tuple[str, Dict[str, float]]:
    """Score candidates by normalized lexical overlap and return the selected id."""

    prompt_terms = set(tokenize(prompt))
    scores: Dict[str, float] = {}
    best_id = ""
    best_score = float("-inf")

    for index, candidate in enumerate(candidates):
        candidate_terms = set(tokenize(candidate["text"]))
        overlap = prompt_terms.intersection(candidate_terms)
        score = float(len(overlap))
        scores[candidate["id"]] = score
        if score > best_score:
            best_id = candidate["id"]
            best_score = score

    if not best_id:
        raise MaskProbeError("No candidates were available for scoring.")
    return best_id, scores


def mask_text(text: str, probability: float, rng: random.Random) -> Tuple[str, List[str]]:
    """Mask token spans in text with the configured probability."""

    parts = re.findall(r"[A-Za-z0-9_]+|[^A-Za-z0-9_]+", text)
    masked_parts: List[str] = []
    masked_tokens: List[str] = []
    for part in parts:
        if re.fullmatch(r"[A-Za-z0-9_]+", part) and rng.random() < probability:
            masked_parts.append(MASK)
            masked_tokens.append(part)
        else:
            masked_parts.append(part)
    return "".join(masked_parts), masked_tokens


def read_optional_env() -> Dict[str, Any]:
    """Read optional environment variables without printing secrets."""

    timeout_raw = os.getenv("MASKLOOM_COMMAND_TIMEOUT", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError as exc:
        raise MaskProbeError("MASKLOOM_COMMAND_TIMEOUT must be a number of seconds.") from exc
    if timeout_seconds <= 0:
        raise MaskProbeError("MASKLOOM_COMMAND_TIMEOUT must be greater than zero.")

    return {
        "command_timeout_seconds": timeout_seconds,
        "api_key": os.getenv("MASKLOOM_API_KEY"),
    }


def apply_template(template: str, values: Mapping[str, str]) -> str:
    """Replace supported placeholders in a shell command template."""

    command = template
    for key, value in values.items():
        command = command.replace("{" + key + "}", shlex.quote(value))
    return command


def run_command_selector(
    command_template: str,
    prompt: str,
    masked_prompt: str,
    candidates: Sequence[Mapping[str, str]],
    masked_candidates: Sequence[Mapping[str, str]],
    trial_index: int,
    timeout_seconds: float,
) -> Tuple[str, Dict[str, float]]:
    """Run an external selector command and parse its selected candidate id."""

    trial_payload = {
        "trial": trial_index,
        "prompt": prompt,
        "masked_prompt": masked_prompt,
        "candidates": list(candidates),
        "masked_candidates": list(masked_candidates),
    }
    replacements = {
        "prompt": prompt,
        "masked_prompt": masked_prompt,
        "candidates_json": json.dumps(list(candidates), separators=(",", ":")),
        "masked_candidates_json": json.dumps(list(masked_candidates), separators=(",", ":")),
        "trial_json": json.dumps(trial_payload, separators=(",", ":")),
    }
    command = apply_template(command_template, replacements)

    completed = subprocess.run(
        command,
        shell=True,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise MaskProbeError(f"Selector command failed on trial {trial_index}: {message}")

    output = completed.stdout.strip()
    if not output:
        raise MaskProbeError(f"Selector command produced no output on trial {trial_index}.")

    candidate_ids = {candidate["id"] for candidate in candidates}
    first_line = output.splitlines()[0].strip()
    scores: Dict[str, float] = {}
    selected_id = first_line

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, Mapping):
        raw_selected = parsed.get("selected_id")
        if raw_selected is None:
            raise MaskProbeError("Selector JSON output must include 'selected_id'.")
        selected_id = str(raw_selected)
        raw_scores = parsed.get("scores", {})
        if isinstance(raw_scores, Mapping):
            scores = {str(key): float(value) for key, value in raw_scores.items()}

    if selected_id not in candidate_ids:
        raise MaskProbeError(
            f"Selector returned unknown candidate id {selected_id!r}; expected one of {sorted(candidate_ids)}."
        )
    return selected_id, scores


def selection_distribution(candidates: Sequence[Mapping[str, str]], selections: Sequence[str]) -> List[Dict[str, Any]]:
    """Build an ordered selection distribution over candidate ids."""

    total = len(selections)
    return [
        {
            "id": candidate["id"],
            "count": selections.count(candidate["id"]),
            "rate": round(selections.count(candidate["id"]) / total, 4) if total else 0.0,
        }
        for candidate in candidates
    ]


def sensitive_spans(
    baseline_selected_id: str,
    trials: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Estimate span sensitivity from selection changes when spans are masked."""

    stats: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for trial in trials:
        changed = trial["selected_id"] != baseline_selected_id
        seen_in_trial = {
            (span["source"], normalize_token(span["token"]))
            for span in trial["masked_spans"]
            if normalize_token(span["token"]) and normalize_token(span["token"]) not in STOPWORDS
        }
        for source, token in seen_in_trial:
            item = stats.setdefault(
                (source, token),
                {"source": source, "token": token, "masked_count": 0, "changed_count": 0},
            )
            item["masked_count"] += 1
            if changed:
                item["changed_count"] += 1

    rows: List[Dict[str, Any]] = []
    for item in stats.values():
        masked_count = item["masked_count"]
        changed_count = item["changed_count"]
        rows.append(
            {
                "source": item["source"],
                "token": item["token"],
                "masked_count": masked_count,
                "changed_count": changed_count,
                "change_rate": round(changed_count / masked_count, 4) if masked_count else 0.0,
            }
        )

    rows.sort(key=lambda row: (-row["change_rate"], -row["masked_count"], row["source"], row["token"]))
    return rows[:20]


def bias_suspects(distribution: Sequence[Mapping[str, Any]], threshold: float = 0.75) -> List[Dict[str, Any]]:
    """Flag candidates that dominate the masked selection distribution."""

    suspects: List[Dict[str, Any]] = []
    for row in distribution:
        if float(row["rate"]) >= threshold:
            suspects.append(
                {
                    "id": row["id"],
                    "selection_rate": row["rate"],
                    "reason": "dominant_selection_under_masking",
                }
            )
    return suspects


def run_probe(
    probe_input: Mapping[str, Any],
    trials: int = 12,
    mask_probability: float = 0.25,
    seed: int = 1337,
    command_template: str | None = None,
) -> Dict[str, Any]:
    """Run a complete masking probe and return a JSON-serializable report."""

    if trials <= 0:
        raise MaskProbeError("trials must be greater than zero.")
    if not 0.0 <= mask_probability <= 1.0:
        raise MaskProbeError("mask_probability must be between 0.0 and 1.0.")

    env = read_optional_env()
    prompt, candidates = validate_probe_input(probe_input)
    baseline_selected_id, baseline_scores = score_candidates(prompt, candidates)
    rng = random.Random(seed)
    trial_rows: List[Dict[str, Any]] = []
    selections: List[str] = []

    for trial_index in range(trials):
        masked_prompt, prompt_masked_tokens = mask_text(prompt, mask_probability, rng)
        masked_spans = [{"source": "prompt", "token": token} for token in prompt_masked_tokens]
        masked_candidates: List[Dict[str, str]] = []

        for candidate in candidates:
            masked_text, candidate_masked_tokens = mask_text(candidate["text"], mask_probability, rng)
            masked_candidates.append({"id": candidate["id"], "text": masked_text})
            masked_spans.extend(
                {"source": f"candidate:{candidate['id']}", "token": token}
                for token in candidate_masked_tokens
            )

        if command_template:
            selected_id, scores = run_command_selector(
                command_template=command_template,
                prompt=prompt,
                masked_prompt=masked_prompt,
                candidates=candidates,
                masked_candidates=masked_candidates,
                trial_index=trial_index,
                timeout_seconds=env["command_timeout_seconds"],
            )
        else:
            selected_id, scores = score_candidates(masked_prompt, masked_candidates)

        selections.append(selected_id)
        trial_rows.append(
            {
                "trial": trial_index,
                "masked_prompt": masked_prompt,
                "masked_candidates": masked_candidates,
                "masked_spans": masked_spans,
                "selected_id": selected_id,
                "scores": scores,
            }
        )

    distribution = selection_distribution(candidates, selections)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "probe": {
            "trials_requested": trials,
            "trials_completed": len(trial_rows),
            "mask_probability": mask_probability,
            "seed": seed,
            "selector": "command" if command_template else "builtin",
        },
        "input_summary": {
            "prompt_token_count": len(tokenize(prompt)),
            "candidate_count": len(candidates),
        },
        "baseline": {
            "selected_id": baseline_selected_id,
            "scores": baseline_scores,
        },
        "selection_distribution": distribution,
        "sensitive_spans": sensitive_spans(baseline_selected_id, trial_rows),
        "bias_suspects": bias_suspects(distribution),
        "trials": trial_rows,
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        prog="mask-probe",
        description="Run deterministic MaskLoom masking probes for LLM, RAG, or agent selection failures.",
    )
    parser.add_argument("--input", "-i", help="Path to probe input JSON.")
    parser.add_argument("--output", "-o", help="Write JSON report to this path instead of stdout.")
    parser.add_argument("--trials", type=int, default=12, help="Number of masking trials to run.")
    parser.add_argument(
        "--mask-probability",
        type=float,
        default=0.25,
        help="Probability of masking each token span in prompt and candidates.",
    )
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for deterministic masking.")
    parser.add_argument(
        "--command-template",
        help=(
            "Optional local command template. Supported placeholders: {prompt}, {masked_prompt}, "
            "{candidates_json}, {masked_candidates_json}, {trial_json}."
        ),
    )
    parser.add_argument("--selftest", action="store_true", help="Run the built-in sample probe with no API key.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list:
        args_list = ["--selftest"]

    parser = build_parser()
    args = parser.parse_args(args_list)

    try:
        probe_input = SAMPLE_INPUT if args.selftest else load_probe_input(args.input) if args.input else None
        if probe_input is None:
            parser.error("provide --input or use --selftest")
        report = run_probe(
            probe_input,
            trials=args.trials,
            mask_probability=args.mask_probability,
            seed=args.seed,
            command_template=args.command_template,
        )
        payload = json.dumps(report, indent=2)
        if args.output:
            Path(args.output).write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
    except MaskProbeError as exc:
        print(f"mask-probe error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
