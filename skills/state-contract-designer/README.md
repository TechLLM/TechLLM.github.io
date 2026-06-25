# State Contract Designer

Auto-generated and experimental; review before using in production workflows.

## Overview

State Contract Designer is an installable skill for designing compact, structured state contracts between agents, tools, and workflow stages. It is useful when a system currently passes long prose summaries downstream and those summaries cause token bloat, lost evidence, unclear routing, or repeated re-summarization.

The skill turns operational context into an explicit packet: intent, evidence type, support score, risk, next action, source references, open questions, constraints, routing hints, and trace metadata. This makes the handoff easier to validate, log, replay, and consume deterministically.

This is not a hidden-state transfer mechanism. It is a practical pattern for hosted LLM systems where state must be explicit, typed, validated, and small enough to survive queues, logs, chat interfaces, scheduled jobs, and multi-agent boundaries.

## Key Features

- Designs compact JSON-style state packets for multi-agent and workflow handoffs.
- Preserves downstream decision state without copying full transcripts or source excerpts.
- Includes core fields for intent, evidence type, support score, risk, and next action.
- Supports optional fields for source references, claims, constraints, open questions, routing hints, artifacts, and expiration.
- Produces producer prompts, consumer prompts, validation rules, and trace examples.
- Provides a standard-library Python helper for schema templates, schema linting, packet validation, and trace compaction.
- Encourages deterministic routing behavior for retrieve, ask, execute, review, publish, escalate, and stop decisions.

## How It Works

The skill starts by mapping workflow edges: producers, consumers, triggers, and handoff points. It then identifies which pieces of information actually affect downstream decisions, such as routing, retrieval, validation, publishing, escalation, or the final user response.

From that decision state, it defines a small contract. The default core fields are `schema_version`, `trace_id`, `intent`, `evidence_type`, `support_score`, `risk`, and `next_action`. Optional fields can be added only when they are required by the workflow.

The final output includes a JSON Schema-compatible schema, instructions for the upstream producer, instructions for the downstream consumer, validation rules, example packets, and migration notes. The bundled script can generate a starter schema, check common schema mistakes, validate packets against the skill's lightweight rules, and print compact trace summaries.

## Installation

Place the skill directory in your skills location or publish it as a GitHub repository that users can install from their own skill manager.

Expected layout:

```text
state-contract-designer/
  SKILL.md
  README.md
  scripts/
    run.py
```

Make the helper script executable if needed:

```bash
chmod +x scripts/run.py
```

No Python packages are required. The helper uses only the standard library.

## Usage

Ask your agent to apply the skill to a concrete workflow or prompt chain:

```text
Use the state-contract-designer skill to create a compact state packet for this RAG reviewer workflow.
```

Generate a starter JSON Schema:

```bash
python scripts/run.py template > state.schema.json
```

Lint the schema for required state-contract fields:

```bash
python scripts/run.py lint-schema state.schema.json
```

Validate a packet:

```bash
python scripts/run.py validate-packet packet.json
```

Print a compact trace view for logs or debugging:

```bash
python scripts/run.py trace packet.json
```

Recommended agent output sections:

- `Workflow Diagnosis`: explain where the current handoff loses state or wastes tokens.
- `State Contract`: provide a JSON Schema-compatible object.
- `Producer Prompt`: tell the upstream agent exactly what to emit and what to omit.
- `Consumer Prompt`: tell the downstream agent how to interpret fields and when to verify.
- `Validation Rules`: define hard checks and rejection conditions.
- `Trace Examples`: include short good, weak-evidence, and rejected packets.
- `Migration Notes`: describe where to insert the contract in prompts, configuration, queues, scheduled jobs, or automation steps.

## Example

Workflow summary:

```text
A user asks for a sourced article. A retrieval step finds notes, a drafting step writes an article, a review step checks claim support, and a publishing step posts the approved draft. The current handoff is a long prose summary containing copied excerpts, uncertain claims, and unclear publish readiness.
```

Compact packet:

```json
{
  "schema_version": "1.0.0",
  "trace_id": "article-20260625-001",
  "intent": "review_article_draft",
  "evidence_type": "retrieval",
  "support_score": 0.76,
  "risk": "medium",
  "next_action": "review",
  "source_refs": ["kb:note-184", "kb:note-219", "draft:article.md"],
  "claims": [
    {
      "claim": "The draft includes one statistic that needs stronger support.",
      "support_score": 0.58,
      "source_refs": ["kb:note-219"]
    }
  ],
  "open_questions": ["Confirm whether the statistic should be removed or sourced."],
  "routing_hint": "reviewer"
}
```

Producer prompt excerpt:

```text
Return only a JSON state packet. Do not paste full source text. Use source_refs for evidence. Use null or empty arrays for unknown optional fields. Set risk=high if next_action is publish and support_score is below 0.85.
```

Consumer prompt excerpt:

```text
Use next_action, risk, support_score, and source_refs to choose the next step. If risk is high or blocked, do not publish. If support_score is below 0.70, retrieve evidence or ask for clarification before irreversible action.
```

Validation command:

```bash
python scripts/run.py validate-packet packet.json
```

Trace command:

```bash
python scripts/run.py trace packet.json
```

## Use Cases

- Multi-agent supervisor handoffs where routing depends on evidence, risk, and next action.
- RAG workflows where downstream reviewers need source references without pasted context.
- Publishing pipelines that need explicit approval gates before CMS, social, or email output.
- Coding workflows that pass inspection results, artifact paths, and unresolved risks to implementers or reviewers.
- Scheduled jobs that need compact payloads for retry, replay, logging, and escalation.
- Customer-support or operations workflows where chat-visible summaries must stay short but auditable.

## Limitations

- The helper script is not a complete JSON Schema validator. It only enforces common checks used by this skill.
- A structured packet can still contain bad information if the producer invents details or cites weak evidence.
- The contract should be kept small. If every field becomes a paragraph, the design has failed.
- Source references are pointers, not proof. High-impact actions should re-check evidence before execution.
- Do not put secrets, credentials, private personal data, or large source excerpts into state packets.
- Human review remains important for high-risk publishing, financial, legal, medical, safety, account, and irreversible workflow actions.