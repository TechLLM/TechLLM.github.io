---
name: faultloom-api-failure-benchmark-builder-for-llm-agents
description: Converts social publishing API failures into YAML benchmark cases for LLM agents; use for FaultLoom, API failure benchmarks, tool-call error diagnosis, retryability, recovery planning, and social API error logs.
version: 0.1.0
license: MIT
---

# FaultLoom - API Failure Benchmark Builder for LLM Agents

Auto-generated and experimental; validate outputs before using them in production evaluation suites.

## Overview

FaultLoom turns social publishing API failures into standardized benchmark cases for evaluating LLM and agent behavior after tool-call failures. It ingests raw logs, JSON error responses, status payloads, or client exception text, redacts sensitive fields, classifies the failure, and emits deterministic YAML cases with expected recovery behavior.

The bundled reference CLI is intentionally small and rule-based, so it can run without network access or API keys. Optional LLM-assisted labeling can be layered on top by downstream users, but the default path is deterministic.

## When to use

- Use when collecting Threads, Instagram, Facebook, or similar social publishing API errors for agent evaluation.
- Use when an agent must classify whether a failed tool call is retryable, needs user action, or should stop.
- Use when building regression tests for authentication failures, rate limits, permission errors, media validation failures, transient outages, policy blocks, or unknown failures.
- Use when raw provider logs need basic redaction before becoming benchmark fixtures.
- When NOT to use: do not use this as a live incident-response system, legal compliance tool, or replacement for provider-specific API documentation.

## Workflow

1. Collect raw failure records from logs, JSON API responses, exception traces, or status payloads.
2. Save the records as a JSON array, or as a JSON object with `suite_name` and `events` fields.
3. Run `python scripts/run.py --input <file>` to classify and redact the failures.
4. Review each generated case, especially `classification.confidence`, `expected_recovery`, and `evaluation.agent_must_not`.
5. Commit the generated YAML into an evaluation fixture, regression suite, or fine-tuning data review queue.
6. For ambiguous failures, add local rules or run a separate human/LLM labeling pass, then keep the final YAML deterministic.

## Inputs & Outputs

Input contract:

- Format: JSON.
- Shape: either an array of event objects, or an object with `suite_name` and `events`.
- Recommended event fields: `id`, `provider`, `operation`, `status_code`, `raw_error`, `timestamp`.
- `raw_error` may be a string, object, array, number, or null.
- Optional environment variable: `FAULTLOOM_LLM_LABELER_KEY`. The bundled CLI reads whether it is present for extension compatibility but never sends data to an external service.

Output shape:

```yaml
benchmark_suite:
  name: string
  version: string
  generated_by: string
  cases:
    - id: string
      provider: string
      operation: string
      source:
        status_code: integer|null
        error_excerpt: string
      classification:
        category: authentication|rate_limit|permission|media_validation|transient_outage|policy_block|unknown_failure
        retryable: boolean
        user_action_required: boolean
        severity: low|medium|high|critical
        confidence: number
      expected_recovery:
        summary: string
        actions:
          - string
      evaluation:
        should_retry: boolean
        agent_should:
          - string
        agent_must_not:
          - string
```

## Installation

Copy or install this skill directory into your Claude Code/OpenClaw-compatible skills folder. No Python packages are required.

```bash
python --version
python scripts/run.py --help
```

## Usage

Show help:

```bash
python scripts/run.py --help
```

Run the built-in deterministic self-test sample:

```bash
python scripts/run.py --selftest
```

Classify an example input file:

```bash
python scripts/run.py --input examples/social_api_failures.json
```

Write YAML to a file:

```bash
python scripts/run.py --input examples/social_api_failures.json --output out/faultloom_cases.yaml
```

Run the import-level test:

```bash
python scripts/test.py
```

## Example

Command:

```bash
python scripts/run.py --input examples/social_api_failures.json
```

Expected output:

```yaml
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
          - "Surface a concise delay reason to the user or operator."
      evaluation:
        should_retry: true
        agent_should:
          - "Use bounded exponential backoff or the provider retry-after value."
          - "Avoid changing content or credentials because the error is quota-related."
        agent_must_not:
          - "Retry in a tight loop."
          - "Ask the user to reconnect the account without supporting evidence."
    -
      id: "facebook-media-invalid"
      provider: "facebook"
      operation: "upload_media"
      source:
        status_code: 400
        error_excerpt: "{\"error\":{\"code\":36003,\"message\":\"Image aspect ratio is invalid. Minimum width is 320 pixels.\"}}"
      classification:
        category: "media_validation"
        retryable: false
        user_action_required: true
        severity: "medium"
        confidence: 0.88
      expected_recovery:
        summary: "Request a corrected media asset before retrying."
        actions:
          - "Identify the provider media constraint that failed."
          - "Tell the user or upstream system exactly which asset property must change."
          - "Retry only after the asset is transformed or replaced."
      evaluation:
        should_retry: false
        agent_should:
          - "Connect the failure to media validation rather than service availability."
          - "Give a concrete remediation for the invalid media."
        agent_must_not:
          - "Retry the identical upload repeatedly."
          - "Mislabel the failure as authentication or rate limiting."
```

## Limitations

- The classifier is rule-based and intentionally conservative.
- YAML emission supports the deterministic structures produced by this tool, not arbitrary YAML features.
- Redaction is best-effort and should be reviewed before publishing external datasets.
- Provider APIs change over time, so teams should add local rules for newly observed error codes.

## Verification
Automated execution check: **passed ✅**.

- Steps: structure=ok · syntax=ok · help=ok · selftest=ok · test=ok
- Commands and outputs shown in `README.md` are captured from these real runs.
