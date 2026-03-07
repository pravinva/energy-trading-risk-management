from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta

from apex_fresh.config import get_config
from apex_fresh.data.sql_exec import poll_statement, submit_statement
from apex_fresh.data.workflows.state import ensure_marker, write_marker


def _run(sql_text: str) -> None:
    sid = submit_statement(sql_text)
    result = poll_statement(sid)
    if result.get("status", {}).get("state") != "SUCCEEDED":
        raise RuntimeError(f"SQL failed: {sql_text}")


def _trade_payload(market: str, source: str) -> dict:
    ts = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
    return {
        "trade_id": str(uuid.uuid4()),
        "market": market,
        "instrument_id": f"{market}_SPOT_MAIN",
        "trader_id": random.choice(["SCHEN", "JWUU", "TJOHNSON"]),
        "direction": random.choice(["BUY", "SELL"]),
        "volume_mw": round(random.uniform(25, 300), 2),
        "price": round(random.uniform(25, 160), 4),
        "source_system": source,
        "trade_timestamp": ts.isoformat(),
    }


def run() -> None:
    ensure_marker("W04-historical-backfill-fresh")
    cfg = get_config()
    catalog = cfg.catalog

    _run(f"TRUNCATE TABLE {catalog}.ingestion.raw_etrm_trades")
    _run(f"TRUNCATE TABLE {catalog}.trading.trades")

    rows: list[str] = []
    market_sources = [
        ("NEM", "ALIGNE_SIM"),
        ("EPEX", "ENDUR_SIM"),
        ("ERCOT", "TRIPLE_POINT_SIM"),
    ]
    for market, source in market_sources:
        for _ in range(10):
            payload = _trade_payload(market, source)
            payload_json = json.dumps(payload).replace("'", "''")
            rows.append(
                f"('{source}','{market}','{payload_json}',false,current_timestamp())"
            )

    _run(
        f"INSERT INTO {catalog}.ingestion.raw_etrm_trades "
        "(source_system, market, payload, processed, received_at) VALUES "
        + ",".join(rows)
    )

    # DLT substitute for fresh implementation: parse key fields into trading.trades.
    _run(
        f"""
        INSERT INTO {catalog}.trading.trades
        SELECT
          get_json_object(payload, '$.trade_id') AS trade_id,
          market,
          get_json_object(payload, '$.instrument_id') AS instrument_id,
          get_json_object(payload, '$.trader_id') AS trader_id,
          get_json_object(payload, '$.direction') AS direction,
          CAST(get_json_object(payload, '$.volume_mw') AS DECIMAL(10,2)) AS volume_mw,
          CAST(get_json_object(payload, '$.price') AS DECIMAL(12,4)) AS price,
          source_system,
          current_timestamp() AS ingested_at
        FROM {catalog}.ingestion.raw_etrm_trades
        """
    )

    write_marker("W05-seeds-fresh", "W05 Trade Seeds Fresh")


if __name__ == "__main__":
    run()

