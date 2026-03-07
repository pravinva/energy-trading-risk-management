from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from apex_fresh.config import get_config


def _sh(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def _split_sql(content: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("--"):
            continue
        current.append(line)
        if ";" in line:
            stmt = "\n".join(current).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1]
            if stmt:
                chunks.append(stmt)
            current = []
    tail = "\n".join(current).strip()
    if tail:
        chunks.append(tail)
    return chunks


def submit_statement(sql_text: str) -> str:
    cfg = get_config()
    body = {
        "statement": sql_text,
        "warehouse_id": cfg.warehouse_id,
        "wait_timeout": "0s",
        "disposition": "INLINE",
    }
    out = _sh(
        [
            "databricks",
            "api",
            "post",
            "/api/2.0/sql/statements",
            "--profile",
            cfg.profile,
            "--json",
            json.dumps(body),
            "-o",
            "json",
        ]
    )
    return json.loads(out)["statement_id"]


def poll_statement(statement_id: str) -> dict:
    cfg = get_config()
    for _ in range(240):
        out = _sh(
            [
                "databricks",
                "api",
                "get",
                f"/api/2.0/sql/statements/{statement_id}",
                "--profile",
                cfg.profile,
                "-o",
                "json",
            ]
        )
        obj = json.loads(out)
        state = obj.get("status", {}).get("state")
        if state in {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}:
            return obj
        time.sleep(2)
    raise TimeoutError(f"Statement timed out: {statement_id}")


def run_sql_file(path: Path) -> None:
    statements = _split_sql(path.read_text(encoding="utf-8"))
    for idx, stmt in enumerate(statements, start=1):
        sid = submit_statement(stmt)
        result = poll_statement(sid)
        state = result.get("status", {}).get("state")
        if state != "SUCCEEDED":
            raise RuntimeError(f"{path} statement #{idx} failed: {state}")

