# QueryLoom - Verifiable BM25 Planning for RAG

QueryLoom is an installable experimental skill that creates a reviewable `retrieval_plan.json` before a RAG pipeline runs BM25 search. It uses local TF-IDF analysis and deterministic heuristics to propose rare terms, synonym slots, exclusion terms, evidence requirements, and BM25-ready query strings.

## Install

Copy this folder into your skills directory. No third-party dependencies are required.

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/test.py
```

## Usage

Run the bundled example:

```bash
python3 scripts/run.py \
  --question-file examples/question.txt \
  --corpus examples/corpus.md
```

Write a plan to disk:

```bash
python3 scripts/run.py \
  --question "How can BM25 planning reduce RAG retrieval failures?" \
  --corpus examples/corpus.md \
  --output retrieval_plan.json
```

## Expected Output

The output is deterministic JSON. It starts like this:

```json
{
  "schema_version": "1.0",
  "planner": {
    "name": "queryloom-local-heuristic",
    "mode": "local",
    "external_llm_used": false
  },
  "question": "How can QueryLoom reduce RAG retrieval failures with BM25 planning?"
}
```

See `examples/expected_output.json` for the full expected output from the example input.

## Files

- `SKILL.md`: skill instructions and trigger guidance.
- `scripts/run.py`: command-line planner.
- `scripts/test.py`: import-based self-test.
- `examples/question.txt`: sample question.
- `examples/corpus.md`: sample corpus.
- `examples/expected_output.json`: expected deterministic output.
