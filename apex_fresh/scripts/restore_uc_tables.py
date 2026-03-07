from __future__ import annotations

import argparse
import json
from pathlib import Path

from apex_fresh.config import get_config
from apex_fresh.data.sql_exec import poll_statement, submit_statement


def _run_sql(sql: str) -> None:
    statement_id = submit_statement(sql)
    result = poll_statement(statement_id)
    state = result.get("status", {}).get("state")
    if state != "SUCCEEDED":
        err = result.get("status", {}).get("error", {})
        raise RuntimeError(f"SQL failed ({state}): {err}")


def main() -> None:
    cfg = get_config()
    parser = argparse.ArgumentParser(description="Restore Unity Catalog tables from backup manifest paths.")
    parser.add_argument("--manifest-path", default="apex_fresh/backups/latest_manifest.json")
    parser.add_argument("--target-catalog", default=cfg.catalog)
    parser.add_argument(
        "--if-exists",
        choices=["replace", "skip"],
        default="replace",
        help="Behavior when target table exists",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_catalog = args.target_catalog.strip()

    entries = manifest.get("entries", [])
    for entry in entries:
        schema = str(entry["schema"])
        table = str(entry["table"])
        path = str(entry["path"])
        full_table = f"{target_catalog}.{schema}.{table}"
        _run_sql(f"CREATE SCHEMA IF NOT EXISTS {target_catalog}.{schema}")
        if args.if_exists == "skip":
            restore_sql = (
                f"CREATE TABLE IF NOT EXISTS {full_table} "
                f"AS SELECT * FROM parquet.`{path}`"
            )
        else:
            restore_sql = (
                f"CREATE OR REPLACE TABLE {full_table} "
                f"AS SELECT * FROM parquet.`{path}`"
            )
        _run_sql(restore_sql)
        print(f"Restored {full_table} from {path}")


if __name__ == "__main__":
    main()
