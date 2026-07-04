# TraceLoom - Failure-Recovery Knowledge Graph Extractor

TraceLoom is an installable skill with a small offline CLI for converting messy agent execution traces into compact recovery memory: failures, likely causes, repair commands, resume points, outcomes, Markdown notes, and JSON graph candidates.

## Install

Place this directory in a Claude Code or OpenClaw-style skills folder, then verify the local script:

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/test.py
```

No dependencies are required beyond Python 3.

## Usage

Run the built-in sample:

```bash
python scripts/run.py --selftest
```

Extract JSON from the example trace:

```bash
python scripts/run.py --input examples/sample-trace.txt --format json
```

Write a Markdown note:

```bash
python scripts/run.py --input examples/sample-trace.txt --format markdown --output examples/recovery-note.md
```

Process JSONL:

```bash
python scripts/run.py --input examples/sample-trace.jsonl --format json
```

Optional environment variables:

```bash
TRACELOOM_LLM_API_KEY=example-key TRACELOOM_USE_LLM=false python scripts/run.py --selftest
```

The bundled script reads optional keys for wrapper compatibility but does not call any external service.

## Example Expected Output

For `examples/sample-trace.txt`, the compact fields should include:

```json
{
  "summary": "Recovered 1 of 1 detected failure(s). Main pattern: missing_dependency repaired with python -m pip install pyyaml.",
  "failures": [
    {
      "error_signature": "ModuleNotFoundError: No module named 'yaml'",
      "likely_cause": "missing_dependency",
      "failed_command": "python worker.py",
      "recovery_command": "python -m pip install pyyaml",
      "resume_point": "python worker.py",
      "outcome": "recovered"
    }
  ]
}
```

The full fixture is in `examples/expected-output.json`.
