from __future__ import annotations

from pathlib import Path

from apex_fresh.data.sql_exec import run_sql_file
from apex_fresh.data.workflows.state import write_marker


def run() -> None:
    schema_file = (
        Path(__file__).resolve().parents[1] / "schema" / "01_catalog_and_core.sql"
    )
    run_sql_file(schema_file)
    write_marker("W02-schema-fresh", "W02 Fresh Schema")


if __name__ == "__main__":
    run()

