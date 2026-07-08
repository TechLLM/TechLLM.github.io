---
id: rag_gate_eval
title: RAG Gate Evaluation
summary: Relevance gates should score retrieved passages by answer evidence rather than metadata labels.
topic: retrieval
label: relevance
---

# RAG Gate Evaluation

## Evidence grounding

A robust RAG relevance gate compares the user question with concrete claims in the candidate passage.

Metadata labels can help route documents, but they should not dominate scoring.

## Masking checks

Masking titles, labels, and headers can reveal whether a scorer depends on non-evidential cues.

Ranking shifts and score variance are useful regression metrics for retrieval audits.
