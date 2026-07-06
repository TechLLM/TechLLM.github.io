# LexiPilot -- BM25 Query Planning for Agent Tool Routing

LexiPilot is an installable experimental skill for transparent agent tool routing. It builds a deterministic query plan from a user request, then ranks a tool catalog with BM25-style lexical evidence.

## Install

Copy this directory into your Claude Code or OpenClaw skills directory.

No dependencies are required.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --input examples/sample_input.json
python scripts/test.py
```

Write output to a file:

```bash
python scripts/run.py --input examples/sample_input.json --output examples/sample_output.json
```

## Expected Output

The sample request ranks `lexical-router` first, excludes `email-sender`, and returns:

```json
{
  "query_plan": {
    "original_request": "Need transparent BM25 tool routing with audit logs and hard exclusions; do not use email tools.",
    "normalized_request": "need transparent bm25 tool routing with audit logs and hard exclusions do not use email tools",
    "high_signal_terms": [
      "audit",
      "bm25",
      "email",
      "exclusions",
      "logs",
      "routing",
      "tool",
      "tools",
      "transparent"
    ],
    "required_capabilities": [
      "audit",
      "bm25",
      "exclusion",
      "routing"
    ],
    "hard_constraints": [
      "hard exclusions"
    ],
    "exclusions": [
      "email",
      "email tools"
    ],
    "subqueries": [
      "transparent bm25 tool routing",
      "audit logs",
      "exclusions"
    ]
  },
  "candidates": [
    {
      "id": "lexical-router",
      "name": "Lexical Tool Router",
      "score": 6.4926,
      "matched_terms": [
        "audit",
        "bm25",
        "exclusions",
        "logs",
        "routing",
        "tool",
        "tools",
        "transparent"
      ],
      "evidence": [
        "matched high-signal terms: audit, bm25, exclusions, logs, routing, tool, tools, transparent",
        "matched required capabilities: audit, bm25, routing"
      ],
      "excluded": false
    },
    {
      "id": "embedding-router",
      "name": "Embedding Router",
      "score": 1.1827,
      "matched_terms": [
        "routing",
        "tools"
      ],
      "evidence": [
        "matched high-signal terms: routing, tools",
        "matched required capabilities: routing"
      ],
      "excluded": false
    }
  ],
  "excluded_tools": [
    {
      "id": "email-sender",
      "name": "Email Sender",
      "reason": "matched exclusion term: email"
    }
  ],
  "metadata": {
    "algorithm": "bm25-lite",
    "top_k": 3,
    "tool_count": 3,
    "min_score": 0.0
  }
}
```
