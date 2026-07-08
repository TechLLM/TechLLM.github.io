# FaultLoom — API Failure Benchmark Builder for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> Turn social API failures into benchmark cases for reliable LLM agents.

> 🤖 Auto-generated & self-verified skill. A minimal, runnable reference — review before production use.

## What is this?

FaultLoom is a proposed open-source library and CLI for converting real social publishing failures into standardized benchmark cases. It treats API errors from platforms like Threads, Instagram, Facebook, and similar services as useful evaluation material rather than disposable operational noise.

The project helps expose how LLM agents behave when a tool call fails. It is designed to catch failure modes such as guessing the wrong cause, retrying when human action is required, ignoring provider-specific error codes, or giving vague recovery advice.

FaultLoom turns raw logs, JSON responses, status payloads, and exception traces into clean YAML cases with normalized labels, retry guidance, severity, user-action requirements, and expected recovery behavior.

**Who is this for.** FaultLoom is for AI evaluation teams, agent framework maintainers, and developers building automation workflows that need to test whether agents can diagnose failures accurately and recommend practical recovery steps.

## ⏱ 30-Second Quick Start

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
python scripts/run.py --selftest
```

**Expected output:**

```text
benchmark_suite:
  name: "social-publishing-failures-demo"
  version: "0.1"
  generated_by: "faultloom-minimal-rule-engine"
  cases:
    -
      id: "auth-token-expired"
      provider: "threads"
      operation: "publish_text_post"
      source:
        status_code: 401
        error_excerpt: "{\"access_token\":\"[REDACTED]\",\"error\":{\"code\":190,\"message\":\"Invalid OAuth access token\",\"type\":\"OAuthException\"}}"
      classification:
        category: "authentication"
        retryable: false
        user_action_required: true
        severity: "high"
        confidence: 0.94
      expected_recovery:
        summary: "Stop automatic retry and request credential refresh or reauthorization."
        actions:
          - "Mark the publishing attempt failed with an authentication cause."
          - "Ask the user or operator to reconnect the provider account."
          - "Retry only after a new credential is available."
      evaluation:
        should_retry: false
        agent_should:
          - "Preserve the provider error code and status code in the diagnosis."
          - "State that human or operator action is required before retry."
        agent_must_not:
          - "Claim the post content caused the failure without evidence."
          - "Loop retries with the same credential."
    -
      id: "instagram-rate-limit"
      provider: "instagram"
      operation: "publish_media"
      source:
        status_code: 429
        error_excerpt: "Rate limit exceeded. Retry after 60 seconds."
      classification:
        category: "rate_limit"
        retryable: true
        user_action_required: false
        severity: "medium"
        confidence: 0.92
      expected_recovery:
        summary: "Schedule a retry using provider-aware backoff."
        actions:
          - "Respect retry-after or rate-limit reset timing when available."
          - "Queue the publish attempt instead of retrying immediately."
          - "Surface a concise delay reason to the
… (+1540 chars truncated)
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
mkdir -p ~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
cp -r /tmp/techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/* ~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/

# Project-local
mkdir -p .claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
cp -r /tmp/techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/* .claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/
```

**2) As a standalone CLI**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
python scripts/run.py --help
```

**3) Manual download**

On GitHub, open the `skills/faultloom-api-failure-benchmark-builder-for-llm-agents/` folder and download the files, or download the repo ZIP and copy that one folder.

## ⚡ Usage

Full `--help` output:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--selftest]

Build YAML benchmark cases from social publishing API failure logs.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        JSON file containing an array of failure events or an
                        object with suite_name and events.
  --output OUTPUT, -o OUTPUT
                        Optional YAML output path. Defaults to stdout.
  --selftest            Run the built-in sample with no external API key or
                        network access.
```

## Examples

See the `examples/` folder in this skill (sample input + expected output).

## 🧠 How it works

- Ingests raw social publishing failures from logs, API responses, exception traces, and status payloads.
- Redacts sensitive data such as tokens, account identifiers, post content, and private metadata before export.
- Classifies each failure into a portable taxonomy covering authentication, rate limits, permissions, media validation, transient outages, policy blocks, and unknown failures.
- Adds benchmark metadata such as retryability, severity, confidence, user-action requirements, and expected recovery behavior.
- Exports normalized YAML test cases for evaluations, regression suites, tool-use benchmarks, and fine-tuning datasets.

## 🔧 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| A failure is classified as unknown. | The input does not match an existing rule closely enough, or the provider returned an ambiguous error. | Review the raw failure, add a more specific classification rule, or use assisted labeling for cases that require judgment. |
| A case recommends retrying when user action is needed. | The failure was missing clear permission, authentication, or policy signals during classification. | Update the taxonomy rule so the case marks user action as required and sets retryability appropriately. |
| Sensitive content appears in an exported case. | The redaction hooks did not cover a provider-specific field or custom log format. | Extend the redaction configuration to cover the missing field before exporting benchmark data. |

## FAQ

**Does FaultLoom replace production monitoring?**

No. FaultLoom is focused on turning failures into reusable evaluation data. It can complement monitoring, but its main purpose is benchmark creation and agent behavior testing.

**Why use real API failures instead of synthetic examples?**

Real failures preserve the messy details agents must handle in production, including provider wording, nested payloads, partial context, and ambiguous recovery paths.

**Can it work without an LLM?**

Yes. FaultLoom is designed to use rule-based classification first. LLM-assisted labeling is optional for ambiguous cases.

**What makes the generated YAML useful for agent evaluation?**

Each case includes the failure evidence, normalized diagnosis, retry policy, user-action requirement, severity, and expected recovery behavior, making it suitable for repeatable tests and regression checks.

## ✅ Verification

Passed automated structure / syntax / selftest checks (see `SKILL.md`).

## Uninstall

Delete the skill folder (`~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/` or `.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/`). Nothing else on your system is touched.

## 📜 Versioning

This skill uses semantic versioning. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## 🤝 Contributing

This is an auto-generated reference skill. Issues and PRs that improve it are welcome.

## License

MIT
