---
name: fidelityloom-representation-contract-linter-for-ai-tool-trac
description: Audit JSONL AI tool traces for lossy units, axes, arrays, numeric precision, and missing-value semantics; use for agent evaluation, representation contract linting, tool-call fidelity, adapter generation, and CI quality gates.
version: 0.1.0
license: MIT
---

# FidelityLoom — Representation Contract Linter for AI Tool Traces

Auto-generated and experimental; review findings against domain expectations before enforcing a gate.

## Overview

FidelityLoom separates routing success from representation fidelity by comparing structured source input, generated tool arguments, and tool results. Its deterministic linter aligns contract-defined paths, detects lossy transformations, and emits both an audit report and an adapter recommendation.

## When to use

Use this skill when evaluating agent tool traces, debugging serialization or modality translation, checking units and array layouts, reviewing numeric or missing-value coercion, generating adapter rules, or adding a deterministic CI fidelity gate.

When NOT to use: Do not use it to judge whether a specialist model's scientific or domain answer is semantically correct.

## Workflow

1. Collect one JSON object per line with `trace_id`, `source`, `tool_args`, and `tool_result` objects.
2. Create a JSON contract that maps each logical field to `source_path`, `tool_path`, and optional `result_path`, then add unit, dimension, nullability, precision, and coercion expectations.
3. Run `python scripts/run.py` with the trace and contract paths.
4. Review `fidelity_report.findings` to locate the exact stage transition that changed a representation.
5. Apply `adapter_recommendation.fields[].coercion_rules` at the model or tool boundary.
6. Re-run the audit and optionally use `--fail-on warning` or `--fail-on error` as a CI gate.

## Inputs & Outputs

Input is UTF-8 JSONL. Every non-empty line must be an object with this shape:

```json
{"trace_id":"unique-id","source":{},"tool_args":{},"tool_result":{}}
```

The optional representation contract is JSON with `fields` keyed by logical field name. Each field requires string `source_path` and `tool_path`; it may include `result_path`, metadata paths, `required`, `unit`, `dimensions`, `nullable`, positive integer `precision` (minimum significant digits), `coercion`, and `missing_values`. An object JSON Schema is also accepted: standard `type`, `required`, `properties`, and nullable type arrays are recognized, while mapping metadata uses `x-source-path`, `x-tool-path`, `x-result-path`, `x-unit`, `x-dimensions`, `x-precision`, and corresponding metadata-path extensions. Without a contract, FidelityLoom infers same-path mappings from the first source object.

JSON output has exactly two top-level fields:

```json
{
  "fidelity_report": {
    "schema_version": "1.0",
    "status": "pass|warn|fail",
    "trace_count": 1,
    "finding_count": 0,
    "severity_counts": {"error": 0, "warning": 0, "info": 0},
    "findings": [
      {
        "trace_id": "unique-id",
        "field": "logical-name",
        "transition": "source->tool_args|tool_args->tool_result",
        "code": "machine_code",
        "severity": "error|warning|info",
        "confidence": 1.0,
        "message": "Human-readable explanation."
      }
    ]
  },
  "adapter_recommendation": {
    "schema_version": "1.0",
    "fields": [
      {
        "field": "logical-name",
        "source_path": "path",
        "tool_path": "path",
        "result_path": "path-or-null",
        "required": true,
        "unit": "unit-or-null",
        "dimensions": ["axis"],
        "nullable": false,
        "precision": 5,
        "coercion": "number",
        "coercion_rules": ["preserve-number-type"]
      }
    ]
  }
}
```

## Installation

Copy this directory into a Claude Code or OpenClaw-compatible skills directory, or run it in place. It requires Python 3.10 or newer and no third-party packages.

```bash
chmod +x scripts/run.py scripts/test.py
python scripts/run.py --selftest
```

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py examples/trace.jsonl --contract examples/contract.json
python scripts/run.py examples/trace.jsonl --contract examples/contract.json --format text
python scripts/run.py examples/trace.jsonl --contract examples/contract.json --fail-on error
python scripts/run.py examples/trace.jsonl --contract examples/contract.json --output report.json
```

Set `FIDELITYLOOM_CONTRACT`, `FIDELITYLOOM_FORMAT`, or `FIDELITYLOOM_FAIL_ON` for optional defaults. The tool uses no API or secret.

## Example

Run:

```bash
python scripts/run.py examples/trace.jsonl --contract examples/contract.json
```

The matching complete output is in `examples/expected-output.json`. Its expected summary is:

```json
{
  "status": "fail",
  "trace_count": 1,
  "finding_count": 13,
  "severity_counts": {"error": 7, "warning": 6, "info": 0}
}
```

Representative finding codes include `zero_substitution`, `overflow_risk`, `flattened_array`, `reordered_dimensions`, `dropped_unit`, `numeric_rounding`, `significant_digit_loss`, and `numeric_type_coercion`.

## Limitations

Path alignment uses dot-separated object keys and does not address list indexes or escaped dots in key names. Contract inference only maps unchanged source paths, array value comparison is structural rather than statistical, and findings identify representation changes rather than domain correctness. Explicit contracts are recommended when field names differ across stages.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · contract=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
