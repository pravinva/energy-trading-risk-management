from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import random

from apex_fresh.config import get_config
from apex_fresh.data.sql_exec import poll_statement, submit_statement
from apex_fresh.data.workflows.state import ensure_marker, write_marker


def _run(sql_text: str) -> None:
    sid = submit_statement(sql_text)
    result = poll_statement(sid)
    if result.get("status", {}).get("state") != "SUCCEEDED":
        raise RuntimeError(f"SQL failed: {sql_text}")


def _fmt_decimal(value: float) -> str:
    return str(Decimal(value).quantize(Decimal("0.0001")))


def run() -> None:
    ensure_marker("W02-schema-fresh")
    cfg = get_config()
    catalog = cfg.catalog

    _run(f"TRUNCATE TABLE {catalog}.market_nem.prices")
    _run(f"TRUNCATE TABLE {catalog}.market_epex.prices")
    _run(f"TRUNCATE TABLE {catalog}.market_ercot.lmp")

    now = datetime.utcnow()
    base = now - timedelta(days=7)

    # NEM backfill sample (5 regions x 288 intervals/day x 2 days)
    nem_regions = ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]
    nem_values: list[str] = []
    for i in range(576):
        dt = base + timedelta(minutes=5 * i)
        for region in nem_regions:
            rrp = 80 + random.uniform(-25, 50)
            if random.random() < 0.004:
                rrp = random.uniform(1500, 8000)
            nem_values.append(
                f"(TIMESTAMP '{dt.strftime('%Y-%m-%d %H:%M:%S')}',"
                f"'{region}',{_fmt_decimal(rrp)},'BACKFILL_W04')"
            )
    _run(
        f"INSERT INTO {catalog}.market_nem.prices "
        "(interval_datetime, region_id, rrp, data_source) VALUES "
        + ",".join(nem_values)
    )

    # EPEX backfill sample with MTU boundary encoded
    epex_zones = ["DE-LU", "FR", "BE", "NL", "ES", "NO1", "NO2", "CH"]
    epex_values: list[str] = []
    pre_change = datetime(2025, 8, 30, 0, 0, 0)
    post_change = datetime(2025, 9, 2, 0, 0, 0)
    for anchor, mtu in [(pre_change, 60), (post_change, 15)]:
        intervals = 48 if mtu == 60 else 192
        for i in range(intervals):
            dt = anchor + timedelta(minutes=mtu * i)
            for zone in epex_zones:
                price = 65 + random.uniform(-30, 35)
                if zone in {"DE-LU", "ES"} and random.random() < 0.05:
                    price = random.uniform(-40, -3)
                epex_values.append(
                    f"(TIMESTAMP '{dt.strftime('%Y-%m-%d %H:%M:%S')}',"
                    f"'{zone}',{_fmt_decimal(price)},{mtu},'BACKFILL_W04')"
                )
    _run(
        f"INSERT INTO {catalog}.market_epex.prices "
        "(delivery_datetime, bidding_zone, price_eur_mwh, mtu_minutes, data_source) VALUES "
        + ",".join(epex_values)
    )

    # ERCOT backfill sample with RTC+B boundary
    ercot_nodes = [
        "West Hub",
        "Houston Hub",
        "North Hub",
        "South Hub",
        "Panhandle Wind 1",
    ]
    ercot_values: list[str] = []
    for dt in [datetime(2025, 12, 4, 12, 0, 0), datetime(2025, 12, 6, 12, 0, 0)]:
        for node in ercot_nodes:
            lmp = 45 + random.uniform(-15, 40)
            rtcb = "NULL" if dt < datetime(2025, 12, 5) else _fmt_decimal(lmp + random.uniform(-2, 2))
            ercot_values.append(
                f"(TIMESTAMP '{dt.strftime('%Y-%m-%d %H:%M:%S')}',"
                f"'{node}',{_fmt_decimal(lmp)},{rtcb},'BACKFILL_W04')"
            )
    _run(
        f"INSERT INTO {catalog}.market_ercot.lmp "
        "(interval_datetime, node_id, lmp, rtcb_signal, data_source) VALUES "
        + ",".join(ercot_values)
    )

    write_marker("W04-historical-backfill-fresh", "W04 Historical Backfill Fresh")


if __name__ == "__main__":
    run()

