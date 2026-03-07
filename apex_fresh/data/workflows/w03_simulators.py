from __future__ import annotations

import random
import threading
import time
from datetime import datetime

from apex_fresh.config import get_config
from apex_fresh.data.sql_exec import poll_statement, submit_statement
from apex_fresh.data.workflows.state import ensure_marker, write_marker


def _run(sql_text: str) -> None:
    sid = submit_statement(sql_text)
    result = poll_statement(sid)
    if result.get("status", {}).get("state") != "SUCCEEDED":
        raise RuntimeError(f"SQL failed: {sql_text}")


def _nem_tick(catalog: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for region in ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]:
        price = 75 + random.uniform(-20, 60)
        rows.append(f"(TIMESTAMP '{now}','{region}',{price:.4f},'SIM_W03')")
    _run(
        f"INSERT INTO {catalog}.market_nem.prices "
        "(interval_datetime, region_id, rrp, data_source) VALUES " + ",".join(rows)
    )


def _epex_tick(catalog: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for zone in ["DE-LU", "FR", "BE", "NL", "ES"]:
        price = 60 + random.uniform(-25, 30)
        rows.append(f"(TIMESTAMP '{now}','{zone}',{price:.4f},15,'SIM_W03')")
    _run(
        f"INSERT INTO {catalog}.market_epex.prices "
        "(delivery_datetime, bidding_zone, price_eur_mwh, mtu_minutes, data_source) VALUES "
        + ",".join(rows)
    )


def _ercot_tick(catalog: str) -> None:
    now_dt = datetime.utcnow()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for node in ["West Hub", "Houston Hub", "North Hub"]:
        lmp = 48 + random.uniform(-15, 35)
        rtcb = "NULL" if now_dt.date().isoformat() < "2025-12-05" else f"{lmp + random.uniform(-2, 2):.4f}"
        rows.append(f"(TIMESTAMP '{now}','{node}',{lmp:.4f},{rtcb},'SIM_W03')")
    _run(
        f"INSERT INTO {catalog}.market_ercot.lmp "
        "(interval_datetime, node_id, lmp, rtcb_signal, data_source) VALUES "
        + ",".join(rows)
    )


def run(cycles: int = 3, sleep_seconds: int = 5) -> None:
    ensure_marker("W05-seeds-fresh")
    catalog = get_config().catalog

    for _ in range(cycles):
        threads = [
            threading.Thread(target=_nem_tick, args=(catalog,), daemon=True),
            threading.Thread(target=_epex_tick, args=(catalog,), daemon=True),
            threading.Thread(target=_ercot_tick, args=(catalog,), daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        time.sleep(sleep_seconds)

    write_marker("W03-simulators-fresh", "W03 Simulators Fresh")


if __name__ == "__main__":
    run()

