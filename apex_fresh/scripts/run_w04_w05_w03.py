from __future__ import annotations

from apex_fresh.data.workflows.w02_schema_bootstrap import run as run_w02
from apex_fresh.data.workflows.w04_backfill import run as run_w04
from apex_fresh.data.workflows.w05_trade_seeds import run as run_w05
from apex_fresh.data.workflows.w03_simulators import run as run_w03


def run() -> None:
    print("APEX fresh runner starting")
    print("Order enforced: W02 -> W04 -> W05 -> W03")
    run_w02()
    run_w04()
    run_w05()
    run_w03()
    print("APEX fresh runner complete")


if __name__ == "__main__":
    run()

