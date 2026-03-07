# APEX W15–W19: Risk Dashboard + Quant Console + Portfolio + Deployment + Genie

---

# W15 — Risk Dashboard

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W10-risk-api.md exist.

## PAGE: /{market}/risk/var — VaRDashboard.tsx

### VaR Header Metrics Row (4 cards)
```
[Portfolio VaR 95%]  [Portfolio VaR 99%]  [Position Value]  [Limit Utilisation]
  A$1.24M              A$2.07M              A$48.3M            67%
  ▲ +$84k today        67% of limit        ▲ +$2.1M MTM       ⚠ WARNING
```
- VaR amounts: pnl-negative always (VaR is a potential loss)
- Currency shown: A$ / € / $ per market from marketStore
- Limit Utilisation: StatusBadge — ACTIVE <70%, WARNING 70–90%, CRITICAL >90%

### VaR Runner Panel
Panel (market accent top border). Title: "RUN VAR CALCULATION"

Body:
- Description: "Monte Carlo · 10,000 paths · 1-day horizon · Historical volatility · [MARKET] portfolio"
- SCOPE radio: FULL PORTFOLIO / BY TRADER / BY REGION
- TRADER select: All Traders + individual trader names (market-filtered)
- "SIMULATIONS: 10,000" read-only display
- Progress indicator (shows "Fetching positions → Building returns matrix → Running simulations → Writing results")

RUN VAR button (accent background, white text, full width of panel).

State machine:
1. Idle: button enabled
2. Loading: button shows spinner "Running…", progress steps animate
3. Complete: metrics update, histogram renders, button re-enables
4. Error: error message in offer-dim background

### P&L Distribution Histogram

Recharts BarChart. 100 bars.
Colour mapping:
- Bars left of VaR_95 threshold: offer colour (red — tail risk)
- Bars between VaR_95 and VaR_99: warning colour (amber)
- Bars between VaR_99 and 0: offer-dim (pale red)
- Bars right of 0 (profits): bid-dim (pale green)

Reference lines:
- VaR_95: vertical dashed line in warning colour with label "VAR 95%: [CURRENCY][AMOUNT]"
- VaR_99: vertical dashed line in offer colour with label "VAR 99%: [CURRENCY][AMOUNT]"
- 0 line: thin line in border-default

X-axis: P&L in currency (A$M / €M / $M), font-data text-2xs
Y-axis: frequency count, font-data text-2xs

### VaR History Chart

Recharts LineChart. 30 days.
- VaR_99 line: persona-risk colour (amber)
- VaR_95 line: same colour dashed
- Horizontal reference line at limit value (var_limit from trading_limits)
- If VaR_99 crosses limit: area fill between line and limit in offer-dim
- X-axis: dates, text-2xs. Y-axis: currency amount.

Hook: useVaRHistory(market, traderId, 30), staleTime: 300000
Hook: calculateVaR(request) POST mutation, invalidates useVaRLatest on success

---

## PAGE: /{market}/risk/stress — StressTestPanel.tsx

### Scenario Cards

Grid of scenario cards filtered by current market (5 NEM / 3 EPEX / 2 ERCOT).

Each card:
- Scenario name in text-md text-primary
- Description in text-sm text-secondary
- Price shock badge: "+400%" in offer colour (red shock) or "−80%" in bid-dim (negative shock)
- Region/zone badge
- Reference event in text-2xs italic text-tertiary

RUN button per card. On click: spinner on that card + POST stress-test.

On return: card highlights (border goes to accent) and results section renders below.

### Stress Test Results Panel

Header: scenario name. Metrics row (4 cards):
- PORTFOLIO P&L IMPACT: large pnl-positive or pnl-negative
- WORST CASE: pnl-negative
- BEST CASE: pnl-positive
- POSITIONS BREACHED: integer, StatusBadge (active=0, warning=1–3, critical>3)

Impact chart: Recharts horizontal BarChart. One bar per trader showing their P&L impact.
Bars in pnl colours. X-axis: currency amount. Y-axis: trader names.

### Stress History Table
DataTable: RUN DATE / SCENARIO / MARKET / P&L IMPACT / BREACHES / RUN BY

---

## PAGE: /{market}/risk/limits — LimitMonitor.tsx

### Limits Table

Columns: TRADER / LIMIT TYPE / LIMIT VALUE / CURRENT / UTILISATION / STATUS

Utilisation: percentage + inline CSS bar (100px):
- Bar fill: bid colour <70%, warning 70–90%, offer >90%
- Number: same colour coding

Breach rows: background offer-dim, border-left 2px offer colour.

### Breach Alert Panel (conditional — top of page if any breach)

Full-width panel, background offer-dim, border offer.
"LIMIT BREACH DETECTED — [N] limits exceeded"
Per-breach row: "Trader [name] · [LIMIT_TYPE] · Current [value] · Limit [value] · Breach since [time]"
ACKNOWLEDGE button per breach (visual only — frontend state, no API call needed for demo).

---

## PAGE: /{market}/risk/credit — CreditExposure.tsx

Columns: COUNTERPARTY / COUNTRY / MTM / PFE / TOTAL EXPOSURE / CREDIT LIMIT / UTILISATION / STATUS

MTM: pnl-positive if positive (they owe us), pnl-negative if negative.
Utilisation inline bar. All amounts in market currency.

---

## SUCCESS CRITERIA
1. RUN VAR completes < 3s, metrics update, histogram renders
2. Histogram has exactly 100 bars, reference lines at VaR_95 and VaR_99
3. VaR_99 > VaR_95 always (verify in 5 consecutive runs)
4. History chart shows VaR trend and highlights limit crossing
5. All 5 NEM / 3 EPEX / 2 ERCOT scenarios render correctly per market
6. Running NEM_SA_SPIKE shows large negative P&L impact
7. Breach rows highlighted in offer-dim background
8. All currency labels correct per market (A$, €, $)

## COMPLETION ARTIFACT
completions/W15-risk-dashboard.md

---

# W16 — Quant Console

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W07-market-data-api.md exist.

## Backend additions required for W16

### app/backend/routes/analytics.py

```python
GET  /api/v1/analytics/model-performance    # ?market&region_id&horizon&days=30
GET  /api/v1/analytics/model-mape-condition # ?market&region_id&days=30
GET  /api/v1/analytics/backtest/runs        # ?market
GET  /api/v1/analytics/backtest/{run_id}    # detail + trades
POST /api/v1/analytics/backtest/run         # run backtest → Lakebase write
```

### Backtest runner — all 3 markets

```python
async def run_backtest(strategy_name: str, market: str, region_id: str,
                        start_date: date, end_date: date,
                        parameters: dict, run_by: str) -> BacktestResult:
    """
    SIMPLE_THRESHOLD strategy:
      NEM: buy when rrp < buy_threshold, sell when rrp > sell_threshold
      EPEX: buy when price_eur_mwh < threshold, sell when > sell_threshold
      ERCOT: buy when lmp < threshold, sell when > sell_threshold
               (if RTC+B live: use rtcb_signal as price signal)

    MOVING_AVERAGE_CROSSOVER:
      Buy on golden cross (short MA > long MA), sell on death cross
      Same price column per market as above

    FCAS_SPIKE_CAPTURE (NEM only):
      Enter raise6sec FCAS when price > fcas_threshold
      Exit after hold_intervals dispatch intervals

    Price column selection:
      NEM:   apex.market_nem.prices.rrp
      EPEX:  apex.market_epex.prices.price_eur_mwh
      ERCOT: apex.market_ercot.lmp.lmp (rtcb_signal if live and not null)

    1. Load historical prices from correct schema/table
    2. Apply strategy interval by interval
    3. Record trades (entry, exit, P&L)
    4. Calculate: total_pnl, sharpe_ratio, max_drawdown, win_rate
    5. Write run + trades to Lakebase
    6. Async sync to Delta for Genie
    7. Return BacktestResult
    """
```

---

## PAGE: /{market}/quant/models — ModelPerformance.tsx

### Region/Zone Selector (top)
NEM: QLD1 / NSW1 / VIC1 / SA1 / TAS1 tabs
EPEX: DE-LU / FR / BE / NL / ES tabs
ERCOT: West Hub / Houston Hub / North Hub / Panhandle W1 tabs

Horizon selector: 5MIN (NEM/ERCOT) | 30MIN | 4HR | DAY_AHEAD

### ForecastVsActualChart

Recharts ComposedChart:
- Line: actual prices (text-primary)
- Line: model forecast (persona-quant colour, dashed)
- Area fill between lines: warning-dim where |error| > 20% of actual

X-axis: datetime, font-data text-2xs
Y-axis: price in correct currency unit (A$/MWh, €/MWh, $/MWh)

For ERCOT: if region includes RTC+B data, show a third line:
- Line: rtcb_signal (neutral/blue colour, dotted) with legend "RTC+B Signal"
- This becomes a demo talking point: "The RTC+B signal is closer to actual than our day-ahead forecast"

### ErrorMetricsPanel (4 metrics)
- MAPE: green <10%, amber 10–15%, red >15%
- MAE: currency/MWh value
- RMSE: currency/MWh value
- BIAS: positive = over-forecasting, negative = under-forecasting

### AccuracyByConditionTable
Market-appropriate condition buckets:
- NEM:   NORMAL ($0–$200) / HIGH ($200–$1000) / SPIKE (>$1000) / NEGATIVE (<$0)
- EPEX:  NORMAL (€0–€100) / HIGH (€100–€200) / PEAK (>€200) / NEGATIVE (<€0)
- ERCOT: NORMAL ($0–$100) / HIGH ($100–$200) / SCARCITY (>$200) / NEGATIVE (<$0)

For ERCOT: add extra row: WITH_RTCB (intervals after Dec 2025) vs WITHOUT_RTCB — shows model improvement.

### ModelMetadataPanel
Panel. "MODEL REGISTRY — MLflow"
Shows: model_version, training_period, algorithm (LightGBM), last_retrained, production_alias.
Features by market:
- NEM: previous_rrp_lag1, demand_forecast, solar_irradiance, temperature, hour_of_day, interconnector_flow
- EPEX: previous_price_lag1, demand_forecast, wind_generation, solar_pv, gas_price, ets_price, temperature
- ERCOT: previous_lmp_lag1, demand_forecast, wind_capacity_factor, temperature, hour_of_day, rtcb_signal (post Dec 2025)

"VIEW IN MLFLOW" link button (accent border, no fill).

---

## PAGE: /{market}/quant/backtest — BacktestConsole.tsx

### StrategyConfigurator (left panel 264px)

Strategy radio: SIMPLE_THRESHOLD / MOVING_AVERAGE / FCAS_SPIKE_CAPTURE (last NEM-only, disabled for EPEX/ERCOT with tooltip "FCAS specific to NEM")

Dynamic parameters (show/hide per strategy):
- SIMPLE_THRESHOLD: Buy Threshold ([currency]/MWh), Sell Threshold, Volume (MW)
- MOVING_AVERAGE: Short Window (intervals), Long Window (intervals), Volume (MW)
- FCAS_SPIKE: FCAS Threshold ([currency]/MW/hr), Hold Intervals (int), Volume (MW)

Region/Zone selector (market-appropriate).
Start Date / End Date pickers.

RUN BACKTEST button (accent). Shows progress: "Loading [N] intervals… Simulating… Writing results…"

### BacktestResults (right panel — appears after run)

Metrics row (4):
- TOTAL P&L: large pnl-positive/negative, correct currency
- SHARPE RATIO: green >1, amber 0–1, red <0
- MAX DRAWDOWN: pnl-negative always
- WIN RATE: green >55%, amber 45–55%, red <45%

BacktestEquityCurve: Recharts AreaChart.
- Cumulative P&L over time
- Fill: bid-dim when positive, offer-dim when negative
- 0 reference line
- For ERCOT: vertical reference line at 2025-12-05 with label "RTC+B Live"
  Show P&L slope change before/after as a demo highlight

TradesTable: DataTable. DATETIME / DIRECTION / VOLUME / ENTRY / EXIT / P&L / SIGNAL
P&L per trade in correct currency with pnl colours.

### BacktestRunHistory (below results)
DataTable: RUN DATE / STRATEGY / MARKET / REGION / PERIOD / TOTAL P&L / SHARPE / WIN RATE

---

## PAGE: /{market}/quant/signals — SignalScanner.tsx

### PriceSignalHeatmap
7×24 CSS grid (day of week × hour of day).
Each cell = average MAPE for that time slot.
Colour: green (accurate, MAPE <5%) → amber → red (inaccurate, MAPE >20%).
Labels: day abbreviations (MON–SUN) and hour labels (00:00–23:00).
This shows WHEN the model struggles — a genuine analytical insight for quants.

### FeatureImportancePanel
Recharts horizontal BarChart. Market-appropriate features.
ERCOT post-Dec-2025: "rtcb_signal" appears in top 3 features — demo talking point.

### VolatilityRegimePanel
Current regime badge: LOW / MEDIUM / HIGH / EXTREME
Based on rolling 24h price standard deviation from live prices.
Metric: exact std dev value in currency/MWh.
Hook: uses latest 288 rows from current market's price table.

---

## SUCCESS CRITERIA
1. ForecastVsActual renders 2 lines from real data
2. ERCOT chart shows 3rd line for rtcb_signal after Dec 2025
3. Backtest runs SIMPLE_THRESHOLD and returns equity curve
4. ERCOT equity curve shows vertical reference line at 2025-12-05
5. Backtest writes to Lakebase + Delta (Genie queryable)
6. FCAS_SPIKE disabled for EPEX/ERCOT
7. AccuracyByCondition shows correct bucket thresholds per market
8. FeatureImportancePanel shows rtcb_signal in ERCOT features (post live date)

## COMPLETION ARTIFACT
completions/W16-quant-console.md

---

# W17 — Portfolio Dashboard

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W11-portfolio-api.md exist.

## PAGE: /{market}/portfolio/revenue — RevenueDashboard.tsx

### PortfolioSummaryMetrics (top row, 4 metrics)
- TOTAL FLEET ARR: sum of all asset annual revenue, pnl-positive, large font-data
- REVENUE PER MW: fleet average, correct currency
- YTD REVENUE: actuals to date
- FORECAST ACCURACY: MAPE of revenue model last 30 days

All amounts prefixed with correct currency symbol.

### RevenueStackingSimulator

Two-column layout.

**Left (280px): PARAMETERS panel** (Panel with portfolio accent border)

Asset selector: current market assets only.

Parameter sliders (native HTML range with CSS styling — no library):
- DURATION: 1hr–8hr. Default per asset type. Value displayed in font-data.
- FCAS PARTICIPATION: 0%–100%. (Label: "FCAS %" for NEM, "RESERVE %" for EPEX, hidden for ERCOT)
- CAP CONTRACT MW: 0–capacity_mw. (Hidden for ERCOT — no cap contract market)
- PPA CONTRACTED MW: 0–capacity_mw
- ERCOT ONLY: RTC+B PARTICIPATION: 0%–100% (visible only for ERCOT assets, disabled if rtcb_eligible=FALSE)

SIMULATE button: accent background when any slider moved. POST simulate on click.

**Right (flex): RESULTS panel**

TOTAL ANNUAL REVENUE: large Metric in pnl-positive.
REVENUE PER MW: Metric.

Component stacked bar (Recharts single horizontal bar, segmented):
- Energy:  neutral colour (#60A5FA)
- FCAS/Reserve: persona-dispatch colour (#60A5FA)
- Cap (NEM only): warning colour (#FBBF24)
- PPA:     persona-portfolio colour (#34D399)
- RTC+B (ERCOT post-Dec-2025): accent colour (#FF6B6B) — only visible if rtcb_participation > 0

Assumption labels: "Based on avg spread [N] [currency]/MWh, avg FCAS [N] [currency]/MW/hr..."

For ERCOT simulator results post-Dec-2025: show a before/after comparison:
"With RTC+B: [X] · Without RTC+B: [Y] · Delta: +[Z]"

### RevenueHistoryChart

Recharts BarChart. 12 months stacked by asset. Current market assets only.
X-axis: months. Y-axis: currency amount.

For ERCOT: vertical reference line at Dec 2025 with label "RTC+B Live".
Bars after Dec 2025 should be visibly taller (rtcb_revenue component added).

### RevenueForecastChart

Recharts ComposedChart:
- Area: confidence band (neutral-dim fill)
- Line: BASE forecast (neutral)
- Dots: actual revenue where available

Scenario selector tabs: BASE / HIGH / LOW
Asset filter dropdown.

---

## PAGE: /{market}/portfolio/ppa — PPABook.tsx

### PPABookHeader (3 metrics)
- NET PPA POSITION: total contracted MW, sign-aware, pnl colours
- TOTAL MTM VALUE: sum of mtm_value in market currency
- IN THE MONEY: count of PPAs where current_mark > strike (with percentage badge)

### PPABookTable

Columns: NAME / COUNTERPARTY / DIR / MW / STRIKE | MARKET PRICE | MTM VALUE | EXPIRY / STATUS

DIRECTION: "LONG" bid colour, "SHORT" offer colour.
MARKET PRICE: font-data mono-price, price-up/down class.
MTM VALUE: pnl-positive if ITM (positive mtm for long, negative market minus strike), pnl-negative if OTM. Currency symbol prefix.

MARK button per row: POST mark endpoint → spinner in cell → updates MTM VALUE immediately on response.

### PPAPayoffDiagram

For selected PPA. Recharts LineChart.
X-axis: market price from 0 to 150% of strike
Y-axis: P&L of PPA
- LONG PPA: positive slope above strike (profit when market > strike) — bid colour
- SHORT PPA: negative slope above strike (loss when market > strike) — offer colour
Vertical line at current_mark — neutral colour "CURRENT"
Horizontal line at 0 — border-default "BREAKEVEN"
Filled area: bid-dim for ITM region, offer-dim for OTM region.

---

## PAGE: /{market}/portfolio/assets — AssetBenchmarking.tsx

### BenchmarkingTable

Columns: RANK / ASSET / REGION | NODE / CAPACITY MW / ANNUAL REV / REV/MW/YR / BENCHMARK / VS BENCH / PERCENTILE

RANK: font-data. 1 = highest revenue per MW.
VS BENCHMARK: "+12%" in pnl-positive or "−8%" in pnl-negative.
Inline bar for revenue vs benchmark (100px, CSS).

ERCOT note: below table, "Revenue includes RTC+B dispatch premium from Dec 2025. Pre/post comparison available in Quant Console."

### BenchmarkChart

Recharts ScatterChart. Each asset = dot.
X-axis: capacity_mw. Y-axis: revenue_per_mw_per_year.
Horizontal reference line at market benchmark average.
Dots above: bid colour. Below: offer colour.
Dot labels: asset name in font-data text-2xs.

### RegionalRevenueHeatmap

CSS grid:
- NEM: 5 regions × 4 components (energy, FCAS raise, FCAS lower, cap)
- EPEX: 5 zones × 3 components (energy, reserve, arbitrage)
- ERCOT: 4 hubs × 3 components (energy, ancillary, rtcb — latter empty pre-Dec-2025)

Colour intensity = relative revenue contribution.

---

## SUCCESS CRITERIA
1. Revenue simulator returns < 500ms for all markets
2. ERCOT simulator shows rtcb_revenue = 0 pre-Dec-2025, non-zero post
3. ERCOT RevenueHistoryChart shows visible uplift after Dec-2025 reference line
4. PPA payoff diagram: LONG has positive slope above strike
5. PPA MARK button updates MTM in real-time (no full page reload)
6. Asset benchmarking rank = 1 is highest rev/MW
7. All currencies correct per market (A$, €, $)

## COMPLETION ARTIFACT
completions/W17-portfolio-dashboard.md

---

# W18 — Integration & Deployment

## PREREQUISITE CHECK
All of these must exist: W13 through W17 completion files.

## STEP 1: Frontend build
```bash
cd app/frontend && npm ci && npm run build
# Verify: app/backend/static/index.html exists
```

## STEP 2: Validate DAB
```bash
databricks --profile fe-vm bundle validate --target dev
# Must pass zero errors
```

## STEP 3: Deploy
```bash
databricks --profile fe-vm bundle deploy --target dev
databricks --profile fe-vm apps deploy apex
# Monitor until status: RUNNING. Record URL.
```

## STEP 4: Start simulator job
```bash
databricks --profile fe-vm jobs run-now --job-name apex-market-simulator
# Verify all 3 threads running in job run logs
```

## STEP 5: Activate DLT pipeline
```bash
databricks --profile fe-vm pipelines start --pipeline-name apex-etrm-ingestion
# Verify: RUNNING status, no quarantined records
```

## STEP 6: API smoke tests (curl)
```bash
curl [url]/api/v1/health/
# Expected: {"lakebase_connected":true,"warehouse_connected":true,"simulator_running":true}

curl [url]/api/v1/market/nem/prices/current
# Expected: 5 rows with recent interval_datetime

curl [url]/api/v1/market/ercot/lmp/current
# Expected: 10 nodes, rtcb_signal populated (post Dec 2025)

curl [url]/api/v1/positions/?market=NEM
# Expected: positions with non-null mtm_pnl and source_system=ALIGNE_SIM

curl [url]/api/v1/dispatch/fleet?market=ERCOT
# Expected: 4 ERCOT assets with state_of_charge_pct

curl [url]/api/v1/risk/var?market=NEM
# Expected: var_95, var_99 with currency=AUD

curl [url]/api/v1/positions/source-lag
# Expected: 3 rows (NEM/EPEX/ERCOT) with lag_seconds < 300
```

## STEP 7: End-to-end workflow tests

### Workflow 1: Live price updates visible
1. Open /nem/trader/analytics in browser
2. Watch Panel A price strip for 30s
3. Prices must flash and update — verify price_flash animation fires
4. Open /ercot/trader/analytics — verify RTC+B signal visible in ERCOT ticker

### Workflow 2: Position MTM live update
1. Note MTM P&L value at T=0
2. Wait 30s (NEM simulator tick)
3. MTM P&L must change (market prices changed)

### Workflow 3: Offer stack submission
1. Navigate to /nem/dispatch/console
2. Select HORNSDALE_1
3. Build 10-band ENERGY stack with valid ascending prices
4. Click SUBMIT STACK
5. Verify ConfirmationToast appears
6. GET /api/v1/dispatch/HORNSDALE_1/offer-stack → stack returned
7. Verify rows in Lakebase: SELECT * FROM offer_stacks WHERE asset_id='HORNSDALE_1'
8. Verify rows in Delta within 60s (Genie query: "what offer stacks were submitted for Hornsdale 1?")

### Workflow 4: VaR calculation
1. Navigate to /nem/risk/var
2. Click RUN VAR
3. Progress steps animate, completes < 3s
4. Histogram renders with 100 bars
5. VaR_99 > VaR_95 in displayed metrics
6. History chart updates with new data point
7. Verify in Delta: SELECT * FROM apex.risk.var_results ORDER BY calculation_datetime DESC LIMIT 1

### Workflow 5: Multi-market navigation
1. Navigate to / → Market Selector
2. Click EPEX → EPEX Persona Selector (purple accent)
3. Click TRADER → Trading Analytics with EPEX zones in ticker
4. Click RISK → VaR Dashboard shows EUR currency
5. RUN VAR → results in EUR
6. Navigate back to / → Click ERCOT → ERCOT workspace
7. Navigate to Dispatch Console — verify "RTC+B ACTIVE" banner present (post Dec 2025)

### Workflow 6: Backtest with ERCOT RTC+B story
1. Navigate to /ercot/quant/backtest
2. Select SIMPLE_THRESHOLD, West Hub, date range spanning Dec 2025 boundary
3. RUN BACKTEST
4. Equity curve renders with vertical reference line at 2025-12-05
5. P&L slope visibly changes after RTC+B go-live (signal quality improves)

### Workflow 7: Genie integration
1. Navigate to any workspace, click "Ask Genie" panel toggle
2. Click pre-built question: "What is our net position in NSW1?"
3. Genie returns correct answer from apex.trading.gold_positions
4. Type freeform: "Show me all BESS assets with SOC below 30%"
5. Genie queries apex.market_nem.bess_telemetry — returns current data

## STEP 8: Performance benchmarks (measure all)
```
GET /api/v1/market/nem/prices/current    < 300ms
GET /api/v1/positions/?market=NEM        < 400ms
POST /api/v1/risk/var/calculate          < 3s
POST /api/v1/dispatch/{id}/offer-stack   < 200ms
POST /api/v1/analytics/backtest/run      < 10s
POST /api/v1/portfolio/revenue-stack/simulate < 500ms
```

## STEP 9: Data portability
Re-run data/seeds/trades/00_run_all.py against deployed workspace.
Verify row counts match W05 documentation.
Proves app can be deployed to any customer workspace in ~20 minutes.

## FINAL SUCCESS CRITERIA

Infrastructure:
1. App RUNNING in fe-sandbox
2. Simulator job RUNNING (all 3 threads alive)
3. DLT pipeline RUNNING continuously
4. All 3 Genie spaces configured

Live data:
5. NEM prices update every 30s (visible in browser without refresh)
6. ERCOT LMP updates every 30s with rtcb_signal populated
7. BESS SOC changes over time (verify over 5 minutes)
8. Position MTM P&L changes as market prices change

Workflows:
9. Offer stack submit → Lakebase → Delta → Genie queryable (end-to-end)
10. VaR calculation → < 3s → result in Lakebase + Delta
11. Backtest execution → creates trades in backtest_trades table

Frontend:
12. Market Selector → NEM/EPEX/ERCOT persona selectors all functional
13. Price flash animation visible on market data refresh
14. Market accent colours correct (NEM blue, EPEX purple, ERCOT amber)
15. Source provenance bar shows correct ETRM source per market
16. All numbers in JetBrains Mono (verify computed styles)
17. No emoji anywhere (DOM inspection)
18. Background is #1B1F23 (NOT black) — verify computed body background

Code quality:
19. mypy --strict passes on all backend
20. TypeScript strict: zero errors
21. All engine unit tests pass (pnl, var, position, dispatch)
22. No inline SQL in Python routes

## COMPLETION ARTIFACT
completions/W18-deployment.md
Commit: "chore: W18 complete — APEX deployed to fe-sandbox"

---

# W19 — Genie Integration

## PREREQUISITE CHECK
Verify completions/W18-deployment.md exists.

## OBJECTIVE
Configure three Genie spaces (one per market) with pre-built question sets per persona. Embed Genie into the APEX frontend via the GenieSidePanel component. This is the NL analytics layer that no standalone ETRM provides.

## STEP 1: Create Genie spaces in workspace

Create via Databricks UI or API:
- **apex-genie-nem**: tables = apex.market_nem.*, apex.trading.* (market=NEM filter), apex.risk.* (NEM), apex.portfolio.* (NEM)
- **apex-genie-epex**: tables = apex.market_epex.*, apex.trading.* (market=EPEX), apex.risk.* (EPEX)
- **apex-genie-ercot**: tables = apex.market_ercot.*, apex.trading.* (market=ERCOT), apex.risk.* (ERCOT)

Record the Genie space IDs for each — used in frontend config.

## STEP 2: Seed pre-built questions

Run data/seeds/genie/seed_genie_questions.py — inserts into apex.genie.questions and configures each Genie space.

### NEM questions by persona

```sql
-- Risk Manager
('NEM','risk','What is our current net position in SA1 for Q1 2026?',      'Exposure',1),
('NEM','risk','Which trader has the highest VaR utilisation today?',        'Risk',2),
('NEM','risk','Show positions that would breach limits if SA1 spikes 200%', 'Stress',3),
('NEM','risk','What was our P&L during the August 2025 NEM spike?',         'History',4),
('NEM','risk','Which counterparties are above 80% credit utilisation?',     'Credit',5),

-- Power Trader
('NEM','trader','What is our aggregate long exposure across all NEM regions?',         'Exposure',1),
('NEM','trader','Show me trades ingested from Aligne in the last 24 hours',            'Ingestion',2),
('NEM','trader','Compare our NSW1 position against the Cal-2027 forward curve',        'Analytics',3),
('NEM','trader','Which positions have the largest unrealised P&L today?',              'P&L',4),
('NEM','trader','How many trades arrived from ALIGNE_SIM this week?',                 'Ingestion',5),

-- Dispatch Operator
('NEM','dispatch','What is the current SOC of all BESS assets above 70%?',            'Fleet',1),
('NEM','dispatch','Show the last 5 offer stacks submitted for Hornsdale 1',            'History',2),
('NEM','dispatch','When was the last time SA1 price exceeded $5000?',                 'Market',3),
('NEM','dispatch','Which BESS asset discharged the most in the last hour?',           'Dispatch',4),
('NEM','dispatch','Show me all offer stacks submitted today across all assets',        'Operations',5),

-- Quant Developer
('NEM','quant','What is the MAPE of the NSW1 5-minute price forecast this week?',     'Performance',1),
('NEM','quant','Show me the 10 intervals with the largest forecast error in QLD1',     'Analysis',2),
('NEM','quant','Compare backtest P&L for SIMPLE_THRESHOLD vs MOVING_AVERAGE in NSW1', 'Backtest',3),
('NEM','quant','What was the average raise6sec FCAS price during spike events?',       'Market',4),
('NEM','quant','Which hour of day has the worst model accuracy in SA1?',               'Performance',5),

-- Portfolio Manager
('NEM','portfolio','Which BESS asset generated the most FCAS revenue last quarter?',  'Revenue',1),
('NEM','portfolio','What is the total MTM value of our NEM PPA book?',                'PPA',2),
('NEM','portfolio','Show revenue per MW for each asset ranked best to worst',          'Benchmarking',3),
('NEM','portfolio','How much cap contract revenue did we earn in the last 90 days?',  'Revenue',4),
('NEM','portfolio','Which PPA is most in-the-money at current forward prices?',       'PPA',5);
```

### EPEX questions by persona (key questions)
```sql
('EPEX','risk','What is our net exposure in DE-LU for the next 3 delivery months?','Exposure',1),
('EPEX','risk','Show all positions where MTM loss exceeds €100,000','Risk',2),
('EPEX','risk','How has our P&L changed since the MTU changed to 15 minutes in Sep 2025?','Market',3),
('EPEX','trader','Which EPEX zone had the most negative price hours last month?','Market',1),
('EPEX','trader','Show me all trades ingested from Endur in the last 7 days','Ingestion',2),
('EPEX','dispatch','Which EPEX BESS asset has the highest current SOC?','Fleet',1),
('EPEX','portfolio','What is the revenue per MW for our European BESS fleet?','Revenue',1);
```

### ERCOT questions by persona (key questions — RTC+B is the story)
```sql
('ERCOT','risk','Show all Panhandle nodes with negative congestion component today','Exposure',1),
('ERCOT','risk','What was our P&L before vs after RTC+B went live in December 2025?','History',2),
('ERCOT','trader','Which dispatch interval had the highest LMP at West Hub this week?','Market',1),
('ERCOT','trader','Show all trades ingested from Triple Point in the last 24 hours','Ingestion',2),
('ERCOT','dispatch','Show BESS assets with SOC below 20% in the ERCOT fleet','Fleet',1),
('ERCOT','dispatch','What is the current RTC+B signal vs day-ahead price for West Hub?','RTC+B',2),
('ERCOT','dispatch','Show offer stacks submitted for TX_WEST_1 today','History',3),
('ERCOT','quant','Does the backtest perform better using RTC+B vs day-ahead LMP as signal?','Backtest',1),
('ERCOT','quant','What is the forecast MAPE for West Hub before and after Dec 2025?','Performance',2),
('ERCOT','portfolio','Show the RTC+B revenue contribution for each ERCOT BESS asset','Revenue',1),
('ERCOT','portfolio','Compare monthly revenue for TX_WEST_1 before and after RTC+B','Revenue',2);
```

## STEP 3: Configure GenieSidePanel in frontend

### src/config/genie-questions.ts
```typescript
export type Market = 'NEM' | 'EPEX' | 'ERCOT';
export type Persona = 'dispatch' | 'trader' | 'risk' | 'quant' | 'portfolio';

export const GENIE_SPACE_IDS: Record<Market, string> = {
  NEM:   '[NEM_SPACE_ID_FROM_WORKSPACE]',
  EPEX:  '[EPEX_SPACE_ID_FROM_WORKSPACE]',
  ERCOT: '[ERCOT_SPACE_ID_FROM_WORKSPACE]',
};

// Loaded dynamically from apex.genie.questions via GET /api/v1/genie/questions
// Fallback to hardcoded for offline demo
export const GENIE_QUESTIONS_FALLBACK: Record<Market, Record<Persona, string[]>> = {
  NEM: {
    risk:      ['What is our net position in SA1 for Q1 2026?', ...],
    trader:    ['Show aggregate long exposure across all NEM regions', ...],
    dispatch:  ['What is the SOC of all BESS assets above 70%?', ...],
    quant:     ['What is the MAPE of the NSW1 5-minute forecast this week?', ...],
    portfolio: ['Which BESS asset generated the most FCAS revenue last quarter?', ...]
  },
  EPEX: { ... },
  ERCOT: { ... }
};
```

### GenieSidePanel.tsx (from W01) — wire up

```typescript
interface GenieSidePanelProps {
  market: Market;
  persona: Persona;
}

export const GenieSidePanel: React.FC<GenieSidePanelProps> = ({ market, persona }) => {
  const [isOpen, setIsOpen] = useState(false);
  const spaceId = GENIE_SPACE_IDS[market];
  const questions = useGenieQuestions(market, persona);  // from API or fallback

  return (
    <div className={`genie-panel ${isOpen ? 'open' : 'closed'}`}>
      {/* Toggle tab — always visible */}
      <button className="genie-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span className="label-caps" style={{writingMode:'vertical-rl'}}>Ask Genie</span>
      </button>

      {isOpen && (
        <div className="genie-content">
          <div className="genie-header">
            <span className="label-caps">Genie — {market}</span>
            <a href={`/genie/${spaceId}`} target="_blank" className="genie-external">
              Open full Genie ↗
            </a>
          </div>

          {/* Pre-built question chips */}
          <div className="genie-questions">
            <span className="label-caps text-tertiary">Suggested questions</span>
            {questions.map((q, i) => (
              <button key={i} className="genie-chip"
                      onClick={() => submitGenieQuestion(q, spaceId)}>
                {q}
              </button>
            ))}
          </div>

          {/* Genie iframe */}
          <iframe
            src={`/genie/embed/${spaceId}`}
            className="genie-iframe"
            title={`Genie — ${market}`}
          />
        </div>
      )}
    </div>
  );
};
```

### Add Genie toggle button to WorkspaceLayout.tsx topbar (right side)
```typescript
<button className="genie-topbar-btn" onClick={toggleGenie}>
  <span className="label-caps" style={{color: 'var(--color-accent)'}}>Ask Genie</span>
</button>
```

### Add backend route: GET /api/v1/genie/questions
Returns questions from apex.genie.questions filtered by ?market&persona.
Also returns Genie space URL for the market.

---

## STEP 4: Verify Genie answers using seeded data

For each market, verify these specific questions return sensible answers:

**NEM:**
- "What is our net position in SA1?" → Should return net_volume_mw from gold_positions for SA1 region
- "Show me all BESS assets with SOC below 30%" → Should query market_nem.bess_telemetry, return subset

**EPEX:**
- "Which zone had the most negative price hours last month?" → DE-LU or ES based on simulator
- "How many trades arrived from Endur this week?" → Count from trading.trades where source_system='ENDUR_SIM'

**ERCOT:**
- "What was our P&L before vs after RTC+B went live?" → Genie queries pnl_daily, compares periods
- "What is the current RTC+B signal for West Hub?" → Queries market_ercot.lmp, latest rtcb_signal

---

## ADD route to backend: GET /api/v1/genie/questions
```python
@router.get("/genie/questions")
async def get_genie_questions(market: str, persona: str) -> list[GenieQuestion]:
    return await query_warehouse(
        GENIE_QUESTIONS_SQL,
        {"market": market, "persona": persona}
    )
```

## SUCCESS CRITERIA
1. Three Genie spaces created and visible in Databricks workspace
2. apex.genie.questions has minimum 5 questions per persona per market (75 total)
3. GenieSidePanel opens/closes in every persona workspace
4. Pre-built question chips render filtered to current market + persona
5. NEM Genie: "net position in SA1" returns data from gold_positions (post-DLT)
6. ERCOT Genie: "P&L before vs after RTC+B" returns a meaningful comparison
7. ERCOT Genie: "current RTC+B signal" returns non-null value (post Dec 2025)
8. EPEX Genie: answers correctly in €/MWh (not AUD or USD)
9. "Open full Genie" link navigates to workspace Genie UI

## COMPLETION ARTIFACT
completions/W19-genie.md
Commit: "feat: W19 complete — Genie integration, 3 markets, 5 personas"

---

# COMPLETE WORKSTREAM EXECUTION ORDER

```
W00   Project Foundation
W01   Design System (Option D — Slate + Coral)
W02   Database Schema (multi-market, 9 schemas)
W02b  ETRM Ingestion DLT Pipeline (bronze→silver→gold)
W03   Continuous Market Simulators (NEM + EPEX + ERCOT + Orchestrator)
W05   Trade Book Seeds (via raw_etrm_trades → DLT)
W06   Backend Core (engines + four-tier serving)
W07   Market Data API (all 3 markets)
W08   Trade Analytics API (read-only, source provenance)
W09   Dispatch & Offer Stack API (Lakebase writes + Delta sync)
W10   Risk Engine API (VaR + stress tests, Lakebase writes + Delta sync)
W11   Portfolio API (revenue stacking simulator, PPA marking)
W12   Frontend Shell (Market Selector → Persona → Workspace)
W13   Dispatch Console (SOC, offer builder, RTC+B ERCOT, NEM rebid)
W14   Trading Analytics (exposure heatmap, source provenance, live MTM)
W15   Risk Dashboard (VaR runner, histogram, stress scenarios)
W16   Quant Console (backtesting, ERCOT RTC+B equity curve)
W17   Portfolio Dashboard (revenue stacking, PPA payoff, benchmarking)
W18   Integration & Deployment (deploy, all workflow tests)
W19   Genie Integration (3 spaces, pre-built questions, frontend embed)
```

# LAKEBASE vs DELTA OWNERSHIP

| Data | Lakebase | Delta (Genie queryable) |
|---|---|---|
| VaR results | Primary write | Async sync after write |
| Offer stacks + bands | Primary write | Async sync after write |
| Backtest runs | Primary write | Async sync after write |
| Trades | NOT stored here | DLT gold_positions |
| Positions | NOT stored here | DLT gold_positions |
| Market prices (all 3) | NOT stored here | Simulator writes directly |
| Market simulator output | NOT stored here | Primary target |
| ETRM raw landing | NOT stored here | apex.ingestion.raw_etrm_trades |
| Genie questions | NOT stored here | apex.genie.questions |
