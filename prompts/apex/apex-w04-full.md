# W04 — Historical Market Data Backfill
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W02-schema.md AND completions/W03-market-simulators.md exist.

## WHY THIS WORKSTREAM EXISTS
The W03 simulators write forward continuously from the moment they start. That gives you live data. But the app needs historical data for:
- VaR Monte Carlo: 252 days of price returns to compute volatility
- Quant backtesting: 12–24 months of price history to run strategies against
- Genie: "what happened during the August 2025 NEM spike?" requires the data to exist
- Portfolio revenue actuals: 12 months of BESS performance data
- ERCOT RTC+B story: data must exist both before and after 2025-12-05 for before/after comparisons

The backfills run ONCE before the simulator is started. The simulator then continues from where the backfill ended.

## DESIGN PRINCIPLES
1. All backfill scripts are idempotent — safe to re-run (MERGE or TRUNCATE+INSERT)
2. Use the same generation functions as the simulators for consistency
3. Batch writes in 10,000-row chunks — avoid OOM on large date ranges
4. Progress logging per batch so you can monitor long-running backfills
5. Scripts share a common `backfill_utils.py` for batching and logging

---

## FILE: data/seeds/market/backfill/backfill_utils.py

```python
"""
Shared utilities for all backfill scripts.
"""
import logging
from datetime import datetime, timedelta
from databricks.connect import DatabricksSession
from pyspark.sql import Row, DataFrame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
)

spark = DatabricksSession.builder.profile("fe-vm").getOrCreate()

def date_range(start: datetime, end: datetime, step_minutes: int):
    """Generator of datetimes from start to end in step_minutes increments."""
    current = start
    while current < end:
        yield current
        current += timedelta(minutes=step_minutes)

def write_batch(rows: list, table: str, batch_num: int, logger: logging.Logger):
    """Write a batch of rows to a Delta table. Append mode."""
    if not rows:
        return
    df = spark.createDataFrame([Row(**r) for r in rows])
    df.write.mode("append").saveAsTable(table)
    logger.info(f"Batch {batch_num}: wrote {len(rows)} rows to {table}")

def truncate_table(table: str, logger: logging.Logger):
    """Truncate before backfill — ensures idempotency."""
    spark.sql(f"TRUNCATE TABLE {table}")
    logger.info(f"Truncated {table}")

def backfill_summary(table: str, logger: logging.Logger):
    count = spark.sql(f"SELECT COUNT(*) AS n FROM {table}").collect()[0]["n"]
    logger.info(f"SUMMARY: {table} → {count:,} total rows")
    return count
```

---

## FILE: data/seeds/market/backfill/nem_backfill.py

```python
"""
NEM Historical Backfill
Targets:
  apex.market_nem.prices          — 2024-01-01 to present
  apex.market_nem.generation      — 2024-01-01 to present
  apex.market_nem.bess_telemetry  — 2024-01-01 to present
  apex.market_nem.predispatch     — 2024-01-01 to present (subset)
  apex.market_nem.forward_curves  — quarterly and calendar products

Expected volumes:
  prices:         ~600,000 rows  (2 years × 5 regions × 288 intervals/day)
  bess_telemetry: ~840,000 rows  (2 years × 8 assets × 288 intervals/day)
  generation:     ~600,000 rows  (same shape as prices, 5 fuel types per region)
  predispatch:    ~150,000 rows  (sampled — 1 run per 30 min, 12 horizons, 5 regions)
"""
import sys, random
from datetime import datetime, date
sys.path.append("../simulators")
from nem_simulator import generate_nem_price, update_bess_soc, REGIONS, NEM_ASSETS
from backfill_utils import *

logger = logging.getLogger("nem_backfill")

BACKFILL_START = datetime(2024, 1, 1, 0, 0, 0)
BACKFILL_END   = datetime.utcnow()
INTERVAL_MIN   = 5   # 5-minute NEM dispatch intervals
BATCH_SIZE     = 10000

FUEL_MIX = {
    "QLD1": {"COAL": 0.45, "GAS": 0.15, "WIND": 0.10, "SOLAR": 0.20, "HYDRO": 0.10},
    "NSW1": {"COAL": 0.40, "GAS": 0.12, "WIND": 0.12, "SOLAR": 0.22, "HYDRO": 0.14},
    "VIC1": {"COAL": 0.30, "GAS": 0.15, "WIND": 0.25, "SOLAR": 0.18, "HYDRO": 0.12},
    "SA1":  {"COAL": 0.00, "GAS": 0.20, "WIND": 0.45, "SOLAR": 0.25, "HYDRO": 0.10},
    "TAS1": {"COAL": 0.00, "GAS": 0.05, "WIND": 0.20, "SOLAR": 0.05, "HYDRO": 0.70},
}

def run_nem_backfill():
    logger.info(f"NEM backfill starting: {BACKFILL_START} → {BACKFILL_END}")

    # Truncate all NEM tables first
    for tbl in ["apex.market_nem.prices", "apex.market_nem.generation",
                "apex.market_nem.bess_telemetry", "apex.market_nem.predispatch"]:
        truncate_table(tbl, logger)

    price_buf, gen_buf, bess_buf, pd_buf = [], [], [], []
    prev_prices = {"QLD1": 80, "NSW1": 90, "VIC1": 95, "SA1": 110, "TAS1": 75}
    asset_soc   = {a: random.uniform(30, 80) for a in NEM_ASSETS}
    ASSET_REGION = {
        "HORNSDALE_1":"SA1","HORNSDALE_2":"SA1","TORRENS_BESS":"SA1",
        "WARATAH_1":"NSW1","ERARING_BESS_1":"NSW1",
        "KOORAGANG_BESS":"NSW1","LIDDELL_BESS":"NSW1",
        "VICTORIAN_BIG":"VIC1"
    }
    batch_num = 0

    for dt in date_range(BACKFILL_START, BACKFILL_END, INTERVAL_MIN):
        for region in REGIONS:
            row = generate_nem_price(region, dt)
            price_buf.append(row)
            prev_prices[region] = float(row["rrp"]) if abs(float(row["rrp"])) < 3000 \
                                   else prev_prices[region]

            # Generation by fuel type
            demand = float(row["totaldemand"])
            for fuel, share in FUEL_MIX[region].items():
                gen_buf.append({
                    "interval_datetime": dt,
                    "region_id": region,
                    "fuel_type": fuel,
                    "generation_mw": round(demand * share * random.uniform(0.9, 1.1), 2),
                    "capacity_factor": round(random.uniform(0.2, 0.95), 4),
                    "data_source": "SIMULATED"
                })

        # BESS telemetry
        avg_p = sum(prev_prices[r] for r in REGIONS) / len(REGIONS)
        for asset in NEM_ASSETS:
            region_price = prev_prices[ASSET_REGION.get(asset, "NSW1")]
            bess_buf.append(update_bess_soc(asset, float(region_price), dt))

        # Pre-dispatch — generate only every 30 min to keep volume manageable
        if dt.minute % 30 == 0:
            for region in REGIONS:
                base_rrp = prev_prices[region]
                for horizon in range(1, 13):
                    pd_buf.append({
                        "predispatch_datetime": dt + timedelta(minutes=horizon * 5),
                        "run_datetime": dt,
                        "region_id": region,
                        "forecast_rrp": round(float(base_rrp) * random.uniform(0.85, 1.15), 4),
                        "forecast_demand": round(
                            {"QLD1":7200,"NSW1":9800,"VIC1":6400,"SA1":1900,"TAS1":1200}[region]
                            * random.uniform(0.97, 1.03), 2),
                        "forecast_raise5min": round(max(0, random.gauss(8, 3)), 4),
                        "data_source": "SIMULATED"
                    })

        # Flush batches
        if len(price_buf) >= BATCH_SIZE:
            write_batch(price_buf, "apex.market_nem.prices", batch_num, logger)
            price_buf = []; batch_num += 1
        if len(gen_buf) >= BATCH_SIZE:
            write_batch(gen_buf, "apex.market_nem.generation", batch_num, logger)
            gen_buf = []
        if len(bess_buf) >= BATCH_SIZE:
            write_batch(bess_buf, "apex.market_nem.bess_telemetry", batch_num, logger)
            bess_buf = []
        if len(pd_buf) >= BATCH_SIZE:
            write_batch(pd_buf, "apex.market_nem.predispatch", batch_num, logger)
            pd_buf = []

    # Flush remaining
    for buf, tbl in [(price_buf,"apex.market_nem.prices"),
                     (gen_buf,"apex.market_nem.generation"),
                     (bess_buf,"apex.market_nem.bess_telemetry"),
                     (pd_buf,"apex.market_nem.predispatch")]:
        if buf: write_batch(buf, tbl, batch_num, logger)

    # Summaries
    for tbl in ["apex.market_nem.prices","apex.market_nem.generation",
                "apex.market_nem.bess_telemetry","apex.market_nem.predispatch"]:
        backfill_summary(tbl, logger)

    # Forward curves — insert once, static
    _backfill_nem_forward_curves()
    logger.info("NEM backfill complete")

def _backfill_nem_forward_curves():
    """
    ASX Energy forward curve — quarterly and calendar products.
    Static snapshot — one curve_date per product.
    """
    tenors = ["Q1-2026","Q2-2026","Q3-2026","Q4-2026","Cal-2027","Cal-2028"]
    base = {"Q1-2026":88,"Q2-2026":85,"Q3-2026":90,"Q4-2026":92,
            "Cal-2027":87,"Cal-2028":85}
    rows = []
    for region in ["NSW1","QLD1","VIC1","SA1"]:
        region_factor = {"NSW1":1.0,"QLD1":0.93,"VIC1":1.05,"SA1":1.20}[region]
        for tenor in tenors:
            mid = round(base[tenor] * region_factor, 4)
            rows.append({
                "curve_date": date.today().isoformat(),
                "instrument_id": f"ASX_{tenor.replace('-','_')}_{region}",
                "region_id": region,
                "tenor": tenor,
                "price": mid,
                "bid": round(mid - 0.50, 4),
                "offer": round(mid + 0.50, 4),
                "volume": round(random.uniform(200, 800), 2),
                "data_source": "SIMULATED"
            })
    truncate_table("apex.market_nem.forward_curves", logger)
    write_batch(rows, "apex.market_nem.forward_curves", 0, logger)

if __name__ == "__main__":
    run_nem_backfill()
```

---

## FILE: data/seeds/market/backfill/epex_backfill.py

```python
"""
EPEX Historical Backfill
Targets:
  apex.market_epex.prices         — 2024-01-01 to present
  apex.market_epex.bess_telemetry — 2024-01-01 to present
  apex.market_epex.forward_curves — quarterly and calendar products

MTU TRANSITION — CRITICAL:
  Before 2024-09-01:  mtu_minutes = 60  (hourly)
  From   2025-09-01:  mtu_minutes = 15  (quarter-hourly)
  This must be faithfully reproduced. The EPEX MTU change is a demo story
  point for the Quant persona ("how did our P&L change after the MTU change?")

Expected volumes:
  prices:         ~130,000 rows pre-Sep-2025 (hourly) +
                  ~170,000 rows post-Sep-2025 (15-min)
                  = ~300,000 total across 8 zones
  bess_telemetry: ~70,000 rows (3 EU assets × daily intervals)
"""
import sys, random
from datetime import datetime, date, timedelta, time as dtime
sys.path.append("../simulators")
from epex_simulator import (generate_epex_price, update_epex_bess,
                             ZONES, EPEX_ASSETS, MTU_CHANGE_DATE)
from backfill_utils import *

logger = logging.getLogger("epex_backfill")

BACKFILL_START = datetime(2024, 1, 1, 0, 0, 0)
BACKFILL_END   = datetime.utcnow()
BATCH_SIZE     = 10000

def run_epex_backfill():
    logger.info(f"EPEX backfill starting: {BACKFILL_START} → {BACKFILL_END}")

    for tbl in ["apex.market_epex.prices", "apex.market_epex.bess_telemetry"]:
        truncate_table(tbl, logger)

    price_buf, bess_buf = [], []
    batch_num = 0
    epex_soc = {a: random.uniform(30, 75) for a in EPEX_ASSETS}

    # Iterate day by day — MTU determines intervals per hour
    current_day = BACKFILL_START.date()
    end_day     = BACKFILL_END.date()

    while current_day <= end_day:
        mtu = 15 if current_day >= MTU_CHANGE_DATE else 60
        intervals_per_hour = 60 // mtu

        for hour in range(24):
            for slot in range(intervals_per_hour):
                dt = datetime.combine(current_day, dtime(hour)) \
                     + timedelta(minutes=slot * mtu)

                for zone in ZONES:
                    price_buf.append(generate_epex_price(zone, dt, mtu))

                # BESS telemetry — hourly for EU assets
                if slot == 0:
                    de_price = next(r["price_eur_mwh"] for r in price_buf[-8:]
                                    if r["bidding_zone"] == "DE-LU")
                    fr_price = next(r["price_eur_mwh"] for r in price_buf[-8:]
                                    if r["bidding_zone"] == "FR")
                    bess_buf.append(update_epex_bess("DE_BESS_1", float(de_price), dt))
                    bess_buf.append(update_epex_bess("FR_BESS_1", float(fr_price), dt))
                    bess_buf.append(update_epex_bess("GB_BESS_1", float(fr_price), dt))

        current_day += timedelta(days=1)

        # Flush batches per day
        if len(price_buf) >= BATCH_SIZE:
            write_batch(price_buf, "apex.market_epex.prices", batch_num, logger)
            price_buf = []; batch_num += 1
        if len(bess_buf) >= BATCH_SIZE:
            write_batch(bess_buf, "apex.market_epex.bess_telemetry", batch_num, logger)
            bess_buf = []

    # Flush remaining
    for buf, tbl in [(price_buf,"apex.market_epex.prices"),
                     (bess_buf,"apex.market_epex.bess_telemetry")]:
        if buf: write_batch(buf, tbl, batch_num, logger)

    for tbl in ["apex.market_epex.prices","apex.market_epex.bess_telemetry"]:
        backfill_summary(tbl, logger)

    # Verification queries — MTU transition
    pre  = spark.sql("""SELECT COUNT(*) AS n FROM apex.market_epex.prices
                        WHERE mtu_minutes = 60""").collect()[0]["n"]
    post = spark.sql("""SELECT COUNT(*) AS n FROM apex.market_epex.prices
                        WHERE mtu_minutes = 15""").collect()[0]["n"]
    logger.info(f"MTU verification: {pre:,} hourly rows, {post:,} quarter-hourly rows")
    assert pre > 0,  "ERROR: No hourly MTU rows — check MTU_CHANGE_DATE logic"
    assert post > 0, "ERROR: No 15-min MTU rows — check MTU_CHANGE_DATE logic"

    # Forward curves
    _backfill_epex_forward_curves()
    logger.info("EPEX backfill complete")

def _backfill_epex_forward_curves():
    """EEX German power forward curve — quarterly and calendar products."""
    products = ["Q1-2026","Q2-2026","Q3-2026","Q4-2026","Cal-2027"]
    base_eur  = {"Q1-2026":78,"Q2-2026":72,"Q3-2026":68,"Q4-2026":82,"Cal-2027":74}
    rows = []
    for zone in ["DE-LU","FR","ES"]:
        zone_factor = {"DE-LU":1.0,"FR":0.97,"ES":0.93}[zone]
        for product in products:
            mid = round(base_eur[product] * zone_factor, 4)
            rows.append({
                "curve_date": date.today().isoformat(),
                "product": product,
                "bidding_zone": zone,
                "price_eur_mwh": mid,
                "bid": round(mid - 0.30, 4),
                "offer": round(mid + 0.30, 4),
                "data_source": "SIMULATED"
            })
    truncate_table("apex.market_epex.forward_curves", logger)
    write_batch(rows, "apex.market_epex.forward_curves", 0, logger)

if __name__ == "__main__":
    run_epex_backfill()
```

---

## FILE: data/seeds/market/backfill/ercot_backfill.py

```python
"""
ERCOT Historical Backfill
Targets:
  apex.market_ercot.lmp           — 2025-01-01 to present (ERCOT only — no pre-2025)
  apex.market_ercot.bess_telemetry— 2025-01-01 to present
  apex.market_ercot.dam_prices    — 2025-01-01 to present

RTC+B BOUNDARY — CRITICAL:
  Before 2025-12-05: rtcb_signal = NULL  (pre-launch)
  From   2025-12-05: rtcb_signal = float (live signal)
  This boundary must be exact. The Quant, Dispatch, and Portfolio personas all
  reference it. Genie queries like "P&L before vs after RTC+B" depend on it.
  Verify with explicit SQL assertion after backfill.

Expected volumes:
  lmp:             ~440,000 rows  (15 months × 10 nodes × 288 intervals/day)
  bess_telemetry:  ~176,000 rows  (15 months × 4 assets × 288 intervals/day)
  dam_prices:      ~44,000 rows   (15 months × 10 nodes × 24 hours/day)
"""
import sys, random
from datetime import datetime, date, timedelta
sys.path.append("../simulators")
from ercot_simulator import (generate_ercot_lmp, update_ercot_bess,
                              NODES, ERCOT_ASSETS, ASSET_NODE, RTCB_LIVE_DATE)
from backfill_utils import *

logger = logging.getLogger("ercot_backfill")

BACKFILL_START = datetime(2025, 1, 1, 0, 0, 0)
BACKFILL_END   = datetime.utcnow()
INTERVAL_MIN   = 5
BATCH_SIZE     = 10000

def run_ercot_backfill():
    logger.info(f"ERCOT backfill starting: {BACKFILL_START} → {BACKFILL_END}")
    logger.info(f"RTC+B live date: {RTCB_LIVE_DATE} — rtcb_signal NULL before, float after")

    for tbl in ["apex.market_ercot.lmp", "apex.market_ercot.bess_telemetry",
                "apex.market_ercot.dam_prices"]:
        truncate_table(tbl, logger)

    lmp_buf, bess_buf, dam_buf = [], [], []
    batch_num = 0

    for dt in date_range(BACKFILL_START, BACKFILL_END, INTERVAL_MIN):
        for node in NODES:
            lmp_buf.append(generate_ercot_lmp(node, dt))

        # BESS telemetry
        hub_prices = {
            "West Hub":    next(r["lmp"] for r in lmp_buf[-10:] if r["node_id"]=="West Hub"),
            "Houston Hub": next(r["lmp"] for r in lmp_buf[-10:] if r["node_id"]=="Houston Hub"),
            "North Hub":   next(r["lmp"] for r in lmp_buf[-10:] if r["node_id"]=="North Hub"),
        }
        for asset in ERCOT_ASSETS:
            node = ASSET_NODE[asset]
            # Map asset node to hub
            hub = "West Hub" if "WEST" in asset else \
                  "Houston Hub" if "HOUSTON" in asset else "North Hub"
            bess_buf.append(update_ercot_bess(asset, float(hub_prices[hub]), dt))

        # Day-ahead prices — generate once per hour
        if dt.minute == 0:
            for node in NODES:
                base_lmp = next(r["lmp"] for r in lmp_buf[-10:] if r["node_id"] == node)
                dam_buf.append({
                    "delivery_datetime": dt,
                    "node_id": node,
                    "dam_lmp": round(float(base_lmp) * random.uniform(0.88, 1.12), 4),
                    "data_source": "SIMULATED"
                })

        # Flush batches
        if len(lmp_buf) >= BATCH_SIZE:
            write_batch(lmp_buf, "apex.market_ercot.lmp", batch_num, logger)
            lmp_buf = []; batch_num += 1
        if len(bess_buf) >= BATCH_SIZE:
            write_batch(bess_buf, "apex.market_ercot.bess_telemetry", batch_num, logger)
            bess_buf = []
        if len(dam_buf) >= BATCH_SIZE:
            write_batch(dam_buf, "apex.market_ercot.dam_prices", batch_num, logger)
            dam_buf = []

    # Flush remaining
    for buf, tbl in [(lmp_buf,"apex.market_ercot.lmp"),
                     (bess_buf,"apex.market_ercot.bess_telemetry"),
                     (dam_buf,"apex.market_ercot.dam_prices")]:
        if buf: write_batch(buf, tbl, batch_num, logger)

    for tbl in ["apex.market_ercot.lmp","apex.market_ercot.bess_telemetry",
                "apex.market_ercot.dam_prices"]:
        backfill_summary(tbl, logger)

    # ── CRITICAL: RTC+B boundary verification ────────────────────────────
    pre_null = spark.sql("""
        SELECT COUNT(*) AS n FROM apex.market_ercot.lmp
        WHERE interval_datetime < '2025-12-05' AND rtcb_signal IS NOT NULL
    """).collect()[0]["n"]

    post_null = spark.sql("""
        SELECT COUNT(*) AS n FROM apex.market_ercot.lmp
        WHERE interval_datetime >= '2025-12-05' AND rtcb_signal IS NULL
    """).collect()[0]["n"]

    pre_count = spark.sql("""
        SELECT COUNT(*) AS n FROM apex.market_ercot.lmp
        WHERE interval_datetime < '2025-12-05'
    """).collect()[0]["n"]

    post_count = spark.sql("""
        SELECT COUNT(*) AS n FROM apex.market_ercot.lmp
        WHERE interval_datetime >= '2025-12-05'
    """).collect()[0]["n"]

    logger.info(f"RTC+B boundary check:")
    logger.info(f"  Pre-Dec-2025:  {pre_count:,} rows — {pre_null} have rtcb_signal (should be 0)")
    logger.info(f"  Post-Dec-2025: {post_count:,} rows — {post_null} have NULL rtcb_signal (should be 0)")

    assert pre_null  == 0, f"FAIL: {pre_null} pre-RTC+B rows have a signal — check generator logic"
    assert post_null == 0, f"FAIL: {post_null} post-RTC+B rows have NULL signal — check generator logic"
    logger.info("RTC+B boundary verification PASSED")

    logger.info("ERCOT backfill complete")

if __name__ == "__main__":
    run_ercot_backfill()
```

---

## FILE: data/seeds/market/backfill/run_all_backfills.py

```python
"""
Master backfill runner. Executes all three market backfills sequentially.
Run this ONCE before starting the continuous simulators.
Total estimated runtime: 15–45 minutes depending on cluster size.

Order: NEM → EPEX → ERCOT
Reason: NEM is largest, ERCOT needs RTC+B boundary asserted last.
"""
import time, logging
from nem_backfill  import run_nem_backfill
from epex_backfill import run_epex_backfill
from ercot_backfill import run_ercot_backfill
from backfill_utils import spark

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_all_backfills")

def run():
    start = time.time()
    logger.info("=" * 60)
    logger.info("APEX Historical Backfill — All Markets")
    logger.info("=" * 60)

    # ── NEM ──────────────────────────────────────────────────────
    logger.info("\n[1/3] Starting NEM backfill")
    t = time.time()
    run_nem_backfill()
    logger.info(f"NEM complete in {(time.time()-t)/60:.1f} min")

    # ── EPEX ─────────────────────────────────────────────────────
    logger.info("\n[2/3] Starting EPEX backfill")
    t = time.time()
    run_epex_backfill()
    logger.info(f"EPEX complete in {(time.time()-t)/60:.1f} min")

    # ── ERCOT ────────────────────────────────────────────────────
    logger.info("\n[3/3] Starting ERCOT backfill")
    t = time.time()
    run_ercot_backfill()
    logger.info(f"ERCOT complete in {(time.time()-t)/60:.1f} min")

    # ── Final verification ────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("BACKFILL COMPLETE — Final row counts")
    logger.info("=" * 60)

    checks = [
        ("apex.market_nem.prices",          500000, 700000),
        ("apex.market_nem.generation",       500000, 700000),
        ("apex.market_nem.bess_telemetry",   700000, 900000),
        ("apex.market_nem.predispatch",      100000, 200000),
        ("apex.market_nem.forward_curves",       20,    100),
        ("apex.market_epex.prices",          200000, 400000),
        ("apex.market_epex.bess_telemetry",   40000,  80000),
        ("apex.market_epex.forward_curves",      10,    50),
        ("apex.market_ercot.lmp",            350000, 500000),
        ("apex.market_ercot.bess_telemetry", 140000, 200000),
        ("apex.market_ercot.dam_prices",      30000,  60000),
    ]

    all_ok = True
    for tbl, min_rows, max_rows in checks:
        n = spark.sql(f"SELECT COUNT(*) AS n FROM {tbl}").collect()[0]["n"]
        status = "OK" if min_rows <= n <= max_rows else "WARNING — outside expected range"
        logger.info(f"  {tbl:<45} {n:>10,} rows  [{status}]")
        if status != "OK":
            all_ok = False

    if all_ok:
        logger.info(f"\nAll checks passed. Total time: {(time.time()-start)/60:.1f} min")
        logger.info("You may now start the continuous simulators (W03 orchestrator).")
    else:
        logger.warning("\nSome row counts outside expected range — review above.")

    logger.info("=" * 60)

if __name__ == "__main__":
    run()
```

---

## Post-backfill verification SQL

Run these in a notebook after backfills complete to confirm data quality before starting the app:

```sql
-- NEM: Spike events present?
SELECT COUNT(*) AS spikes FROM apex.market_nem.prices WHERE rrp > 1000;
-- Expected: > 500

-- NEM: Negative prices present?
SELECT COUNT(*) AS negatives FROM apex.market_nem.prices WHERE rrp < 0;
-- Expected: > 1000 (summer midday QLD/SA events)

-- NEM: FCAS data populated?
SELECT AVG(raise6sec) FROM apex.market_nem.prices;
-- Expected: non-null, roughly 8–15

-- EPEX: MTU transition correct?
SELECT mtu_minutes, COUNT(*) AS n
FROM apex.market_epex.prices
GROUP BY mtu_minutes ORDER BY mtu_minutes;
-- Expected: two rows: 60 (pre-Sep-2025), 15 (post-Sep-2025)

-- EPEX: Negative prices present?
SELECT COUNT(*) FROM apex.market_epex.prices WHERE price_eur_mwh < 0;
-- Expected: > 200 (DE-LU and ES solar events)

-- ERCOT: RTC+B boundary exact?
SELECT
  SUM(CASE WHEN interval_datetime < '2025-12-05' AND rtcb_signal IS NOT NULL THEN 1 ELSE 0 END) AS pre_violations,
  SUM(CASE WHEN interval_datetime >= '2025-12-05' AND rtcb_signal IS NULL THEN 1 ELSE 0 END) AS post_violations
FROM apex.market_ercot.lmp;
-- Expected: both = 0

-- ERCOT: Panhandle wind congestion negative?
SELECT AVG(congestion_component)
FROM apex.market_ercot.lmp
WHERE node_id LIKE 'Panhandle%';
-- Expected: negative (wind congestion discount)

-- All BESS assets have SOC data?
SELECT asset_id, COUNT(*) AS rows, AVG(state_of_charge_pct) AS avg_soc
FROM apex.market_nem.bess_telemetry GROUP BY asset_id ORDER BY asset_id;
-- Expected: 8 assets, avg SOC 30–70%, no NULLs
```

---

## SUCCESS CRITERIA
1. `run_all_backfills.py` completes without assertion errors
2. All row counts within expected ranges (printed by master script)
3. NEM: spike count > 500, negative price count > 1000
4. EPEX: two distinct mtu_minutes values (60 and 15), transition at 2025-09-01
5. EPEX: negative prices present in DE-LU and ES zones
6. ERCOT: `pre_violations = 0` AND `post_violations = 0` for RTC+B boundary
7. ERCOT: Panhandle Wind nodes have negative avg congestion component
8. All BESS assets across all 3 markets have SOC data with avg between 20–80%
9. forward_curves populated for NEM (ASX) and EPEX (EEX) products
10. All scripts re-runnable (idempotent via TRUNCATE before insert)
11. Continuous simulators started AFTER backfill completes — no overlap

## COMPLETION ARTIFACT
completions/W04-historical-backfill.md
Commit: "feat: W04 complete — historical backfill all three markets"
