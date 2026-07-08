# TraceVault — Evidence-Based Grading for Knowledge Agents

TraceVault is a small installable skill for grading observable work in Markdown knowledge-base tasks. It compares before-and-after vault snapshots against an expectation file and emits a JSON pass/fail report.

## Install

Copy this folder into your local skills directory or install it with your agent runtime's local skill installer.

No dependencies are required.

## Run

Built-in demo:

```bash
python scripts/run.py --pretty
```

Included example:

```bash
python scripts/run.py --before examples/before --after examples/after --expectations examples/expectations.yml --pretty
```

Save a report:

```bash
python scripts/run.py --before examples/before --after examples/after --expectations examples/expectations.yml --out report.json
```

## Expectation Checks

The reference grader checks:

- Created files
- Modified files
- Forbidden edits
- Required wiki or Markdown links
- Required citation text
- Required frontmatter fields and list membership

The script uses only the Python standard library. It optionally reads `TRACEVAULT_API_KEY` from the environment, but it performs all grading locally and does not call external services.
