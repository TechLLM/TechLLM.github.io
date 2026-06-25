---
name: state-contract-designer
description: Design compact structured state contracts for multi-agent, RAG, and workflow handoffs when long summaries lose information, grounding, or routing decisions.
license: MIT
---

# State Contract Designer

Auto-generated and experimental; review before using in production workflows.

## Overview

State Contract Designer helps replace long agent-to-agent prose handoffs with compact, explicit state packets. It is intended for multi-agent systems, RAG pipelines, workflow routers, reviewers, publishers, and automation chains where intermediate messages become too long, ambiguous, or unreliable.

The skill treats operational context as typed state instead of hidden model memory. A good contract preserves the intent, evidence, confidence, risk, routing hints, and next action needed by the downstream consumer while reducing token use and limiting error propagation.

Use this skill to design JSON Schema-compatible packets, producer instructions, consumer instructions, validation rules, and short trace examples that fit into logs, queues, cron payloads, chat messages, or debugging output.

## When to use

Use this skill when:

- A workflow passes long summaries between agents, tools, or stages.
- A RAG step loses source grounding, confidence, or unresolved risks.
- A reviewer, supervisor, or router needs to make a decision from compact state rather than a full transcript.
- A pipeline needs stable handoff packets across chat, gateway, internal orchestration, knowledge-base lookup, scheduled jobs, or publishing flows.
- Prompts repeatedly say things like "summarize the previous agent output" or "continue from this context" in a multi-agent workflow.
- You need trigger keywords such as state contract, structured handoff, multi-agent handoff, RAG state, compact context, workflow packet, trace packet, schema validation, or agent routing.

Do not use this skill for one-off single-agent tasks where normal prose is shorter and clearer than a schema.

## Installation

Copy this directory into your skills folder or install it through your skill manager if one is available. A typical repository layout is:

```text
state-contract-designer/
  SKILL.md
  README.md
  scripts/
    run.py
```

Make the helper script executable if your environment preserves executable bits:

```bash
chmod +x scripts/run.py
```

The bundled script uses only the Python standard library and does not require package installation.

## Usage

Ask the agent to use the skill against a workflow summary, prompt chain, RAG pipeline, or automation design. For example:

```text
Use the state-contract-designer skill to replace this three-agent handoff with a validated JSON state packet.
```

Generate a starter schema:

```bash
python scripts/run.py template > state.schema.json
```

Lint a schema for the core contract requirements:

```bash
python scripts/run.py lint-schema state.schema.json
```

Validate a state packet:

```bash
python scripts/run.py validate-packet packet.json
```

Print compact trace fields from a packet:

```bash
python scripts/run.py trace packet.json
```

When using the skill manually, return these sections:

- `Workflow Diagnosis`: current handoff problem and where state is lost or bloated.
- `State Contract`: JSON Schema-compatible schema object.
- `Producer Prompt`: concise instruction block for the upstream agent.
- `Consumer Prompt`: concise instruction block for the downstream agent.
- `Validation Rules`: hard checks and rejection conditions.
- `Trace Examples`: two or three example packets.
- `Migration Notes`: where to insert the contract in prompts, configuration, queues, scheduled jobs, or skill instructions.

## Example

Input workflow summary:

```text
A chat user asks for a blog post. A knowledge-base agent retrieves notes, a writer drafts the post, a reviewer checks source support, and a publisher posts to a CMS. The current handoff is a 2,000-token prose summary with pasted source excerpts.
```

Output contract excerpt:

```json
{
  "schema_version": "1.0.0",
  "trace_id": "chat-20260625-001",
  "intent": "review_blog_draft",
  "evidence_type": "retrieval",
  "support_score": 0.82,
  "risk": "medium",
  "next_action": "review",
  "source_refs": ["kb:note-184", "draft:post.md"],
  "open_questions": ["One claim lacks a source reference"],
  "routing_hint": "reviewer"
}
```

Producer instruction excerpt:

```text
Return only a JSON state packet. Do not paste full source text. Use source_refs for evidence. Set risk=high if next_action is publish and support_score is below 0.85.
```

Consumer instruction excerpt:

```text
If risk is high or blocked, do not publish. If support_score is below 0.70, retrieve evidence or ask for clarification. Use source_refs to inspect evidence before approving claims.
```

## Limitations

- The bundled validator is intentionally lightweight and is not a full JSON Schema validator.
- The skill improves handoff structure, but it does not guarantee that upstream evidence is true or current.
- Contracts that include too many fields can become another form of bloated context; keep fields tied to downstream decisions.
- A state packet should not include secrets, credentials, private user data, or large pasted source excerpts.
- Human review is still required for high-impact publishing, financial, legal, medical, safety, or irreversible actions.