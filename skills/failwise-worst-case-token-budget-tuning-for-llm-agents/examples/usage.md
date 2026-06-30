# Example

Run Failwise with the bundled sample logs and policies:

```bash
python scripts/run.py --logs examples/sample_logs.jsonl --policies examples/policies.yaml --output examples/report.json
```

Use the `pareto` field in the JSON report to shortlist policies that improve reliability or worst-slice resilience without being dominated on estimated cost and latency.
