# W06 — Backend Core
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W00-foundation.md AND completions/W02-database-schema.md exist.

---

## OBJECTIVE
Build the FastAPI core with four-tier serving, auth, and the calculation engines. The engines (pnl.py, var.py, position.py, dispatch.py) are pure Python modules — fully testable without database access. They are the analytical heart of APEX.

---

## FOUR-TIER SERVING
Identical to NEXUS P06 pattern from sourabhghose/databricks-energy-copilot:
1. Lakebase (psycopg3): 10-38ms primary
2. Dashboard snapshots table: <10ms pre-computed
3. SQL Warehouse (databricks-sql-connector): 400-1000ms fallback
4. In-memory TTL cache (cachetools): <1ms for repeated calls

---

## FILE: app/backend/config.py
pydantic-settings BaseSettings:
- databricks_host, lakebase_host, lakebase_database, lakebase_port: int = 5432
- sql_warehouse_id, apex_environment, app_version
- cache_ttl_market: int = 15 (market data — fast refresh)
- cache_ttl_positions: int = 5 (positions — very fast, P&L is live)
- cache_ttl_reference: int = 600 (reference data — slow change)
- var_simulation_count: int = 10000

## FILE: app/backend/database.py
Four-tier connection management. Identical structure to NEXUS P06 backend core.
Add: get_lakebase_db() context manager that AUTOMATICALLY writes position updates back to Lakebase after trade entry (not just reads).

## FILE: app/backend/auth.py
Same pattern as NEXUS. get_current_user_email(). is_databricks_employee().
APEX adds: get_trader_context(email) — looks up apex.reference.traders by email (using email as trader identifier in demo). Returns trader_id, name, desk, position_limit_mw, var_limit_aud.

## FILE: app/backend/engines/pnl.py
Pure Python P&L calculation engine. No FastAPI imports. No database access.
All prices use Python Decimal for financial precision.

```python
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

@dataclass
class Trade:
    trade_id: str
    direction: str  # BUY or SELL
    volume_mw: Decimal
    price: Decimal
    delivery_hours: Decimal  # derived from delivery_start to delivery_end

@dataclass
class MarketPrice:
    instrument_id: str
    current_price: Decimal

def calculate_mtm_pnl(trade: Trade, market_price: MarketPrice) -> Decimal:
    """
    Mark-to-market P&L for a single trade.
    BUY: (current_price - trade_price) × volume × hours
    SELL: (trade_price - current_price) × volume × hours
    """

def calculate_position_pnl(
    net_volume_mw: Decimal,
    avg_entry_price: Decimal,
    current_price: Decimal,
    delivery_hours: Decimal
) -> Decimal:
    """Aggregate position P&L."""

def calculate_realised_pnl(
    closed_trades: list[Trade],
    closing_price: Decimal
) -> Decimal:
    """Realised P&L for closed/settled trades."""

def aggregate_desk_pnl(
    positions: list[dict],
    market_prices: dict[str, Decimal]
) -> dict:
    """Returns: total_mtm, total_realised, by_instrument, by_region."""
```

Write unit tests for all functions. Test boundary cases: zero position, equal prices, large volumes, negative prices.

## FILE: app/backend/engines/var.py
Monte Carlo VaR engine. No FastAPI imports. No database access.

```python
import numpy as np
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class VaRInput:
    positions: list[dict]  # [{instrument_id, net_volume_mw, avg_price}]
    price_returns: dict[str, list[float]]  # historical daily returns per instrument
    simulation_count: int = 10000
    confidence_levels: list[float] = (0.95, 0.99)

@dataclass
class VaRResult:
    var_95: Decimal
    var_99: Decimal
    cvar_95: Decimal  # Expected Shortfall
    cvar_99: Decimal
    position_value: Decimal
    simulated_pnl_distribution: list[float]  # for histogram display

def run_monte_carlo_var(inputs: VaRInput) -> VaRResult:
    """
    1. Calculate historical volatility from price_returns per instrument
    2. Generate correlated random returns using Cholesky decomposition
    3. Apply shocked prices to current positions
    4. Calculate P&L distribution across simulations
    5. Extract VaR at confidence levels
    6. Calculate CVaR (expected shortfall beyond VaR)
    """

def run_stress_test(
    positions: list[dict],
    scenario: dict,  # price_shock_pct, demand_shock_pct, etc.
    current_prices: dict[str, float]
) -> dict:
    """Apply scenario shocks to positions and calculate P&L impact."""

def calculate_historical_returns(
    price_series: list[float],
    window_days: int = 252
) -> list[float]:
    """Calculate log returns from price history."""
```

Write unit tests: test with known distribution (normal), verify VaR at 95% is approximately 1.645 sigma, test stress test shock application, test CVaR > VaR always.

## FILE: app/backend/engines/position.py
Position aggregation engine. No FastAPI imports. No database access.

```python
from decimal import Decimal
from dataclasses import dataclass

def aggregate_positions(trades: list[dict]) -> list[dict]:
    """
    Aggregate raw trades into net positions by (instrument_id, region_id, trader_id, delivery_period).
    Returns net_volume_mw (positive=long, negative=short), avg_price, total_volume.
    """

def calculate_book_greeks(positions: list[dict], market_data: dict) -> dict:
    """Delta, DV01-equivalent for derivatives positions."""

def check_position_limits(
    positions: list[dict],
    limits: dict[str, float]  # trader_id -> position_limit_mw
) -> list[dict]:
    """Returns list of limit breaches with breach amount and utilisation %."""

def net_position_by_region(positions: list[dict]) -> dict:
    """Returns {region_id: net_mw} for all regions in the book."""
```

## FILE: app/backend/engines/dispatch.py
BESS dispatch recommendation engine. Integrates with MLflow model serving.

```python
from decimal import Decimal
from dataclasses import dataclass
from databricks.sdk import WorkspaceClient

@dataclass
class DispatchInput:
    asset_id: str
    current_soc_pct: float
    capacity_mw: float
    duration_hours: float
    forecast_prices: list[float]  # next N intervals
    fcas_prices: dict[str, list[float]]  # service_type -> prices
    market_region: str

@dataclass
class DispatchRecommendation:
    interval_datetime: str
    recommended_energy_mw: float  # positive=dispatch, negative=charge
    recommended_price: float  # offer price for energy band
    fcas_raise_mw: float
    fcas_lower_mw: float
    confidence_score: float
    expected_revenue: float
    rationale: str

def get_dispatch_recommendation(
    inputs: DispatchInput,
    model_serving_endpoint: str
) -> DispatchRecommendation:
    """
    1. Call MLflow model serving endpoint with input features
    2. Parse recommendation response
    3. Apply SOC constraints (cannot discharge below 10% or charge above 95%)
    4. Apply ramp rate constraints
    5. Return recommendation with rationale
    """

def build_offer_stack(
    recommendation: DispatchRecommendation,
    asset_capacity_mw: float
) -> list[dict]:
    """
    Convert recommendation to a 10-band offer stack.
    Distributes volume across bands with stepped price profile.
    """

def check_rebid_compliance(
    original_stack: list[dict],
    proposed_stack: list[dict],
    interval_datetime: str,
    reason: str
) -> dict:
    """
    NEL s.254 good faith rebidding check.
    Returns: is_compliant, warnings, required_disclosures.
    """
```

## FILE: app/backend/routes/__init__.py
Include all 8 routers: health, user, market, trades, positions, dispatch, risk, portfolio.

## FILE: app/backend/routes/health.py
GET /api/v1/health/ — checks Lakebase, SQL Warehouse, MLflow serving endpoint
GET /api/v1/health/lakebase, /health/warehouse, /health/ready

## FILE: app/backend/routes/user.py
GET /api/v1/user/me — UserContextResponse + trader context (desk, limits)
GET /api/v1/user/trader-context — returns full trader profile from apex.reference.traders

## FILE: app/backend/app.py
FastAPI with lifespan, four-tier init, routes, StaticFiles mount.

---

## TESTS: app/backend/tests/

### test_engines_pnl.py
- test_mtm_pnl_long_position_price_increase_is_positive
- test_mtm_pnl_long_position_price_decrease_is_negative
- test_mtm_pnl_short_position_price_increase_is_negative
- test_decimal_precision_no_floating_point_error
- test_zero_position_pnl_is_zero

### test_engines_var.py
- test_var_99_greater_than_var_95
- test_cvar_greater_than_var
- test_zero_position_var_is_zero
- test_monte_carlo_runs_10000_simulations
- test_stress_test_price_shock_applied_correctly

### test_engines_position.py
- test_buy_sell_same_instrument_nets_to_flat
- test_long_position_positive_net_volume
- test_limit_breach_detected_when_over_limit
- test_limit_utilisation_calculated_correctly

### test_engines_dispatch.py
- test_soc_constraint_prevents_overdischarge
- test_offer_stack_has_10_bands
- test_rebid_compliance_returns_is_compliant_flag
- test_build_offer_stack_sums_to_capacity

---

## SUCCESS CRITERIA
1. uvicorn starts without errors
2. GET /api/v1/health/ returns all components healthy
3. All engine unit tests pass (zero tolerance — no skipped tests)
4. pnl.py, var.py, position.py, dispatch.py have ZERO FastAPI or database imports
5. mypy --strict passes on all backend files
6. Decimal used for all price/P&L calculations — no float arithmetic

---

## COMPLETION ARTIFACT
completions/W06-backend-core.md
Commit message: "feat: W06 complete — APEX backend core with calculation engines"

---
---

# W07 — Market Data API
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W03-market-data-anz.md exist.

---

## OBJECTIVE
Implement market data API routes. These feed the live price displays, pre-dispatch panels, and forward curve views used by all five personas.

---

## SQL QUERIES: data/queries/market/

### nem_current_prices.sql
Latest RRP and FCAS prices per region (4 rows).

### nem_price_history.sql
Parameterised: :region_id (optional), :hours (default 24). Returns interval_datetime, rrp, fcas prices, demand.

### nem_predispatch.sql
Latest 12 pre-dispatch intervals (60 min of 5-min forecasts) per region. Parameterised: :region_id.

### nem_bess_telemetry_current.sql
Latest telemetry for all BESS assets or specific asset. Parameterised: :asset_id (optional).

### forward_curves.sql
Forward curve for an instrument or all NEM instruments. Parameterised: :instrument_id (optional), :region_id (optional).

### epex_current.sql
Latest EPEX day-ahead price per zone.

### ercot_lmp_current.sql
Latest ERCOT LMP per hub node. Includes rtcb_signal column.

### market_summary.sql
One row per market (NEM/EPEX/ERCOT) with: current average price, 24h change, volatility, market status (OPEN/CLOSED/AUCTION).

---

## ROUTES: app/backend/routes/market.py

Pydantic models:
- NEMPrice: interval_datetime, region_id, rrp, lower6sec, raise6sec, lowerreg, raisereg, totaldemand, change_vs_prev, is_spike: bool
- PreDispatchSignal: predispatch_datetime, run_datetime, region_id, forecast_rrp, forecast_demand, horizon_minutes: int
- BESSTelemetry: asset_id, recorded_at, state_of_charge_pct, output_mw, fcas_raise_mw, fcas_lower_mw, available_mw
- ForwardCurvePoint: instrument_id, tenor, price, bid, offer, volume
- EPEXPrice: bidding_zone, delivery_datetime, price_eur_mwh, mtu_minutes
- ERCOTPrice: node_id, interval_datetime, lmp, energy_component, congestion_component, rtcb_signal
- MarketSummary: market_id, avg_price, change_24h, volatility_24h, status

Routes (all four-tier serving, all return APIResponse[T]):
- GET /api/v1/market/nem/prices/current — list[NEMPrice], refetch every 15s
- GET /api/v1/market/nem/prices/history — query: region_id, hours int=24
- GET /api/v1/market/nem/predispatch — query: region_id. Returns 12 forward intervals.
- GET /api/v1/market/nem/bess/telemetry — query: asset_id optional. list[BESSTelemetry]
- GET /api/v1/market/forward-curves — query: instrument_id optional, region_id optional
- GET /api/v1/market/epex/current — list[EPEXPrice]
- GET /api/v1/market/ercot/current — list[ERCOTPrice]
- GET /api/v1/market/summary — list[MarketSummary] across all active markets

---

## TESTS: app/backend/tests/test_market_routes.py
- All 8 routes return 200
- NEM current prices returns 4 regions
- Pre-dispatch returns exactly 12 intervals
- ERCOT route includes rtcb_signal field
- Forward curves returns at least 20 rows
- Market summary covers NEM, EPEX, ERCOT

---

## SUCCESS CRITERIA
1. All routes 200 with real Lakebase data
2. Pre-dispatch signals update within 15s of market data simulator writing
3. No inline SQL
4. mypy passes
5. Tests pass

---

## COMPLETION ARTIFACT
completions/W07-market-data-api.md
Commit message: "feat: W07 complete — market data API routes"

---
---

# W08 — Trade Management API
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-trade-book-seeds.md exist.

---

## OBJECTIVE
Implement the trade management API. This is the core ETRM functionality — deal entry, trade book retrieval, position calculation with live P&L, and order management. This must work end-to-end: a user enters a trade through the API and it immediately writes to Lakebase, the position recalculates, and P&L updates.

---

## SQL QUERIES: data/queries/trades/

### trade_blotter.sql
Returns trades for a trader ordered by trade_timestamp DESC. Parameterised: :trader_id (optional), :status (optional), :days (default 30). Includes counterparty_name and instrument_name from JOINs.

### trade_detail.sql
Single trade with all fields plus related offer_stack_id if FCAS_OFFER type.

### position_book.sql
Current positions with live MTM P&L. JOINs positions table with current market prices from forward_curves. Parameterised: :trader_id (optional), :region_id (optional).

### pnl_summary.sql
Daily P&L summary. Parameterised: :trader_id, :days (default 30). Returns: date, realised, unrealised, total, trade_count, volume.

### pnl_attribution.sql
P&L broken down by region, instrument type, and trader. Used by risk manager portfolio view. Parameterised: :date (default today).

### open_orders.sql
All open orders for a trader. Parameterised: :trader_id.

---

## ROUTES: app/backend/routes/trades.py

Pydantic models:
- TradeEntry: instrument_id, counterparty_id, direction Literal['BUY','SELL'], volume_mw Decimal, price Decimal, delivery_start datetime, delivery_end datetime, trade_type, region_id optional, notes optional
- Trade: all TradeEntry fields + trade_id, trade_timestamp, status, settlement_status, trader_id, mtm_pnl Decimal
- Position: instrument_id, region_id, trader_id, delivery_period, net_volume_mw Decimal, avg_price Decimal, current_market_price Decimal, mtm_pnl Decimal, is_long bool
- PnLDay: date, realised_pnl Decimal, unrealised_pnl Decimal, total_pnl Decimal, trade_count int
- PnLAttribution: trader_id, region_id, instrument_type, pnl Decimal
- Order: order_id, instrument_id, direction, order_type, volume_mw Decimal, limit_price optional Decimal, filled_volume_mw Decimal, status, created_at
- OrderEntry: instrument_id, direction, order_type, volume_mw Decimal, limit_price optional Decimal, expires_at optional datetime

Routes:
- GET /api/v1/trades/ — trade blotter. query: trader_id optional, status optional, days int=30
- GET /api/v1/trades/{trade_id} — single trade detail
- POST /api/v1/trades/ — enter new trade. Body: TradeEntry. WRITES to Lakebase. Returns Trade with generated trade_id. After write: triggers position recalculation via position engine, updates MTM, returns immediately with new position.
- PATCH /api/v1/trades/{trade_id}/cancel — cancel a trade. Updates status to CANCELLED, recalculates positions.
- GET /api/v1/positions/ — position book with live MTM. query: trader_id optional, region_id optional
- GET /api/v1/positions/pnl-summary — query: trader_id optional, days int=30
- GET /api/v1/positions/pnl-attribution — query: date optional (default today)
- GET /api/v1/orders/ — open orders. query: trader_id optional
- POST /api/v1/orders/ — place new order. Body: OrderEntry.
- DELETE /api/v1/orders/{order_id} — cancel order.

### CRITICAL: POST /api/v1/trades/ implementation
This is the most important route in APEX. It must:
1. Validate TradeEntry against business rules:
   - volume_mw must be positive
   - price must be positive (except spot may be negative — allow negative spot prices)
   - delivery_end must be after delivery_start
   - counterparty_id must exist in apex.reference.counterparties
   - instrument_id must exist in apex.reference.instruments
2. Write to apex.trading.trades via Lakebase (psycopg3) — NOT via SQL Warehouse
3. Call position.aggregate_positions() to recalculate positions for affected instrument/trader/period
4. Upsert into apex.trading.positions (INSERT ... ON CONFLICT DO UPDATE)
5. Call pnl.calculate_position_pnl() with current market price
6. Update mtm_pnl in apex.trading.positions
7. Return the created trade + updated position in the response
8. Send a confirmation via response header X-Trade-Confirmed: true

The entire flow must complete in < 200ms on Lakebase. Use psycopg3 async context manager.

---

## TESTS: app/backend/tests/test_trade_routes.py
- test_post_trade_creates_record_in_lakebase
- test_post_trade_returns_trade_id
- test_post_trade_updates_position_immediately
- test_post_trade_calculates_mtm_pnl
- test_post_trade_invalid_counterparty_returns_422
- test_post_trade_volume_must_be_positive
- test_cancel_trade_updates_status
- test_position_book_shows_net_direction
- test_pnl_summary_returns_daily_breakdown
- test_post_order_creates_open_order
- test_delete_order_cancels_it

---

## SUCCESS CRITERIA
1. POST /api/v1/trades/ completes in < 200ms (measured)
2. Trade is written to Lakebase — verified with SELECT after POST
3. Position updates immediately — GET /positions/ after POST shows updated net_volume_mw
4. MTM P&L is calculated and non-null on all positions
5. Cancel endpoint correctly updates status
6. All Pydantic models use Decimal for financial values (no float)
7. mypy --strict passes
8. All tests pass

---

## COMPLETION ARTIFACT
completions/W08-trade-management-api.md
Commit message: "feat: W08 complete — trade management API with live position updates"

---
---

# W09 — Dispatch & Offer Stack API
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-trade-book-seeds.md exist.

---

## OBJECTIVE
Implement the dispatch and offer stack API. This is what the dispatch operator uses: viewing current SOC, getting ML dispatch recommendations, building and modifying offer stacks, submitting them, and checking rebid compliance. The ML dispatch recommendation must be a real call to an MLflow model serving endpoint (or a deterministic simulation of one if no endpoint is available).

---

## SQL QUERIES: data/queries/dispatch/

### asset_fleet_status.sql
Current status of all BESS assets: SOC, output MW, available MW, current offer stack status. One row per asset.

### offer_stack_current.sql
Current active offer stack for an asset and service type. Returns all 10 bands. Parameterised: :asset_id, :service_type.

### offer_stack_history.sql
Offer stack submissions for an asset over last N intervals. Parameterised: :asset_id, :days (default 7).

### dispatch_recommendations.sql
Latest dispatch recommendations for an asset. Parameterised: :asset_id, :limit (default 12 = next hour of 5-min intervals).

### predispatch_vs_actual.sql
Comparison of pre-dispatch forecast vs actual dispatch outcome for an asset. Used by quant for model evaluation. Parameterised: :asset_id, :days (default 7).

---

## ROUTES: app/backend/routes/dispatch.py

Pydantic models:
- AssetStatus: asset_id, asset_name, region_id, capacity_mw, duration_hours, current_soc_pct Decimal, current_output_mw Decimal, fcas_raise_mw Decimal, fcas_lower_mw Decimal, available_mw Decimal, current_stack_status str
- OfferBand: band_number int, price_per_mwh Decimal, volume_mw Decimal, dispatched_mw Decimal
- OfferStack: stack_id, asset_id, service_type, dispatch_interval datetime, status, bands list[OfferBand], total_mw Decimal, submitted_by optional str
- OfferStackDraft: asset_id, service_type str, dispatch_interval datetime, bands list[OfferBandInput]
- OfferBandInput: band_number int, price_per_mwh Decimal, volume_mw Decimal (both validated with Decimal)
- RebidRequest: stack_id, new_bands list[OfferBandInput], reason str (required for rebid)
- ComplianceCheck: is_compliant bool, warnings list[str], required_disclosures list[str], interval_datetime datetime
- DispatchRec: asset_id, dispatch_interval datetime, recommended_energy_mw Decimal, recommended_price Decimal, fcas_raise_mw Decimal, fcas_lower_mw Decimal, confidence_score Decimal, expected_revenue Decimal, rationale str, model_version str

Routes:
- GET /api/v1/dispatch/fleet — list[AssetStatus]. All BESS assets. refetch 30s.
- GET /api/v1/dispatch/{asset_id}/status — AssetStatus. refetch 15s.
- GET /api/v1/dispatch/{asset_id}/offer-stack — query: service_type str default 'ENERGY'. Current active stack.
- POST /api/v1/dispatch/{asset_id}/offer-stack — Submit new offer stack. Body: OfferStackDraft. WRITES to Lakebase (apex.trading.offer_stacks + offer_bands). Returns created OfferStack.
- PATCH /api/v1/dispatch/{asset_id}/offer-stack/{stack_id}/rebid — Submit a rebid. Body: RebidRequest. Validates rebid compliance first (MUST pass compliance check before writing). Creates new stack with is_rebid=TRUE and original_stack_id set.
- POST /api/v1/dispatch/{asset_id}/compliance-check — Body: RebidRequest. Returns ComplianceCheck WITHOUT submitting. Used to pre-validate before rebid.
- GET /api/v1/dispatch/{asset_id}/recommendations — list[DispatchRec]. Returns ML-generated dispatch recommendations for next N intervals.
- POST /api/v1/dispatch/{asset_id}/recommendations/accept/{recommendation_id} — Mark a recommendation as accepted. Creates corresponding offer stack automatically.
- GET /api/v1/dispatch/{asset_id}/stack-history — query: days int=7. Historical submissions.

### ML RECOMMENDATION IMPLEMENTATION
Try to call MLflow model serving endpoint from sourabhghose/databricks-energy-copilot (price forecast endpoint). If unavailable, use a deterministic simulation:

```python
def get_dispatch_recommendation_deterministic(
    asset: dict, current_soc: float, forecast_prices: list[float]
) -> DispatchRecommendation:
    """
    Rule-based simulation when ML endpoint unavailable:
    1. If price > 150 and SOC > 30%: recommend discharge at 90% capacity
    2. If price < 50 and SOC < 80%: recommend charge at 80% capacity
    3. If SOC < 15%: emergency charge regardless of price
    4. If SOC > 95%: emergency discharge regardless of price
    5. Calculate rationale string explaining the decision
    """
```

The route always returns the same DispatchRec schema whether from ML or deterministic — the model_version field distinguishes them.

### OFFER STACK VALIDATION
Before writing any offer stack to Lakebase:
1. Exactly 10 bands must be provided
2. Band numbers must be 1-10 with no gaps
3. Prices must be ascending (band 1 < band 2 < ... < band 10)
4. Each volume_mw must be positive
5. Sum of volumes must not exceed asset capacity_mw
6. Prices must be in range: -$1000 to $15,200 (AEMO market floor/cap)
7. Service type must be valid (ENERGY, FCAS_RAISE6SEC, etc.)

If any validation fails: return HTTP 422 with specific error messages per band.

### REBID COMPLIANCE
NEL s.254 good faith rebidding. The compliance_check engine must:
1. Verify reason string is non-empty (required by rule)
2. Verify the rebid is submitted before gate closure (simulated: > 5 minutes before dispatch interval)
3. Check if the new stack materially changes dispatch position (significant if > 50MW change in any band)
4. If material change: flag as requiring disclosure
5. Return is_compliant=True if no violations. Warnings are advisory only.

---

## TESTS: app/backend/tests/test_dispatch_routes.py
- test_fleet_status_returns_all_assets
- test_post_offer_stack_writes_10_bands_to_lakebase
- test_post_offer_stack_validates_ascending_prices
- test_post_offer_stack_rejects_volume_over_capacity
- test_rebid_requires_reason_string
- test_rebid_compliance_check_returns_is_compliant
- test_accept_recommendation_creates_offer_stack
- test_offer_stack_bands_sum_validation

---

## SUCCESS CRITERIA
1. POST offer stack writes to apex.trading.offer_stacks and apex.trading.offer_bands in Lakebase
2. Validation rejects non-ascending prices with HTTP 422
3. Rebid without reason returns 422
4. Compliance check returns is_compliant field
5. Recommendations endpoint returns data (ML or deterministic)
6. Accept recommendation creates corresponding offer stack
7. All Decimal — no float in financial fields
8. mypy passes
9. Tests pass

---

## COMPLETION ARTIFACT
completions/W09-dispatch-api.md
Commit message: "feat: W09 complete — dispatch and offer stack API"
