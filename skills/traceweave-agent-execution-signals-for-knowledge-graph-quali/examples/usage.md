# Example Usage

Run TraceWeave against the bundled notes and logs:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --out traceweave-report.md
```

Preview sidecar metadata changes:

```bash
python scripts/run.py --notes examples/notes --logs examples/logs --metadata-dir .traceweave --diff
```
