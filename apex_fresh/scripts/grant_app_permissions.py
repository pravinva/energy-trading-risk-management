from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any


def _sh(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def _api(profile: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    cmd = ["databricks", "api", method, path, "--profile", profile, "-o", "json"]
    if payload is not None:
        cmd.extend(["--json", json.dumps(payload)])
    out = _sh(cmd)
    return json.loads(out) if out.strip() else {}


def _apps_get(profile: str, app_name: str) -> dict[str, Any]:
    out = _sh(["databricks", "apps", "get", app_name, "--profile", profile, "-o", "json"])
    return json.loads(out)


def _warehouse_update_permissions(profile: str, warehouse_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    out = _sh(
        [
            "databricks",
            "warehouses",
            "update-permissions",
            warehouse_id,
            "--profile",
            profile,
            "--json",
            json.dumps(payload),
            "-o",
            "json",
        ]
    )
    return json.loads(out) if out.strip() else {}


def _execute_sql(profile: str, warehouse_id: str, statement: str) -> list[dict[str, Any]]:
    create = _api(
        profile,
        "post",
        "/api/2.0/sql/statements",
        {
            "statement": statement,
            "warehouse_id": warehouse_id,
            "wait_timeout": "0s",
            "disposition": "INLINE",
        },
    )
    sid = create["statement_id"]
    for _ in range(180):
        status = _api(profile, "get", f"/api/2.0/sql/statements/{sid}")
        state = status.get("status", {}).get("state")
        if state == "SUCCEEDED":
            manifest_cols = status.get("manifest", {}).get("schema", {}).get("columns", [])
            col_names = [str(c.get("name", f"c{i}")) for i, c in enumerate(manifest_cols)]
            data = status.get("result", {}).get("data_array", [])
            return [dict(zip(col_names, row)) for row in data]
        if state in {"FAILED", "CANCELED", "CLOSED"}:
            detail = status.get("status", {}).get("error", {}).get("message", state)
            raise RuntimeError(f"SQL failed: {detail}\nStatement: {statement}")
    raise TimeoutError(f"SQL statement timed out: {sid}")


def grant_app_permissions(profile: str, app_name: str, warehouse_id: str, catalog: str) -> None:
    app = _apps_get(profile, app_name)
    sp_name = app.get("service_principal_name")
    sp_client_id = app.get("service_principal_client_id")
    sp_id = app.get("service_principal_id")
    if not sp_name or not sp_client_id:
        raise RuntimeError(f"App {app_name} has no service principal identity yet")

    _warehouse_update_permissions(
        profile,
        warehouse_id,
        {
            "access_control_list": [
                {
                    "service_principal_name": sp_client_id,
                    "permission_level": "CAN_USE",
                }
            ]
        },
    )

    principal_sql = str(sp_client_id).replace("`", "``")
    schemas_read = ["market_nem", "market_epex", "market_ercot", "analytics", "risk", "portfolio"]
    schemas_rw = ["trading"]

    statements: list[str] = [
        f"GRANT USE CATALOG ON CATALOG {catalog} TO `{principal_sql}`",
    ]
    for schema in schemas_read + schemas_rw:
        statements.extend(
            [
                f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{principal_sql}`",
            ]
        )
    for schema in schemas_rw:
        statements.extend(
            [
                f"GRANT CREATE TABLE ON SCHEMA {catalog}.{schema} TO `{principal_sql}`",
            ]
        )

    table_grants: list[str] = []
    for schema in schemas_read + schemas_rw:
        table_rows = _execute_sql(profile, warehouse_id, f"SHOW TABLES IN {catalog}.{schema}")
        for row in table_rows:
            table_name = str(row.get("tableName", "")).strip()
            if not table_name:
                continue
            fqtn = f"{catalog}.{schema}.{table_name}"
            table_grants.append(f"GRANT SELECT ON TABLE {fqtn} TO `{principal_sql}`")
            if schema in schemas_rw:
                table_grants.append(f"GRANT MODIFY ON TABLE {fqtn} TO `{principal_sql}`")

    for stmt in statements:
        _execute_sql(profile, warehouse_id, stmt)
    for stmt in table_grants:
        _execute_sql(profile, warehouse_id, stmt)

    print(
        json.dumps(
            {
                "app_name": app_name,
                "service_principal_name": sp_name,
                "service_principal_client_id": sp_client_id,
                "service_principal_id": sp_id,
                "warehouse_id": warehouse_id,
                "catalog": catalog,
                "grants_applied": len(statements) + len(table_grants) + 1,
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant warehouse and UC permissions to Databricks app identity")
    parser.add_argument("--profile", default="fe-vm")
    parser.add_argument("--app-name", default="apex-fresh-energy-app")
    parser.add_argument("--warehouse-id", default="a62624c51dced859")
    parser.add_argument("--catalog", default="apex_fresh")
    args = parser.parse_args()
    grant_app_permissions(args.profile, args.app_name, args.warehouse_id, args.catalog)


if __name__ == "__main__":
    main()
