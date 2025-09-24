# CLI Usage (Python backend)

Count faces:
```
python -m convert_asset.cli mesh-faces <stage.usd>
```

Plan ratio for a target total faces (dry-run planning):
```
python -m convert_asset.cli mesh-simplify <stage.usd> --target-faces 80000
```

Apply decimation with Python backend:
```
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --ratio 0.5 --apply --out <out.usd> \
  --progress --progress-interval-collapses 10000 --time-limit 120
```

Options:
- `--ratio r` target face ratio (0..1]; if `--target-faces` is given, the planner suggests a ratio first.
- `--apply` write back and export to `--out`.
- `--progress` show periodic progress; interval in collapses via `--progress-interval-collapses`.
- `--time-limit` per-mesh time limit in seconds.
