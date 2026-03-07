from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class FreshConfig:
    profile: str
    warehouse_id: str
    catalog: str
    app_name: str
    completion_dir: str


def get_config() -> FreshConfig:
    return FreshConfig(
        profile=os.getenv("APEX_FRESH_DATABRICKS_PROFILE", "fe-vm"),
        warehouse_id=os.getenv("APEX_FRESH_WAREHOUSE_ID", "a62624c51dced859"),
        catalog=os.getenv("APEX_FRESH_CATALOG", "apex_fresh"),
        app_name=os.getenv("APEX_FRESH_APP_NAME", "apex-fresh-energy-app"),
        completion_dir=os.getenv("APEX_FRESH_COMPLETION_DIR", "completions"),
    )

