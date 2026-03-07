# APEX Fresh App (Standalone)

This is a clean implementation path that does not modify the existing app.

## Why this exists

- Uses only the `*full*` APEX prompt guidance.
- Enforces run order: `W04` before `W05`, and both before `W03` simulators.
- Uses Databricks profile `fe-vm`.
- Creates and uses a fresh Unity Catalog catalog: `apex_fresh`.

## Structure

- `apex_fresh/app/` - standalone FastAPI app entrypoint.
- `apex_fresh/data/` - schema SQL and Python execution workflow.
- `apex_fresh/scripts/` - ordered orchestration runner.

## Required execution order

1. W02 schema bootstrap (fresh catalog + schemas)
2. W04 historical backfill
3. W05 trade seeds
4. W03 continuous simulators

## One-command bootstrap

```bash
python -m apex_fresh.scripts.run_w04_w05_w03
```

The runner will fail fast if order is violated.
