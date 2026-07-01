# Agent Runbook

## Objective

Maintain a concise working summary for a long-running research agent while updating only changed evidence.

## Memory

The agent tracks the original user request, open questions, completed steps, and the latest accepted summary.

## Delta Policy

- Preserve stable context.
- Highlight changed sections.
- Keep enough surrounding lines to understand the edit.

## Risks

- Reprocessing the full context can waste tokens.
- Repeated summaries can drift away from source evidence.
- Deleted sections may invalidate previous memory.
