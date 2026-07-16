# Calibration

Run the toy calibration loop from a config file:

```powershell
nokaman train toy --config configs/example.yaml
```

The config file is a small YAML-compatible mapping. NokaMan parses this subset
with the standard library, so no extra YAML dependency is required.

Supported keys:

- `run_id`: stable run directory name under `data/runs/`
- `epochs`: number of calibration epochs
- `seed`: deterministic seed recorded with the run
- `resume`: reuse a completed matching run when the report and dashboard exist

Each run writes:

- `data/runs/<run_id>/toy_train_report.json`
- `data/runs/<run_id>/dashboard.json`

`dashboard.json` keeps predictable top-level keys for app dashboards:
`run_id`, `model`, `status`, `metrics`, and `report_path`.
