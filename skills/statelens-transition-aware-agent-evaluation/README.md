# StateLens - Transition-Aware Agent Evaluation

Minimal installable skill for evaluating LLM agents by checking the state transitions they produce.

## Install

Copy this directory into your Claude Code, OpenClaw, or compatible skills folder. No dependencies are required beyond Python 3.

## Usage

```bash
python scripts/run.py --help
python scripts/run.py --selftest
python scripts/run.py --before examples/before --after examples/after --spec examples/spec.yaml --trace examples/trace.json
python scripts/test.py
```

Use `python3` in the same commands if your shell does not provide `python`.

## Expected example output

Running the example command should produce the same report stored in `examples/expected-output.json`: pass is `true`, confidence is `high`, ten checks pass, two files are modified, and no unexpected changes are reported.
