from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from apex_fresh.config import get_config
from apex_fresh.data.sql_exec import poll_statement, submit_statement


def _escape(value: str) -> str:
    return value.replace("'", "''")


def _run_sql(sql: str) -> list[list[object]]:
    statement_id = submit_statement(sql)
    result = poll_statement(statement_id)
    state = result.get("status", {}).get("state")
    if state != "SUCCEEDED":
        err = result.get("status", {}).get("error", {})
        raise RuntimeError(f"SQL failed ({state}): {err}")
    return result.get("result", {}).get("data_array", [])


def _table_inventory_sql(catalog: str, schemas: list[str]) -> str:
    schema_filter = ", ".join(f"'{_escape(s)}'" for s in schemas)
    return f"""
    SELECT table_schema, table_name
    FROM {catalog}.information_schema.tables
    WHERE table_schema IN ({schema_filter})
      AND table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name
    """


def main() -> None:
    cfg = get_config()
    parser = argparse.ArgumentParser(description="Backup Unity Catalog tables to DBFS as parquet snapshots.")
    parser.add_argument("--catalog", default=cfg.catalog)
    parser.add_argument(
        "--schemas",
        default="market_nem,market_epex,market_ercot,trading,ingestion,risk,portfolio,analytics",
        help="Comma-separated schemas in source catalog",
    )
    parser.add_argument("--backup-root", default="dbfs:/tmp/apex_fresh_backups")
    parser.add_argument("--manifest-path", default="apex_fresh/backups/latest_manifest.json")
    args = parser.parse_args()

    catalog = args.catalog.strip()
    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]
    snapshot_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = _run_sql(_table_inventory_sql(catalog, schemas))
    entries: list[dict[str, object]] = []

    for schema, table in rows:
        schema_name = str(schema)
        table_name = str(table)
        target_path = (
            f"{args.backup_root.rstrip('/')}/{catalog}/{schema_name}/{table_name}/snapshot_ts={snapshot_ts}/"
        )
        copy_sql = (
            f"COPY INTO '{target_path}' "
            f"FROM (SELECT * FROM {catalog}.{schema_name}.{table_name}) "
            f"FILEFORMAT = PARQUET "
            f"FORMAT_OPTIONS ('compression' = 'snappy') "
            f"OVERWRITE = TRUE"
        )
        _run_sql(copy_sql)
        count_rows = _run_sql(
            f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema_name}.{table_name}"
        )
        row_count = int(count_rows[0][0]) if count_rows else 0
        entries.append(
            {
                "catalog": catalog,
                "schema": schema_name,
                "table": table_name,
                "path": target_path,
                "row_count": row_count,
            }
        )
        print(f"Backed up {catalog}.{schema_name}.{table_name} -> {target_path} ({row_count} rows)")

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_catalog": catalog,
        "schemas": schemas,
        "backup_root": args.backup_root,
        "snapshot_ts": snapshot_ts,
        "entries": entries,
    }
    manifest_path = Path(args.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
