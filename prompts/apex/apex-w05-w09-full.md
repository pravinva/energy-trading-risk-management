# APEX W05–W09: Trade Seeds + Backend Core + Market/Trade/Dispatch APIs

---

# W05 — Trade Book Seeds (Multi-Market)

## PREREQUISITE CHECK
Verify completions/W03-market-simulators.md exists.

## OBJECTIVE
Seed realistic pre-existing trade books for all three markets. Trades are seeded directly into `apex.ingestion.raw_etrm_trades` as JSON payloads, then flow through DLT into `apex.trading.trades` — preserving the ETRM ingestion story.

## FILES

### data/seeds/trades/seed_etrm_trades.py

```python
"""
Seeds trade data into apex.ingestion.raw_etrm_trades as JSON payloads,
simulating records arriving from ALIGNE_SIM (NEM), ENDUR_SIM (EPEX),
TRIPLE_POINT_SIM (ERCOT).
The DLT pipeline then processes these into apex.trading.trades.
"""
import json, uuid, random
from decimal import Decimal
from datetime import datetime, timedelta
from databricks.connect import DatabricksSession
from pyspark.sql import Row

spark = DatabricksSession.builder.profile("fe-vm").getOrCreate()

def days_ago(n): return datetime.utcnow() - timedelta(days=n)
def quarter(dt): return f"{dt.year}-Q{(dt.month-1)//3+1}"

# ── NEM TRADES (source: ALIGNE_SIM) ──────────────────────────────
NEM_TRADES = []
NEM_INSTRUMENTS = ["NEM_SPOT_NSW1","NEM_SPOT_QLD1","NEM_SPOT_VIC1",
                   "NEM_SPOT_SA1","ASX_CAL27_NSW1","ASX_CAL27_QLD1",
                   "ASX_Q1_26_VIC1","CAP_NSW1_Q1","PPA_NEOEN_SA"]
NEM_TRADERS   = ["SCHEN","JWUU","EPARK"]
NEM_CPS       = ["AGL","ORIGIN","ENERGYAUST","CSENERGY","STANWELL","NEOEN","SNOWY","SHELL_AUS"]

for i in range(55):
    dt = days_ago(random.randint(1, 90))
    direction = "BUY" if random.random() < 0.55 else "SELL"
    instr = random.choice(NEM_INSTRUMENTS)
    price_base = {"NEM_SPOT_NSW1":90,"NEM_SPOT_QLD1":82,"NEM_SPOT_VIC1":95,
                  "NEM_SPOT_SA1":112,"ASX_CAL27_NSW1":88,"ASX_CAL27_QLD1":80,
                  "ASX_Q1_26_VIC1":92,"CAP_NSW1_Q1":5,"PPA_NEOEN_SA":72}.get(instr,85)
    vol = round(random.choice([50,75,100,150,200,250,300,400,500]) * random.uniform(0.8,1.2), 2)
    status = random.choices(["CONFIRMED","CONFIRMED","CONFIRMED","CONFIRMED",
                              "PARTIALLY_FILLED","CANCELLED"],weights=[4,4,4,4,1,1])[0]
    NEM_TRADES.append({
        "trade_id": str(uuid.uuid4()),
        "market": "NEM",
        "instrument_id": instr,
        "counterparty_id": random.choice(NEM_CPS),
        "trader_id": random.choice(NEM_TRADERS),
        "direction": direction,
        "volume_mw": float(vol),
        "price": round(price_base * random.uniform(0.92, 1.08), 4),
        "delivery_start": (dt + timedelta(hours=random.randint(1,720))).isoformat(),
        "delivery_end":   (dt + timedelta(hours=random.randint(721,2160))).isoformat(),
        "trade_type": random.choice(["SPOT","SPOT","BILATERAL","FUTURES","FUTURES","CAP","PPA"]),
        "region_id": instr.split("_")[-1] if "SPOT" in instr else "NSW1",
        "status": status,
        "trade_timestamp": dt.isoformat()
    })

# ── EPEX TRADES (source: ENDUR_SIM) ──────────────────────────────
EPEX_TRADES = []
EPEX_INSTRUMENTS = ["EPEX_DA_DE_LU","EPEX_DA_FR","EPEX_DA_BE",
                    "EPEX_INTRA_DE_LU","EEX_CAL27_DE","EU_ETS_DEC26"]
EPEX_TRADERS = ["HMÜLLER","SDUPONT"]
EPEX_CPS     = ["SHELL_EU","TOTALENERGIES","AXPO","EQUINOR","EDF"]

for i in range(30):
    dt = days_ago(random.randint(1, 60))
    direction = "BUY" if random.random() < 0.50 else "SELL"
    instr = random.choice(EPEX_INSTRUMENTS)
    price_base = {"EPEX_DA_DE_LU":70,"EPEX_DA_FR":68,"EPEX_DA_BE":72,
                  "EPEX_INTRA_DE_LU":68,"EEX_CAL27_DE":65,"EU_ETS_DEC26":60}.get(instr,65)
    EPEX_TRADES.append({
        "trade_id": str(uuid.uuid4()),
        "market": "EPEX",
        "instrument_id": instr,
        "counterparty_id": random.choice(EPEX_CPS),
        "trader_id": random.choice(EPEX_TRADERS),
        "direction": direction,
        "volume_mw": float(round(random.choice([50,100,150,200,250]), 2)),
        "price": round(price_base * random.uniform(0.90, 1.10), 4),
        "delivery_start": (dt + timedelta(hours=random.randint(1,168))).isoformat(),
        "delivery_end":   (dt + timedelta(hours=random.randint(169,720))).isoformat(),
        "trade_type": random.choice(["DA","DA","INTRADAY","FUTURES","SWAP"]),
        "region_id": instr.split("_")[-1] if "DA" in instr else "DE-LU",
        "status": "CONFIRMED" if random.random() < 0.85 else "PARTIALLY_FILLED",
        "trade_timestamp": dt.isoformat()
    })

# ── ERCOT TRADES (source: TRIPLE_POINT_SIM) ──────────────────────
ERCOT_TRADES = []
ERCOT_INSTRUMENTS = ["ERCOT_RT_WEST","ERCOT_RT_HOUSTON","ERCOT_DA_WEST",
                     "ERCOT_DA_NORTH","ERCOT_SWAP_WEST_Q1"]
ERCOT_TRADERS = ["TJOHNSON","LRODRIGUEZ"]
ERCOT_CPS     = ["VISTRA","NRG","MACQUARIE","VITOL","CALPINE"]

for i in range(30):
    dt = days_ago(random.randint(1, 60))
    direction = "BUY" if random.random() < 0.52 else "SELL"
    instr = random.choice(ERCOT_INSTRUMENTS)
    price_base = {"ERCOT_RT_WEST":46,"ERCOT_RT_HOUSTON":51,"ERCOT_DA_WEST":44,
                  "ERCOT_DA_NORTH":43,"ERCOT_SWAP_WEST_Q1":42}.get(instr,45)
    ERCOT_TRADES.append({
        "trade_id": str(uuid.uuid4()),
        "market": "ERCOT",
        "instrument_id": instr,
        "counterparty_id": random.choice(ERCOT_CPS),
        "trader_id": random.choice(ERCOT_TRADERS),
        "direction": direction,
        "volume_mw": float(round(random.choice([50,100,150,200,250,300]), 2)),
        "price": round(price_base * random.uniform(0.88, 1.12), 4),
        "delivery_start": (dt + timedelta(hours=random.randint(1,168))).isoformat(),
        "delivery_end":   (dt + timedelta(hours=random.randint(169,720))).isoformat(),
        "trade_type": random.choice(["RT","RT","DA","SWAP","BILATERAL"]),
        "region_id": instr.split("_")[-1],
        "status": "CONFIRMED" if random.random() < 0.88 else "PARTIALLY_FILLED",
        "trade_timestamp": dt.isoformat()
    })

# ── INSERT into raw_etrm_trades ───────────────────────────────────
def make_raw_rows(trades, source_system, market):
    return [Row(
        source_system=source_system,
        market=market,
        payload=json.dumps(t),
        processed=False
    ) for t in trades]

rows = (
    make_raw_rows(NEM_TRADES,   "ALIGNE_SIM",       "NEM")  +
    make_raw_rows(EPEX_TRADES,  "ENDUR_SIM",        "EPEX") +
    make_raw_rows(ERCOT_TRADES, "TRIPLE_POINT_SIM", "ERCOT")
)
df = spark.createDataFrame(rows)
df.write.mode("append").saveAsTable("apex.ingestion.raw_etrm_trades")
print(f"Inserted {len(rows)} raw trade records. DLT will process within 60s.")
```

### data/seeds/trades/seed_offer_stacks.sql
Insert 5 pre-seeded offer stacks (2 NEM, 2 ERCOT, 1 EPEX) into apex.trading.offer_stacks and offer_bands. Each with 10 bands. ERCOT stacks show rtcb-eligible assets.

### data/seeds/trades/seed_pnl_daily.py
Insert 90 days of P&L for all traders, all markets, correct currency per market.
NEM: AUD, EPEX: EUR, ERCOT: USD.

### data/seeds/trades/seed_ppa_book.sql
Insert 5 PPAs across all markets:
- NEM: APEX_PPA_001 (Long 100MW Neoen, A$72/MWh), APEX_PPA_002 (Short 80MW AGL, A$95/MWh)
- EPEX: EU_PPA_001 (Long 150MW Equinor wind, €58/MWh)
- ERCOT: TX_PPA_001 (Long 200MW Vistra wind, $35/MWh)
- NEM: APEX_PPA_003 (Long 80MW Pacific Hydro, A$85/MWh)

### data/seeds/trades/seed_revenue_actuals.py
12 months of daily revenue for all 15 BESS assets, correct currency per market. ERCOT assets: rtcb_revenue IS NULL before 2025-12-05, populated after.

### data/seeds/trades/00_run_all.py
Master script: runs all seed files in order with progress logging.

## SUCCESS CRITERIA
1. `apex.ingestion.raw_etrm_trades`: 115 rows (55 NEM + 30 EPEX + 30 ERCOT)
2. After DLT processes: `apex.trading.trades` has same 115 rows with ingested_at populated
3. `apex.trading.offer_stacks`: 5 stacks × 10 bands = 50 band rows
4. `apex.trading.pnl_daily`: 90 × (9 traders across 3 markets) rows
5. `apex.portfolio.ppa_book`: 5 rows, currencies AUD/EUR/USD
6. `apex.portfolio.revenue_actuals`: ERCOT assets show rtcb_revenue NULL/NOT NULL boundary at 2025-12-05
7. source_system column shows ALIGNE_SIM/ENDUR_SIM/TRIPLE_POINT_SIM correctly

## COMPLETION ARTIFACT
completions/W05-seeds.md
Commit: "feat: W05 complete — multi-market trade seeds via ETRM ingestion"

---

# W06 — Backend Core

## PREREQUISITE CHECK
Verify completions/W00-foundation.md AND completions/W02-schema.md exist.

## FILE: app/backend/config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    databricks_host: str = ""
    lakebase_host: str = ""
    lakebase_database: str = "apex"
    lakebase_port: int = 5432
    sql_warehouse_id: str = ""
    apex_environment: str = "dev"
    app_version: str = "1.0.0"

    # Cache TTLs
    cache_ttl_market: int = 15      # seconds — market prices
    cache_ttl_positions: int = 10   # seconds — positions
    cache_ttl_reference: int = 600  # seconds — reference data

    # Engine config
    var_simulation_count: int = 10000

    class Config:
        env_file = ".env"

settings = Settings()
```

## FILE: app/backend/database.py
Four-tier serving pattern (from sourabhghose/databricks-energy-copilot):
1. Lakebase (psycopg3): <20ms — for VaR results, offer stacks, backtest runs
2. SQL Warehouse (databricks-sql-connector): 400–1000ms — for analytics queries
3. In-memory TTL cache (cachetools): <1ms — for repeated identical calls

Lakebase is NOT used for trade/position reads (those go via SQL Warehouse to Delta).

```python
import psycopg
from cachetools import TTLCache
from databricks import sql as dbsql
from databricks.sdk import WorkspaceClient
from contextlib import asynccontextmanager
from typing import Any
import asyncio

# Caches
_market_cache    = TTLCache(maxsize=200, ttl=15)
_position_cache  = TTLCache(maxsize=100, ttl=10)
_reference_cache = TTLCache(maxsize=50,  ttl=600)

async def query_warehouse(sql_text: str, params: dict = None,
                          cache: TTLCache = None, cache_key: str = None) -> list[dict]:
    """Query SQL Warehouse — used for Delta table analytics reads."""
    if cache and cache_key and cache_key in cache:
        return cache[cache_key]
    # ... databricks-sql-connector execution
    # result stored in cache if provided
    ...

@asynccontextmanager
async def get_lakebase():
    """Psycopg3 async connection to Lakebase. Used for operational writes."""
    conn = await psycopg.AsyncConnection.connect(
        host=settings.lakebase_host,
        dbname=settings.lakebase_database,
        port=settings.lakebase_port
    )
    try:
        yield conn
        await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()

async def write_lakebase_and_sync_delta(
    lakebase_sql: str, params: tuple,
    delta_table: str, record: dict
):
    """
    Write to Lakebase (fast operational store) then async append to Delta (Genie queryable).
    Used for VaR results, offer stacks, backtest runs.
    """
    async with get_lakebase() as conn:
        await conn.execute(lakebase_sql, params)
    # Non-blocking Delta append for Genie discoverability
    asyncio.create_task(_append_to_delta(delta_table, record))

async def _append_to_delta(table: str, record: dict):
    """Background task — appends a single record to Delta via SQL Warehouse."""
    ...
```

## FILE: app/backend/auth.py
```python
async def get_current_user_email(request: Request) -> str:
    """Extract user email from Databricks token context."""
    ...

async def get_trader_context(email: str, market: str) -> dict | None:
    """Lookup trader by email in apex.reference.traders filtered by market."""
    ...

def get_market_from_path(request: Request) -> str:
    """Extract market from URL path — /api/v1/{market}/..."""
    ...
```

## ENGINES

### app/backend/engines/pnl.py
Pure Python. No FastAPI. No DB. All Decimal arithmetic.

```python
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class PositionPnL:
    net_volume_mw: Decimal
    avg_entry_price: Decimal
    current_market_price: Decimal
    delivery_hours: Decimal
    currency: str

def calculate_mtm_pnl(p: PositionPnL) -> Decimal:
    """(current_price - avg_entry) × net_volume × hours"""
    return (p.current_market_price - p.avg_entry_price) * p.net_volume_mw * p.delivery_hours

def calculate_realised_pnl(closed_trades: list, closing_price: Decimal) -> Decimal: ...

def aggregate_desk_pnl(positions: list[dict], market_prices: dict[str, Decimal]) -> dict:
    """Returns: total_mtm, total_realised, by_instrument, by_region, currency."""
    ...
```

Tests: long position price up = positive, short position price up = negative, zero position = zero, Decimal precision (no float error), negative market prices (NEM/EPEX scenarios).

### app/backend/engines/var.py
```python
import numpy as np
from decimal import Decimal
from dataclasses import dataclass, field

@dataclass
class VaRInput:
    positions: list[dict]
    price_returns: dict[str, list[float]]
    simulation_count: int = 10000
    confidence_levels: list[float] = field(default_factory=lambda: [0.95, 0.99])
    currency: str = "AUD"

@dataclass
class VaRResult:
    var_95: Decimal
    var_99: Decimal
    cvar_95: Decimal
    cvar_99: Decimal
    position_value: Decimal
    pnl_distribution: list[float]  # 100 histogram buckets
    currency: str

def run_monte_carlo_var(inputs: VaRInput) -> VaRResult:
    """
    1. Compute historical volatility per instrument from price_returns
    2. Compute correlation matrix across instruments
    3. Cholesky decomposition for correlated random draws
    4. Apply shocked prices to current positions (10,000 simulations)
    5. Extract VaR at 95% and 99%
    6. Calculate CVaR (Expected Shortfall beyond VaR)
    7. Bucket distribution into 100 bins for histogram
    """
    ...

def run_stress_test(positions: list[dict], scenario: dict,
                    current_prices: dict[str, float]) -> dict: ...

def calculate_historical_returns(price_series: list[float],
                                  window_days: int = 252) -> list[float]: ...
```

Tests: VaR99 > VaR95 always, CVaR > VaR always, zero position VaR = 0, 10k simulations run, stress test shock applied correctly.

### app/backend/engines/position.py
```python
def aggregate_positions(trades: list[dict]) -> list[dict]: ...
def check_position_limits(positions: list[dict], limits: dict) -> list[dict]: ...
def net_position_by_region(positions: list[dict]) -> dict: ...
def net_exposure_heatmap(positions: list[dict]) -> dict:
    """Returns {region: {delivery_period: net_mw}} for heatmap rendering."""
    ...
```

### app/backend/engines/dispatch.py
```python
@dataclass
class DispatchInput:
    asset_id: str
    market: str
    current_soc_pct: float
    capacity_mw: float
    duration_hours: float
    forecast_prices: list[float]
    fcas_prices: dict[str, list[float]]
    rtcb_signal: float | None  # ERCOT only — None if pre-launch or NEM/EPEX

@dataclass
class DispatchRecommendation:
    interval_datetime: str
    recommended_energy_mw: float
    recommended_price: float
    fcas_raise_mw: float
    fcas_lower_mw: float
    rtcb_adjusted: bool  # True if RTC+B signal was used in recommendation
    confidence_score: float
    expected_revenue: float
    currency: str
    rationale: str

def get_dispatch_recommendation(inputs: DispatchInput,
                                 model_endpoint: str) -> DispatchRecommendation: ...
def build_offer_stack(rec: DispatchRecommendation,
                       asset_capacity_mw: float) -> list[dict]: ...
def check_rebid_compliance(original: list[dict], proposed: list[dict],
                            interval: str, reason: str,
                            market: str) -> dict: ...
```

## FILE: app/backend/app.py
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .routes import health, user, market, trades, positions, dispatch, risk, portfolio, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init four-tier connections
    await init_lakebase_pool()
    await init_warehouse_connection()
    yield
    await cleanup_connections()

app = FastAPI(title="APEX Energy Analytics", lifespan=lifespan)

# All routes prefixed with /api/v1/
# Market-specific routes: /api/v1/market/{market}/...
app.include_router(health.router,    prefix="/api/v1")
app.include_router(user.router,      prefix="/api/v1")
app.include_router(market.router,    prefix="/api/v1")
app.include_router(trades.router,    prefix="/api/v1")
app.include_router(positions.router, prefix="/api/v1")
app.include_router(dispatch.router,  prefix="/api/v1")
app.include_router(risk.router,      prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

## SUCCESS CRITERIA
1. All engine unit tests pass — zero tolerance
2. pnl/var/position/dispatch engines have zero FastAPI or DB imports
3. mypy --strict passes on all backend files
4. GET /api/v1/health/ returns lakebase_connected: true
5. Decimal used for all price/P&L arithmetic — verified by test

## COMPLETION ARTIFACT
completions/W06-backend-core.md
Commit: "feat: W06 complete — backend core and engines"

---

# W07 — Market Data API

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W03-market-simulators.md exist.

## SQL QUERIES: data/queries/market/

### nem_prices_current.sql
```sql
SELECT region_id, rrp, raise6sec, lower6sec, raisereg, lowerreg,
       totaldemand, interval_datetime,
       rrp - LAG(rrp) OVER (PARTITION BY region_id ORDER BY interval_datetime) AS change_vs_prev,
       rrp > 1000 AS is_spike,
       rrp < 0 AS is_negative
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) AS rn
  FROM apex.market_nem.prices
) WHERE rn = 1
```

### nem_prices_history.sql — parameterised :region_id :hours
### nem_predispatch.sql — latest 12 intervals per region :region_id
### nem_bess_telemetry.sql — latest per asset :asset_id (optional)
### nem_forward_curves.sql — :region_id (optional) :tenor (optional)
### epex_prices_current.sql — latest per zone, includes mtu_minutes
### epex_prices_history.sql — :zone :hours
### epex_bess_telemetry.sql
### ercot_lmp_current.sql — latest per node, includes rtcb_signal
### ercot_lmp_history.sql — :node_id :hours
### ercot_bess_telemetry.sql
### market_summary.sql — one row per market: avg price, 24h change, status, currency

## ROUTES: app/backend/routes/market.py

All routes return `APIResponse[T]`. All accept `?market=NEM|EPEX|ERCOT`.
The market parameter is used to select the correct schema (market_nem / market_epex / market_ercot).

```python
# NEM routes
GET /api/v1/market/nem/prices/current     # 5 regions, refetch 15s
GET /api/v1/market/nem/prices/history     # ?region_id&hours=24
GET /api/v1/market/nem/predispatch        # ?region_id, 12 intervals
GET /api/v1/market/nem/bess/telemetry     # ?asset_id optional
GET /api/v1/market/nem/forward-curves     # ?region_id&tenor

# EPEX routes
GET /api/v1/market/epex/prices/current    # 8 zones, includes mtu_minutes
GET /api/v1/market/epex/prices/history    # ?zone&hours=24
GET /api/v1/market/epex/bess/telemetry
GET /api/v1/market/epex/forward-curves    # ?zone&product

# ERCOT routes
GET /api/v1/market/ercot/lmp/current      # 10 nodes, includes rtcb_signal
GET /api/v1/market/ercot/lmp/history      # ?node_id&hours=24
GET /api/v1/market/ercot/bess/telemetry
GET /api/v1/market/ercot/dam              # day-ahead prices

# Cross-market
GET /api/v1/market/summary                # All 3 markets — for topbar ticker
```

### Pydantic models
```python
class NEMPrice(BaseModel):
    region_id: str; rrp: Decimal; raise6sec: Decimal; lower6sec: Decimal
    raisereg: Decimal; lowerreg: Decimal; totaldemand: Decimal
    interval_datetime: datetime; change_vs_prev: Decimal | None
    is_spike: bool; is_negative: bool; currency: str = "AUD"

class EPEXPrice(BaseModel):
    bidding_zone: str; delivery_datetime: datetime
    price_eur_mwh: Decimal; volume_mwh: Decimal
    mtu_minutes: int; auction_type: str; currency: str = "EUR"

class ERCOTPrice(BaseModel):
    node_id: str; interval_datetime: datetime
    lmp: Decimal; energy_component: Decimal
    congestion_component: Decimal; loss_component: Decimal
    rtcb_signal: Decimal | None  # None before 2025-12-05
    currency: str = "USD"

class BESSTelemetry(BaseModel):
    asset_id: str; market: str; recorded_at: datetime
    state_of_charge_pct: Decimal; output_mw: Decimal
    fcas_raise_mw: Decimal | None; fcas_lower_mw: Decimal | None
    rtcb_signal: Decimal | None  # ERCOT only
    available_mw: Decimal

class MarketSummary(BaseModel):
    market_id: str; avg_price: Decimal; change_24h: Decimal
    volatility_24h: Decimal; status: str; currency: str
    price_unit: str  # $/MWh | €/MWh
```

## SUCCESS CRITERIA
1. All routes 200 with live simulator data
2. NEM prices update with each 30s simulator tick (verify Last-Modified header)
3. EPEX returns mtu_minutes=15 for current rows (post-Sep 2025)
4. ERCOT returns rtcb_signal: null for historical rows pre-Dec 2025
5. Market summary returns 3 rows (NEM/EPEX/ERCOT) with correct currencies

## COMPLETION ARTIFACT
completions/W07-market-api.md
Commit: "feat: W07 complete — multi-market data API"

---

# W08 — Trade Analytics API (Read-Only)

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-seeds.md exist.

## CRITICAL: This API is READ-ONLY for trades/positions.
No POST /trades. No order entry. Trades arrive via ETRM ingestion (DLT).
Lakebase writes in this workstream: none. All reads via SQL Warehouse → Delta.

## SQL QUERIES: data/queries/trades/

### trade_blotter.sql
```sql
SELECT t.trade_id, t.trade_timestamp, t.instrument_id, i.instrument_name,
       t.counterparty_id, c.short_name AS counterparty_name,
       t.trader_id, tr.name AS trader_name,
       t.direction, t.volume_mw, t.price, t.trade_type,
       t.market, t.region_id, t.delivery_start, t.delivery_end,
       t.status, t.source_system, t.ingested_at
FROM apex.trading.trades t
LEFT JOIN apex.reference.instruments i ON i.instrument_id = t.instrument_id
LEFT JOIN apex.reference.counterparties c ON c.counterparty_id = t.counterparty_id
LEFT JOIN apex.reference.traders tr ON tr.trader_id = t.trader_id
WHERE (:trader_id IS NULL OR t.trader_id = :trader_id)
  AND (:market IS NULL OR t.market = :market)
  AND (:status IS NULL OR t.status = :status)
  AND t.trade_timestamp >= CURRENT_TIMESTAMP - INTERVAL :days DAYS
ORDER BY t.trade_timestamp DESC
```

### position_book.sql — joins positions with latest market prices
### pnl_summary.sql — daily P&L per trader per market :days
### pnl_attribution.sql — P&L by region/instrument/trader :date :market
### exposure_heatmap.sql — net MW by region × delivery_period :market :trader_id
### source_lag.sql — last sync time per source_system per market

## ROUTES: app/backend/routes/trades.py + positions.py

```python
# Trades — read only
GET /api/v1/trades/              # blotter ?market&trader_id&status&days=30
GET /api/v1/trades/{trade_id}    # single trade

# Positions — read only, with live MTM
GET /api/v1/positions/           # position book ?market&trader_id
GET /api/v1/positions/pnl-summary    # ?market&trader_id&days=30
GET /api/v1/positions/pnl-attribution # ?market&date
GET /api/v1/positions/exposure-heatmap # ?market&trader_id — for heatmap component
GET /api/v1/positions/source-lag      # ETRM data freshness per source
```

### source-lag endpoint — key demo talking point
```python
class SourceLagStatus(BaseModel):
    market: str
    source_system: str        # ALIGNE_SIM | ENDUR_SIM | TRIPLE_POINT_SIM
    last_sync_at: datetime
    records_last_24h: int
    lag_seconds: int
    status: str               # FRESH | STALE | DELAYED

@router.get("/positions/source-lag")
async def get_source_lag() -> list[SourceLagStatus]:
    """
    Demo talking point: 'Here is exactly when data last arrived from Endur.'
    Queries apex.ingestion.etrm_sync_log for freshness per source.
    """
```

### MTM P&L calculation (server-side, on every positions/ call)
Join positions with latest market price per instrument:
- NEM: join to apex.market_nem.prices latest rrp per region
- EPEX: join to apex.market_epex.prices latest price_eur_mwh per zone
- ERCOT: join to apex.market_ercot.lmp latest lmp per node

MTM = (current_price - avg_entry_price) × net_volume_mw × delivery_hours_remaining

## SUCCESS CRITERIA
1. GET /positions/ returns positions with non-null mtm_pnl
2. source_lag shows correct ETRM source per market
3. exposure_heatmap returns {region: {period: net_mw}} structure
4. All Decimal — no float in response models
5. After simulator writes new price rows, GET /positions/ MTM updates on next request

## COMPLETION ARTIFACT
completions/W08-trade-analytics-api.md
Commit: "feat: W08 complete — trade analytics API (read-only)"

---

# W09 — Dispatch & Offer Stack API

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-seeds.md exist.

## This workstream uses Lakebase for writes (offer stacks + bands).
After every Lakebase write, async append to Delta for Genie.

## SQL QUERIES: data/queries/dispatch/

### asset_fleet_status.sql — latest telemetry per asset :market (optional)
### offer_stack_current.sql — active stack per asset × service :asset_id :service_type
### offer_stack_history.sql — last N submissions :asset_id :days
### dispatch_recommendations.sql — latest 12 per asset :asset_id
### nem_predispatch_for_asset.sql — pre-dispatch for asset's region

## ROUTES: app/backend/routes/dispatch.py

```python
GET  /api/v1/dispatch/fleet                                    # all assets, ?market
GET  /api/v1/dispatch/{asset_id}/status                        # single asset, refetch 15s
GET  /api/v1/dispatch/{asset_id}/offer-stack                   # ?service_type=ENERGY
POST /api/v1/dispatch/{asset_id}/offer-stack                   # submit new stack → Lakebase
PATCH /api/v1/dispatch/{asset_id}/offer-stack/{stack_id}/rebid # rebid → Lakebase
POST /api/v1/dispatch/{asset_id}/compliance-check              # pre-validate without writing
GET  /api/v1/dispatch/{asset_id}/recommendations               # 12 ML/deterministic recs
POST /api/v1/dispatch/{asset_id}/recommendations/accept/{rec_id} # creates offer stack
GET  /api/v1/dispatch/{asset_id}/stack-history                 # ?days=7
```

### Offer stack submission (POST) — Lakebase write flow
```python
@router.post("/{asset_id}/offer-stack")
async def submit_offer_stack(asset_id: str, draft: OfferStackDraft):
    # 1. Validate (10 bands, ascending prices, sum ≤ capacity, price range)
    validate_offer_stack(draft)
    
    # 2. Write to Lakebase
    stack_id = str(uuid.uuid4())
    async with get_lakebase() as conn:
        await conn.execute(INSERT_STACK_SQL, (stack_id, asset_id, ...))
        for band in draft.bands:
            await conn.execute(INSERT_BAND_SQL, (stack_id, band.band_number, ...))
    
    # 3. Async append to Delta for Genie
    asyncio.create_task(append_stack_to_delta(stack_id, draft))
    
    return OfferStack(stack_id=stack_id, ...)
```

### Market-specific validation rules
NEM:
- Price range: -A$1,000 to A$15,200 (AEMO market cap/floor)
- Service types: ENERGY, FCAS_RAISE6SEC, FCAS_LOWER6SEC, FCAS_RAISE5MIN, FCAS_LOWER5MIN, FCAS_RAISEREG, FCAS_LOWERREG
- Rebid reason required (NEL s.254 good faith)

EPEX:
- Price range: -€500 to €3,000
- Service types: ENERGY, BALANCING_RESERVE
- No rebid concept — stack replacement model

ERCOT:
- Price range: -$250 to $5,000 (ERCOT LCAP)
- Service types: ENERGY, REGUP, REGDOWN, ECRS
- RTC+B: if asset is rtcb_eligible and rtcb_signal IS NOT NULL, show adjusted recommendation
- stack.rtcb_eligible flag in response

### Dispatch recommendations — ERCOT RTC+B special case
```python
def get_dispatch_recommendation_deterministic(
    asset: dict, soc: float, prices: list[float], rtcb: float | None
) -> DispatchRecommendation:
    """
    ERCOT assets with rtcb_eligible=True and live rtcb_signal:
    Use rtcb_signal as primary price signal (more accurate than forecast).
    Set recommendation.rtcb_adjusted = True.
    """
    if asset["market"] == "ERCOT" and asset["rtcb_eligible"] and rtcb is not None:
        effective_price = rtcb  # RTC+B is the signal
        rationale = f"RTC+B signal ${rtcb:.2f}/MWh driving dispatch"
    else:
        effective_price = prices[0] if prices else 45.0
        rationale = f"Forecast price {asset['currency']}{effective_price:.2f}/MWh"
    ...
```

## SUCCESS CRITERIA
1. POST offer stack creates rows in Lakebase offer_stacks + offer_bands tables
2. POST offer stack also appears in Delta (Genie can query it within 60s)
3. NEM: non-ascending prices → HTTP 422 with per-band error
4. NEM: rebid without reason → HTTP 422
5. ERCOT: recommendations show rtcb_adjusted=True when RTC+B is live
6. ERCOT: recommendations show rtcb_adjusted=False for pre-Dec-2025 historical assets
7. Fleet status returns all 15 assets across NEM/EPEX/ERCOT filtered by ?market

## COMPLETION ARTIFACT
completions/W09-dispatch-api.md
Commit: "feat: W09 complete — dispatch and offer stack API"
