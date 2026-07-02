# Usage Example

Run RouteQuake on the included sample CSV:

```bash
python scripts/run.py --input examples/router_eval.csv --output-dir reports
```

Expected report files:

- `reports/routequake_report.md`
- `reports/routequake_report.json`

Use it as a release gate:

```bash
python scripts/run.py --input examples/router_eval.csv --min-worst-slice-accuracy 0.55
```
