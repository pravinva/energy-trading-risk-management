# W16 — Quant Console
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W07-market-data-api.md exist.

---

## OBJECTIVE
Build the Quant Developer workspace. A research console where quants monitor ML price forecast model performance, run backtests of trading strategies against historical data, and analyse market signals. This is where the MLflow model governance story becomes real.

---

## BACKEND ADDITIONS for W16

### data/queries/analytics/

**model_performance.sql**
Forecast vs actual comparison for the price forecast model. Parameterised: :region_id, :horizon, :days (default 30). Returns: forecast_datetime, forecast_price, actual_price, error, abs_error, mape per interval. JOINs apex.analytics.price_forecasts with apex.market.nem_prices on interval_datetime and region_id.

**model_mape_by_condition.sql**
MAPE grouped by market condition (spike/normal/negative). Parameterised: :region_id, :days. Shows where the model is most/least accurate.

**backtest_runs.sql**
All backtest runs ordered by run_datetime DESC. Returns summary metrics.

**backtest_trades.sql**
Individual trades from a backtest run. Parameterised: :run_id.

### Backend route addition: app/backend/routes/analytics.py

GET /api/v1/analytics/model-performance — query: region_id, horizon, days int=30
GET /api/v1/analytics/model-mape-by-condition — query: region_id, days int=30
GET /api/v1/analytics/backtest/runs — list of backtest run summaries
GET /api/v1/analytics/backtest/{run_id} — detail of a specific run including trades
POST /api/v1/analytics/backtest/run — run a new backtest. Body: {strategy_name, region_id, start_date, end_date, parameters dict}

### BACKTEST RUNNER IMPLEMENTATION
POST /api/v1/analytics/backtest/run must actually run a strategy against historical data:

```python
async def run_backtest(
    strategy_name: str,
    region_id: str,
    start_date: date,
    end_date: date,
    parameters: dict
) -> BacktestResult:
    """
    Available strategies (parameter-driven):
    
    SIMPLE_THRESHOLD:
    - Buy when price < parameters['buy_threshold'] (e.g. $50/MWh)
    - Sell when price > parameters['sell_threshold'] (e.g. $120/MWh)
    - Volume: parameters['volume_mw']
    
    MOVING_AVERAGE_CROSSOVER:
    - Short MA period: parameters['short_window'] (e.g. 6 intervals = 30 min)
    - Long MA period: parameters['long_window'] (e.g. 24 intervals = 2 hr)
    - Buy on golden cross, sell on death cross
    
    FCAS_SPIKE_CAPTURE:
    - Enter FCAS when raise6sec price > parameters['fcas_threshold']
    - Exit after parameters['hold_intervals'] dispatch intervals
    
    1. Load historical prices from apex.market.nem_prices for date range
    2. Apply strategy logic interval by interval
    3. Record each simulated trade (entry price, exit price, P&L)
    4. Calculate: total P&L, Sharpe ratio, max drawdown, win rate, trade count
    5. Write to apex.analytics.backtest_runs and backtest_trades via Lakebase
    6. Return BacktestResult
    """
```

---

## PAGE: /quant/models — ModelPerformance.tsx

### ForecastVsActualChart
Recharts ComposedChart showing:
- Line: actual NEM prices (--color-text-primary)
- Line: model forecast (--color-persona-quant dashed)
- Area fill between them: --color-warning-dim where |error| > 20%
X-axis: time in --font-data --text-xs
Y-axis: $/MWh in --font-data --text-xs

Above chart: region selector (NEM4 regions + tabs) and horizon selector (5MIN/30MIN/4HR).

### ErrorMetricsPanel
Four Metrics:
- MAPE: percentage in --font-data — green < 10%, amber 10-15%, red > 15%
- MAE: $/MWh
- RMSE: $/MWh
- BIAS: positive (over-forecasting) or negative (under-forecasting)

### AccuracyByConditionTable
DataTable: MARKET CONDITION / INTERVAL COUNT / MAPE / BIAS
Rows: NORMAL ($0-$200) / HIGH ($200-$1000) / SPIKE (>$1000) / NEGATIVE (<$0)
This directly shows where the model is strongest and weakest.

### ModelMetadataPanel
Panel titled "MODEL REGISTRY — MLflow".
Shows: model_version, training_data_period, feature_count, algorithm (LightGBM), last_retrained datetime, production_alias.
A "VIEW IN MLFLOW" link button (--color-accent, no fill) that opens the MLflow experiment URL in a new tab.

---

## PAGE: /quant/backtest — BacktestConsole.tsx

### StrategyConfigurator
Left panel (280px). Configure and run backtests.

Strategy selector: radio group for SIMPLE_THRESHOLD / MOVING_AVERAGE_CROSSOVER / FCAS_SPIKE_CAPTURE.

Dynamic parameters form: shows relevant parameter inputs based on selected strategy.
- SIMPLE_THRESHOLD: Buy Threshold ($/MWh), Sell Threshold ($/MWh), Volume (MW)
- MOVING_AVERAGE: Short Window (intervals), Long Window (intervals), Volume (MW)
- FCAS_SPIKE: FCAS Threshold ($/MW/hr), Hold Intervals, Volume (MW)

Region selector, Start Date, End Date.

RUN BACKTEST button. Spinner while running (typical: 1-5 seconds). Shows estimated progress: "Simulating [N] intervals..."

### BacktestResults
Appears after successful run.

Performance metrics (4 Metrics):
- TOTAL P&L: large, pnl-positive or pnl-negative
- SHARPE RATIO: --font-data (>1 = good, amber 0-1, red < 0)
- MAX DRAWDOWN: pnl-negative always
- WIN RATE: percentage (green > 55%, amber 45-55%, red < 45%)

BacktestEquityCurve: Recharts AreaChart showing cumulative P&L over time. Fill: --color-bid-dim when positive, --color-offer-dim when negative. Inflection points visible.

TradesTable: DataTable of all simulated trades.
Columns: DATETIME / DIRECTION / VOLUME / ENTRY PRICE / EXIT PRICE / P&L / SIGNAL
P&L: pnl-positive or pnl-negative per trade.

### BacktestRunHistory (below)
DataTable of previous backtest runs.
Columns: RUN DATE / STRATEGY / REGION / PERIOD / TOTAL P&L / SHARPE / WIN RATE / TRADES

---

## PAGE: /quant/signals — SignalScanner.tsx

### PriceSignalHeatmap
A heatmap showing model confidence by hour of day × day of week. Each cell = average MAPE for that time slot. Colour scale: green (accurate) to red (inaccurate). Rendered as a 7×24 grid of CSS divs — no chart library needed.

### FeatureImportancePanel
Horizontal bar chart (Recharts BarChart) showing the most important features driving the price forecast. Mock data (feature names from the model): "previous_rrp_lag1", "demand_forecast", "solar_irradiance", "temperature", "hour_of_day", "day_of_week", "wind_generation", "interconnector_flow_vic_nsw". Bar length proportional to importance. Labels in --font-data --text-xs.

### VolatilityRegimePanel
Shows current market volatility regime: LOW/MEDIUM/HIGH/EXTREME based on rolling 24h price standard deviation. StatusBadge + a Metric showing the exact std dev value.

---

## HOOKS: app/frontend/src/api/hooks/analytics.ts
- useModelPerformance(regionId, horizon, days): staleTime: 300000
- useModelMAPEByCondition(regionId, days): staleTime: 300000
- useBacktestRuns: staleTime: 60000
- useBacktestDetail(runId): staleTime: 3600000
- runBacktest(request): POST mutation — invalidates useBacktestRuns on success

---

## SUCCESS CRITERIA
1. Forecast vs actual chart renders with two lines from real data
2. MAPE metric shows correct value (not always green — model accuracy varies)
3. Backtest runner executes SIMPLE_THRESHOLD strategy against historical data and returns results
4. Backtest P&L is calculated correctly (can be verified manually from trade list)
5. Backtest writes to Lakebase (verify in backtest_runs table)
6. Equity curve chart shows cumulative P&L progression
7. Run history table shows previous runs from seed data + new run
8. Sharpe ratio > 1 shown in green, < 0 in red
9. Vitest tests pass

---

## COMPLETION ARTIFACT
completions/W16-quant-console.md
Commit message: "feat: W16 complete — Quant Developer research console"

---
---

# W17 — Portfolio Dashboard
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W11-portfolio-api.md exist.

---

## OBJECTIVE
Build the Portfolio Manager workspace. Revenue stacking model with interactive parameter controls, PPA book with live MTM valuation, and asset benchmarking. The revenue stacking simulator is the key interactive element — portfolio managers change BESS parameters and see revenue impact in real time.

---

## PAGE: /portfolio/revenue — RevenueDashboard.tsx

### PortfolioSummaryMetrics
Four Metrics (top row):
- TOTAL FLEET ARR: sum of all asset annual revenue in --font-data --text-2xl pnl-positive
- REVENUE PER MW: fleet average in --font-data
- YTDAY REVENUE: current year actual to date in --font-data pnl-positive
- FORECAST ACCURACY: last 30-day forecast vs actual MAPE for revenue model

### RevenueStackingSimulator
The flagship portfolio tool. Two-column layout.

Left (300px): PARAMETERS panel
Asset selector: dropdown of all 8 BESS assets (or "ALL ASSETS" aggregate).
Parameter sliders (visual sliders using native HTML range input styled with CSS):
- DURATION: 1hr to 8hr. Default 2hr. Shows value in --font-data.
- FCAS PARTICIPATION: 0% to 100%. Default 40%.
- CAP CONTRACT MW: 0 to capacity_mw. Default 0.
- PPA CONTRACTED MW: 0 to capacity_mw. Default 0.

As the user moves a slider, the SIMULATE button highlights (--color-accent background). Do not auto-simulate on every slider move — wait for button press to avoid excessive API calls.

SIMULATE button. On click: POST /api/v1/portfolio/revenue-stack/simulate. Shows spinner. On return: updates the Results panel.

Right (flex): RESULTS panel
When results available:
- TOTAL ANNUAL REVENUE: large Metric in pnl-positive
- REVENUE PER MW: Metric
- STACKED BAR showing breakdown by component (Energy / FCAS / Cap / PPA):
  Recharts BarChart (horizontal single bar). Each segment a different shade:
  - Energy: --color-neutral
  - FCAS: --color-persona-dispatch
  - Cap: --color-warning
  - PPA: --color-persona-portfolio
- Assumption labels below: "Based on: avg TB4 spread $[X], avg FCAS [Y]$/MW/hr, cap premium $[Z]/MW/quarter"

### RevenueHistoryChart
Recharts BarChart showing monthly actual revenue for all 8 assets stacked.
12 months of data. Each bar stacked by asset. X-axis: month. Y-axis: $AUD.
Clicking a month bar highlights that month's breakdown in a tooltip showing per-asset revenue.

### RevenueForecastChart
Recharts ComposedChart showing:
- Area: confidence interval (low to high) in --color-neutral-dim
- Line: BASE scenario forecast in --color-neutral
- Dots: actual revenue (where available)
Filter: asset selector + scenario selector (BASE/HIGH/LOW).

---

## PAGE: /portfolio/ppa — PPABook.tsx

### PPABookHeader
Three Metrics:
- NET PPA POSITION: +MW long, -MW short in pnl colours
- TOTAL MTM VALUE: sum of all PPA MTM values
- IN-THE-MONEY COUNT: how many PPAs are ITM (above strike)

### PPABookTable
DataTable of all PPAs.
Columns: PPA NAME / COUNTERPARTY / DIRECTION / CONTRACTED MW / STRIKE $/MWh / MARKET PRICE / MTM VALUE / EXPIRY / STATUS

DIRECTION: "LONG" in --color-bid, "SHORT" in --color-offer.
MARKET PRICE: --font-data mono-price with price-up/price-down class.
MTM VALUE: large column — pnl-positive if ITM, pnl-negative if OTM. Show as "A$X,XXX,XXX".
MARK button per row: calls POST /api/v1/portfolio/ppa/{id}/mark. Shows spinner in cell. Updates MTM VALUE in the row immediately on response.

### PPAPayoffDiagram
For selected PPA: a Recharts LineChart showing the payoff structure.
X-axis: market price from $0 to $200/MWh.
Y-axis: P&L of the PPA at each price point.
- Long PPA: line has positive slope (profit as price rises above strike) — colour --color-bid
- Short PPA: line has negative slope — colour --color-offer
Vertical reference line at current market price in --color-neutral.
Horizontal reference line at 0 (breakeven) in --color-border-default.

---

## PAGE: /portfolio/assets — AssetBenchmarking.tsx

### BenchmarkingTable
DataTable of all 8 BESS assets ranked by revenue performance.
Columns: RANK / ASSET / REGION / CAPACITY MW / ANNUAL REVENUE / REV/MW/YR / BENCHMARK / VS BENCHMARK / PERCENTILE

RANK: 1-8 in --font-data (1 = highest revenue per MW).
VS BENCHMARK: shows +X% or -X% vs market benchmark. pnl-positive if above, pnl-negative if below.
PERCENTILE: badge showing "TOP 20%" or "BOTTOM 40%" etc.

### BenchmarkChart
Recharts ScatterChart. Each asset is a dot.
X-axis: capacity_mw.
Y-axis: revenue_per_mw_per_year.
Horizontal reference line at market benchmark average.
Dots above reference: --color-bid. Below: --color-offer.
Asset name labels next to each dot in --font-data --text-2xs.

### RegionalRevenueHeatmap
A 4×3 grid (4 NEM regions × 3 revenue components: energy, FCAS, other). CSS div grid. Colour intensity = relative revenue contribution. Labels in --label-caps. Values in --font-data --text-xs.

---

## HOOKS: app/frontend/src/api/hooks/portfolio.ts
- useRevenueActuals(assetId?, days?): staleTime: 3600000
- useRevenueForecast(assetId?, scenario?, months?): staleTime: 3600000
- useRevenueComponents(assetId?, months?): staleTime: 3600000
- usePPABook: refetchInterval: 120000
- markPPA(ppaId): POST mutation — invalidates usePPABook on success
- useAssetBenchmarking: staleTime: 3600000
- simulateRevenueStack(inputs): POST mutation — no cache invalidation (pure calculation)

---

## SUCCESS CRITERIA
1. Revenue simulator returns in < 500ms and shows breakdown components
2. Higher FCAS participation slider → higher FCAS revenue in results (monotonic)
3. Higher duration → higher energy revenue (monotonic up to a point)
4. PPA MARK button updates MTM in the table row
5. Long PPA payoff diagram has positive slope above strike price
6. Short PPA payoff diagram has negative slope above strike price
7. Benchmarking table shows correct rank (rank 1 = highest rev/MW)
8. All revenue amounts: Decimal precision with comma formatting
9. Vitest tests pass

---

## COMPLETION ARTIFACT
completions/W17-portfolio-dashboard.md
Commit message: "feat: W17 complete — Portfolio Manager dashboard"

---
---

# W18 — Integration & Deployment
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
ALL of these must exist before starting:
- completions/W13-dispatch-console.md
- completions/W14-trading-blotter.md
- completions/W15-risk-dashboard.md
- completions/W16-quant-console.md
- completions/W17-portfolio-dashboard.md

If any are missing, stop and report which are absent.

---

## OBJECTIVE
Deploy APEX to the fe-sandbox Databricks Apps workspace. Run full end-to-end integration tests across all five persona workspaces. Verify all critical trading workflows function correctly end-to-end.

---

## STEP 1: Frontend production build
cd app/frontend && npm ci && npm run build
Verify: app/backend/static/index.html exists.

## STEP 2: Validate DAB
databricks --profile fe-vm bundle validate --target dev
Must pass zero errors.

## STEP 3: Deploy
databricks --profile fe-vm bundle deploy --target dev
databricks --profile fe-vm apps deploy apex
Monitor until status: RUNNING. Get deployed URL.

## STEP 4: Smoke test all API routes
Using curl against deployed URL:
- GET [url]/api/v1/health/ → status:ok, lakebase_connected:true
- GET [url]/api/v1/market/nem/prices/current → 4 regions
- GET [url]/api/v1/trades/ → 50 trades from seed data
- GET [url]/api/v1/positions/ → positions with MTM P&L
- GET [url]/api/v1/dispatch/fleet → 8 BESS assets
- GET [url]/api/v1/risk/var → latest VaR result
- GET [url]/api/v1/portfolio/revenue/actuals → data for all assets
- GET [url]/ → index.html

## STEP 5: End-to-end workflow tests

### Test workflow 1: Complete trade entry
1. POST /api/v1/trades/ — enter BUY 100MW NSW1 @ $85/MWh
2. Verify trade appears in GET /api/v1/trades/
3. Verify position for NSW1 has increased by 100MW in GET /api/v1/positions/
4. Verify MTM P&L is calculated and non-null
5. PATCH /api/v1/trades/{id}/cancel — cancel the trade
6. Verify position reverts (or reduces) correctly

### Test workflow 2: Complete offer stack submission
1. GET /api/v1/dispatch/HORNSDALE_1/status — confirm SOC available
2. POST /api/v1/dispatch/HORNSDALE_1/offer-stack — submit 10-band energy stack
3. Verify stack_id returned
4. GET /api/v1/dispatch/HORNSDALE_1/offer-stack — verify stack retrieved
5. PATCH rebid endpoint — submit rebid with reason
6. Verify new stack created with is_rebid=TRUE

### Test workflow 3: VaR calculation
1. POST /api/v1/risk/var/calculate — trigger Monte Carlo
2. Verify returns in < 3 seconds
3. Verify VaR_99 > VaR_95 in response
4. Verify result written to Lakebase (GET /api/v1/risk/var returns the new result)

### Test workflow 4: Backtest execution
1. POST /api/v1/analytics/backtest/run — SIMPLE_THRESHOLD strategy, 30 days
2. Verify trades generated (backtest_trades count > 0)
3. Verify total P&L is sum of individual trade P&Ls

### Test workflow 5: Revenue simulation
1. POST /api/v1/portfolio/revenue-stack/simulate — duration=2hr, fcas=0.5
2. POST again with fcas=0.8 — verify fcas_revenue increases
3. POST with duration=4hr — verify energy_revenue increases

## STEP 6: Frontend E2E verification
Manual browser verification at each persona workspace:

DISPATCH persona:
- Fleet monitor shows 8 assets with real SOC
- Selecting an asset loads offer stack builder
- Band validation works (ascending price constraint)
- Submit stack and see ConfirmationToast

TRADER persona:
- Trade entry form submits successfully
- Position book updates with new trade
- MTM P&L shows correct sign (positive/negative per market vs trade price)
- Spike alert shows when test data has RRP > $1000

RISK persona:
- RUN VAR executes and shows histogram
- P&L histogram renders with 100 bars
- Stress test runs and shows P&L impact

QUANT persona:
- Forecast vs actual chart renders with two lines
- Backtest runs and returns equity curve
- At least one previous backtest run shows in history

PORTFOLIO persona:
- Revenue simulator returns breakdown
- PPA mark button updates MTM value
- Benchmarking table ranks all 8 assets

## STEP 7: Performance benchmarks
- POST /api/v1/trades/ : < 200ms
- GET /api/v1/positions/ : < 300ms
- POST /api/v1/risk/var/calculate : < 3s
- POST /api/v1/analytics/backtest/run : < 10s (acceptable for research tool)
- POST /api/v1/portfolio/revenue-stack/simulate : < 500ms

## STEP 8: Data portability verification
Re-run data/seeds/trades/00_run_all.sql against deployed workspace. Verify row counts match W05 documentation. Proves the app can be re-seeded in another workspace.

---

## FINAL SUCCESS CRITERIA

### Infrastructure
1. App RUNNING in fe-sandbox
2. All 5 persona workspaces accessible
3. Health endpoint: lakebase_connected:true

### Trading workflows (end-to-end):
4. Trade entry creates record in Lakebase and updates position (< 200ms)
5. Offer stack submission creates stack + 10 bands in Lakebase
6. Rebid compliance check returns is_compliant field
7. VaR calculation completes in < 3s with result in Lakebase
8. Backtest execution creates trades in backtest_trades table

### Frontend:
9. All 5 persona workspaces load with real data
10. Price flash animation visible on market data refresh
11. BUY green / SELL red convention correct throughout
12. All numbers monospace (JetBrains Mono verified in browser)
13. No emoji anywhere (verified by DOM inspection)
14. Zero console errors

### Code quality:
15. mypy --strict passes on all backend files
16. TypeScript strict: zero errors
17. All engine unit tests pass (pnl, var, position, dispatch)
18. All API integration tests pass
19. No inline SQL anywhere in Python route files
20. All financial calculations use Decimal — no float

---

## FINAL COMPLETION ARTIFACT
Create: completions/W18-deployment-complete.md

Must contain:
- Deployed app URL
- Date and time
- databricks apps get apex status output
- All workflow test outputs (Steps 5-5 above)
- Performance measurements for all endpoints
- Browser verification of each persona workspace
- Links to all 19 completion files (W00-W18)
- Known limitations or deviations

Final commit message: "chore: W18 complete — APEX ETRM deployed to fe-sandbox"

---

## MOVING APEX TO A NEW WORKSPACE
1. Clone apex-etrm repository
2. Run data/schema/01-06 SQL files in order
3. Run data/seeds/market/anz_backfill.py and anz_simulator.py (adapted from sourabhghose repo)
4. Run data/seeds/market/epex_backfill.py and ercot_backfill.py
5. Run data/seeds/reference/*.sql
6. Run data/seeds/trades/00_run_all.sql
7. Update databricks.yml workspace host
8. Configure Databricks Secrets
9. Run: databricks bundle deploy && databricks apps deploy apex
10. App operational in approximately 20 minutes
