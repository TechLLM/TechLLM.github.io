# QueryLens

QueryLens is a minimal, offline command-line skill for turning a question and a local text corpus into an evaluable BM25 query plan. It produces deterministic JSON with include terms, optional expansions, exclusions, preserved constraints, and a verification checklist.

## Install

Copy this folder into a Claude Code, OpenClaw, or compatible skills directory. Python 3.10 or newer is enough; no third-party packages are required.

## Usage

```bash
python3 scripts/run.py --help
python3 scripts/run.py --selftest
python3 scripts/run.py --input examples/querylens_input.json --pretty
python3 scripts/run.py --question "How can hybrid retrieval evaluation run on a local corpus without external APIs?" --corpus examples/querylens_input.json --pretty
python3 scripts/test.py
```

Optional configuration:

```bash
QUERYLENS_MAX_TERMS=8 python3 scripts/run.py --input examples/querylens_input.json --pretty
QUERYLENS_SYNONYMS_JSON='{"retrieval":["lexical search"],"evaluation":["relevance audit"]}' python3 scripts/run.py --input examples/querylens_input.json --pretty
```

## Expected Output

`python3 scripts/run.py --input examples/querylens_input.json --pretty` should match `examples/querylens_expected_output.json`. The plan includes a BM25 query like:

```text
"hybrid retrieval" "local corpus" corpus evaluation hybrid local retrieval -"external apis" -external -apis
```

Run the built-in verification:

```bash
python3 scripts/run.py --selftest
python3 scripts/test.py
```
