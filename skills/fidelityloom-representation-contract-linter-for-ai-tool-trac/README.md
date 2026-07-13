# FidelityLoom — Representation Contract Linter for AI Tool Traces

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Detect representation loss before it becomes a specialist-model failure.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

FidelityLoom is an open-source command-line tool for auditing how structured inputs change as an AI agent prepares and invokes specialist models, scientific services, and domain-specific tools. It addresses a common evaluation blind spot: a tool may receive the correct request conceptually while losing critical representation details such as units, axes, missing-value semantics, array structure, numeric precision, or field provenance during text conversion.

The project analyzes JSONL traces containing the original structured input, generated tool-call arguments, and returned results. It aligns fields across trace stages, detects lossy transformations, assigns severity and confidence, and produces both a human-readable fidelity report and a machine-readable adapter recommendation. This separates routing failures from serialization and modality-translation failures, helping teams improve the interface around specialist systems instead of incorrectly blaming the underlying model.

FidelityLoom is designed for agent evaluation pipelines, model gateways, tool-calling frameworks, and cross-architecture distillation experiments. It is deterministic by default, supports configurable domain contracts, and can be used locally or as a CI quality gate.

**Who is this for.** 

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
python scripts/run.py --selftest
```

**Expected output:**

```text
{
  "fidelity_report": {
    "schema_version": "1.0",
    "status": "fail",
    "trace_count": 1,
    "finding_count": 13,
    "severity_counts": {
      "error": 7,
      "warning": 6,
      "info": 0
    },
    "findings": [
      {
        "trace_id": "weather-array-001",
        "field": "missing_reading",
        "transition": "source->tool_args",
        "code": "zero_substitution",
        "severity": "error",
        "confidence": 1.0,
        "message": "Missing value was replaced with numeric zero."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "source->tool_args",
        "code": "overflow_risk",
        "severity": "warning",
        "confidence": 0.95,
        "message": "Integer 9007199254740993 exceeds the IEEE-754 safe integer range."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "tool_args->tool_result",
        "code": "overflow_risk",
        "severity": "warning",
        "confidence": 0.95,
        "message": "Integer 9007199254740993 exceeds the IEEE-754 safe integer range."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "tool_args->tool_result",
        "code": "numeric_type_coercion",
        "severity": "warning",
        "confidence": 1.0,
        "message": "Numeric value changed type from int to string."
      },
      {
        "trace_id": "weather-array-001",
        "field": "signal",
        "transition": "source->tool_args",
        "code": "flattened_array",
        "severity": "error",
        "confidence": 1.0,
        "message": "Array shape changed from [2, 2] to [4] by flattening."
      },
      {
        "trace_id": "weather-array-001",
        "field": "signal",
        "transition": "source->tool_args",
        "code": "reordered_dimensions",
        "severity": "error",
        "confidence": 1.0,
        "message": "Axis order changed 
… (+4227 chars truncated)
```

## Requirements

| Key | Value |
|---|---|
| Python | 3.9+ |
| Dependencies | Python standard library only |
| API key | Not required |

## 📦 Installation

**1) As a Claude Code / OpenClaw skill**

```bash
# Personal (available in every project)
git clone https://github.com/TechLLM/TechLLM.github.io /tmp/techllm-skills
mkdir -p ~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
cp -r /tmp/techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/* ~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/

# Project-local
mkdir -p .claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
cp -r /tmp/techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/* .claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--contract CONTRACT] [--format {json,text}]
              [--output OUTPUT] [--fail-on {none,warning,error}] [--selftest]
              [input]

Audit representation fidelity across source, tool arguments, and tool results.

positional arguments:
  input                 JSONL trace file

options:
  -h, --help            show this help message and exit
  --contract CONTRACT   JSON contract file (default: FIDELITYLOOM_CONTRACT,
                        then inferred same-path contract)
  --format {json,text}  report format (default: json; env:
                        FIDELITYLOOM_FORMAT)
  --output OUTPUT       explicit output file; overwrites that file if it
                        exists
  --fail-on {none,warning,error}
                        return exit code 1 at or above this severity (default:
                        none)
  --selftest            run the built-in offline deterministic sample and
                        internal assertions
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Read each JSONL record and validate the source, call, and result trace stages against the configured trace envelope
- Normalize field paths while preserving data types, array rank, dimensions, units, null markers, and numeric precision metadata
- Align fields using exact paths, declared mappings, aliases, and conservative structural matching
- Run loss detectors that compare presence, type, shape, ordering, units, precision, and missing-value semantics
- Aggregate findings by trace, field, detector, severity, and probable transformation boundary
- Emit a fidelity report and generate a proposed adapter schema that preserves the observed source contract

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| — | — | — |

## FAQ

_—_

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/` or `.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
