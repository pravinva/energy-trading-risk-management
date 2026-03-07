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

## Backup and Restore (Workspace Loss Protection)

To snapshot all core `apex_fresh` tables to durable parquet paths and save a manifest:

```bash
python3 -m apex_fresh.scripts.backup_uc_tables \
  --catalog apex_fresh \
  --backup-root dbfs:/tmp/apex_fresh_backups \
  --manifest-path apex_fresh/backups/latest_manifest.json
```

To restore from the manifest into a catalog:

```bash
python3 -m apex_fresh.scripts.restore_uc_tables \
  --manifest-path apex_fresh/backups/latest_manifest.json \
  --target-catalog apex_fresh \
  --if-exists replace
```
