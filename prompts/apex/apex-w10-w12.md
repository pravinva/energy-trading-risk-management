# W10 — Risk Engine API
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-trade-book-seeds.md exist.

---

## OBJECTIVE
Implement the risk management API. This includes on-demand VaR Monte Carlo simulation, scenario stress testing, credit exposure monitoring, and limit breach alerting. The risk manager persona works entirely through these endpoints.

---

## SQL QUERIES: data/queries/risk/

### var_latest.sql
Most recent VaR result for a trader or portfolio. Parameterised: :trader_id (optional), :portfolio_scope (default 'FULL').

### var_history.sql
VaR history over last N days. Parameterised: :trader_id (optional), :days (default 30). Used for VaR trend chart.

### price_returns_history.sql
Daily log returns for each instrument over last 252 days. Used as input to Monte Carlo simulation. Parameterised: :instrument_ids list.

### stress_scenarios.sql
All available stress test scenarios from apex.risk.stress_test_scenarios.

### stress_results_history.sql
Past stress test results for a trader. Parameterised: :trader_id (optional), :days (default 30).

### credit_exposure.sql
Current credit exposure per counterparty with utilisation. Parameterised: :counterparty_id (optional).

### trading_limits.sql
All limit definitions and current utilisation for a trader. Parameterised: :trader_id.

### limit_breaches.sql
Current and historical limit breaches. Parameterised: :trader_id (optional), :days (default 7).

---

## ROUTES: app/backend/routes/risk.py

Pydantic models:
- VaRResult: var_id, calculation_datetime, trader_id optional, var_95_aud Decimal, var_99_aud Decimal, cvar_95_aud Decimal, cvar_99_aud Decimal, position_value_aud Decimal, method str, simulation_count int, pnl_distribution list[float] (for histogram — 100 buckets)
- VaRRequest: trader_id optional str, portfolio_scope str = 'FULL', simulation_count int = 10000
- StressScenario: scenario_id, scenario_name, description, price_shock_pct Decimal, demand_shock_pct Decimal, region_id optional, reference_event
- StressTestResult: result_id, scenario_id, scenario_name, run_datetime, trader_id optional, portfolio_pnl_impact_aud Decimal, worst_case_pnl_aud Decimal, best_case_pnl_aud Decimal, positions_breached int
- StressTestRequest: scenario_id str, trader_id optional str
- CreditExposure: counterparty_id, counterparty_name, mark_to_market_aud Decimal, potential_future_exposure_aud Decimal, total_exposure_aud Decimal, credit_limit_aud Decimal, utilisation_pct Decimal, is_breach bool
- TradingLimit: limit_id, trader_id, limit_type, limit_value Decimal, current_value Decimal, utilisation_pct Decimal, is_breach bool, breach_timestamp optional datetime

Routes:
- GET /api/v1/risk/var — latest VaR result. query: trader_id optional
- POST /api/v1/risk/var/calculate — run VaR NOW. Body: VaRRequest. This triggers the var engine synchronously (for demo purposes — <3s acceptable). Writes result to apex.risk.var_results via Lakebase. Returns VaRResult with pnl_distribution for histogram.
- GET /api/v1/risk/var/history — query: trader_id optional, days int=30
- GET /api/v1/risk/scenarios — list all available stress scenarios
- POST /api/v1/risk/stress-test — run stress test. Body: StressTestRequest. Applies scenario shocks to current positions using stress_test engine function. Writes result to apex.risk.stress_test_results. Returns StressTestResult.
- GET /api/v1/risk/stress-test/history — query: trader_id optional, days int=30
- GET /api/v1/risk/credit — list[CreditExposure]. All counterparties with exposure > 0.
- GET /api/v1/risk/limits — list[TradingLimit]. query: trader_id optional.
- GET /api/v1/risk/limits/breaches — current and recent breaches. query: trader_id optional.

### CALCULATE VAR IMPLEMENTATION
The POST /api/v1/risk/var/calculate route must:
1. Fetch current positions from apex.trading.positions (via Lakebase)
2. Fetch 252 days of price returns from apex.market.nem_prices (or forward_curves) for each instrument
3. Call var.run_monte_carlo_var() with 10,000 simulations using numpy
4. Calculate pnl_distribution as a list of 100 histogram bucket counts (for frontend chart)
5. Write result to apex.risk.var_results via Lakebase
6. Also update apex.risk.trading_limits with new VaR utilisation
7. If VaR_99 > var_limit_aud: set is_breach=TRUE and breach_timestamp on the limit
8. Return within 3 seconds (10,000 simulations should be < 1s in numpy)

### STRESS TEST IMPLEMENTATION
1. Fetch scenario from apex.risk.stress_test_scenarios
2. Fetch current positions from apex.trading.positions
3. Apply price_shock_pct to current market prices: shocked_price = current_price × (1 + price_shock_pct)
4. Recalculate P&L under shocked prices using pnl engine
5. Calculate worst_case (2× the shock) and best_case (scenario reversal)
6. Count positions_breached (where stressed P&L exceeds position limit)
7. Write to apex.risk.stress_test_results via Lakebase
8. Return StressTestResult

### CREDIT EXPOSURE IMPLEMENTATION
Credit exposure = sum of positive MTM positions with each counterparty. If I have bought 100MW at $80 from counterparty A and the market is at $100, counterparty A owes me $20/MWh — that's exposure to counterparty A. Add PFE (potential future exposure) as 20% of MTM (simplified for demo).

---

## TESTS: app/backend/tests/test_risk_routes.py
- test_var_calculate_returns_var_result
- test_var_99_greater_than_var_95_always
- test_var_calculate_writes_to_lakebase
- test_var_pnl_distribution_has_100_buckets
- test_stress_test_returns_pnl_impact
- test_stress_test_writes_result_to_lakebase
- test_limit_breach_flagged_when_var_exceeds_limit
- test_credit_exposure_non_negative
- test_var_calculation_completes_under_3_seconds

---

## SUCCESS CRITERIA
1. POST /api/v1/risk/var/calculate completes in < 3s (measured)
2. VaR_99 > VaR_95 on every run
3. CVaR > VaR on every run
4. Result written to Lakebase — verified
5. pnl_distribution is a list of 100 numbers summing to 10000 (simulation count)
6. Stress test applies shock correctly to positions
7. Limit breach correctly set when VaR > limit
8. All Decimal — no float in response models
9. mypy passes, tests pass

---

## COMPLETION ARTIFACT
completions/W10-risk-api.md
Commit message: "feat: W10 complete — risk engine API with VaR and stress testing"

---
---

# W11 — Portfolio API
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-trade-book-seeds.md exist.

---

## OBJECTIVE
Implement the portfolio management API. Revenue stacking model, PPA book valuation, asset benchmarking, and the interactive revenue simulator that lets a portfolio manager adjust BESS parameters and see how revenue changes.

---

## SQL QUERIES: data/queries/portfolio/

### revenue_actuals.sql
Actual revenue by asset and date. Parameterised: :asset_id (optional), :days (default 365).

### revenue_forecast.sql
Revenue forecast by scenario. Parameterised: :asset_id (optional), :scenario (default 'BASE'), :months (default 24).

### ppa_book.sql
All PPAs with current MTM value. Includes counterparty name JOIN.

### ppa_detail.sql
Single PPA with full history. Parameterised: :ppa_id.

### asset_benchmarking.sql
Revenue per MW per year for each asset compared to calculated market benchmark. Uses settlement data vs simple energy arbitrage benchmark calculation.

### revenue_stacking_components.sql
Revenue breakdown by component (energy, FCAS raise, FCAS lower, cap, PPA) per asset per month. Used for stacked bar chart.

---

## ROUTES: app/backend/routes/portfolio.py

Pydantic models:
- RevenueActual: asset_id, asset_name, revenue_date date, energy_revenue Decimal, fcas_raise_revenue Decimal, fcas_lower_revenue Decimal, total_revenue Decimal, revenue_per_mw Decimal
- RevenueForecast: asset_id, asset_name, forecast_date date, total_revenue_forecast Decimal, confidence_low Decimal, confidence_high Decimal, scenario str
- PPAPosition: ppa_id, ppa_name, counterparty_name, direction, contracted_mw Decimal, strike_price Decimal, start_date date, end_date date, current_mark Decimal, mtm_value_aud Decimal, status, is_in_the_money bool
- AssetBenchmark: asset_id, asset_name, region_id, capacity_mw Decimal, annual_revenue_per_mw Decimal, benchmark_revenue_per_mw Decimal, vs_benchmark_pct Decimal, rank_in_region int
- RevenueStackingInput: asset_id str, duration_hours Decimal, fcas_participation_pct Decimal (0-1), cap_contract_mw Decimal, ppa_contracted_mw Decimal
- RevenueStackingResult: base_case_revenue Decimal, energy_revenue Decimal, fcas_revenue Decimal, cap_revenue Decimal, ppa_revenue Decimal, total_annual_revenue Decimal, revenue_per_mw Decimal, assumptions dict[str, str]
- RevenueComponent: month date, asset_id, energy_revenue Decimal, fcas_raise Decimal, fcas_lower Decimal, cap_revenue Decimal, ppa_revenue Decimal, total Decimal

Routes:
- GET /api/v1/portfolio/revenue/actuals — query: asset_id optional, days int=365
- GET /api/v1/portfolio/revenue/forecast — query: asset_id optional, scenario str='BASE', months int=24
- GET /api/v1/portfolio/revenue/components — query: asset_id optional, months int=12. Returns stacked data per month.
- GET /api/v1/portfolio/ppa — list[PPAPosition]. All active PPAs with MTM.
- GET /api/v1/portfolio/ppa/{ppa_id} — PPAPosition detail.
- POST /api/v1/portfolio/ppa/{ppa_id}/mark — Recalculate MTM against current forward curve. Updates apex.portfolio.ppa_book. Returns updated PPAPosition.
- GET /api/v1/portfolio/benchmarking — list[AssetBenchmark]. All assets vs market benchmark.
- POST /api/v1/portfolio/revenue-stack/simulate — INTERACTIVE REVENUE SIMULATOR. Body: RevenueStackingInput. No database write. Pure calculation. Returns RevenueStackingResult showing how annual revenue changes with different parameters.

### REVENUE STACKING SIMULATOR IMPLEMENTATION
The POST /api/v1/portfolio/revenue-stack/simulate route is the key portfolio tool.

```python
def simulate_revenue_stack(inputs: RevenueStackingInput, market_data: dict) -> RevenueStackingResult:
    """
    Calculates expected annual revenue for a BESS asset given parameters.
    
    Energy revenue:
    - Based on historical TB4 spread (top 4 hours price - bottom 4 hours price)
    - Daily cycles = min(2, duration_hours / 2)  -- simplified
    - Energy revenue = avg_daily_tb4_spread × daily_cycles × capacity_mw × 365
    
    FCAS revenue:
    - Based on historical average FCAS prices
    - FCAS participation = fcas_participation_pct × capacity_mw
    - FCAS revenue = avg_raise6sec_price × fcas_mw × 8760 + avg_lower6sec_price × fcas_mw × 8760
    
    Cap contract:
    - Cap premium = $4-8/MW/quarter × 4 quarters (market typical)
    - Cap revenue = cap_contract_mw × cap_premium_per_mw × 4
    
    PPA revenue:
    - Based on difference between PPA strike and average pool price
    - PPA delta = (avg_pool_price - ppa_strike) × ppa_contracted_mw × utilisation_factor × 8760
    
    Returns breakdown + total with assumptions dictionary explaining each calculation.
    """
```

---

## TESTS: app/backend/tests/test_portfolio_routes.py
- test_revenue_actuals_returns_data_for_all_assets
- test_revenue_forecast_base_case_non_negative
- test_ppa_list_includes_mtm_values
- test_ppa_mark_updates_lakebase
- test_revenue_simulator_total_equals_component_sum
- test_revenue_simulator_higher_fcas_pct_increases_fcas_revenue
- test_benchmarking_returns_rank_per_region

---

## SUCCESS CRITERIA
1. Revenue actuals covers all 8 BESS assets
2. PPA MTM mark updates Lakebase and returns updated value
3. Revenue simulator returns in < 500ms (pure calculation, no DB)
4. Simulator component totals add up to total_annual_revenue
5. Increasing fcas_participation_pct increases fcas_revenue (monotonic)
6. Benchmarking shows rank within region (1 = best)
7. mypy passes, tests pass

---

## COMPLETION ARTIFACT
completions/W11-portfolio-api.md
Commit message: "feat: W11 complete — portfolio management API"

---
---

# W12 — Frontend Shell
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W01-design-system.md AND completions/W06-backend-core.md exist.

---

## OBJECTIVE
Build the APEX application shell. Unlike NEXUS which used a region selector, APEX uses a PERSONA selector — the user chooses their role and gets a workspace optimised for that workflow. Each persona has a different layout, different panels, and different data density requirements.

---

## PERSONA SELECTOR: app/frontend/src/pages/PersonaSelector.tsx

Full viewport landing page. Same dark aesthetic as the design system specifies.

Header (centred):
- "APEX" in --font-data weight 300 letter-spacing 0.3em --color-text-secondary
- "ENERGY TRADING & RISK MANAGEMENT" in --label-caps --color-text-tertiary

Five persona cards in a horizontal row (or 3+2 on smaller screens):

**DISPATCH** (--color-persona-dispatch teal):
Card content:
- Role: "DISPATCH OPERATOR"
- Function: "BESS Dispatch Console"
- Three lines: "Live SOC monitoring" / "Offer stack builder" / "Dispatch recommendations"
- Badge: "NEM · ERCOT"

**TRADER** (--color-persona-trader blue):
- Role: "POWER TRADER"
- Function: "Trading Blotter"
- Three lines: "Deal entry & position book" / "Live P&L mark-to-market" / "Spike alerts & order management"
- Badge: "NEM · EPEX · ERCOT"

**QUANT** (--color-persona-quant purple):
- Role: "QUANT DEVELOPER"
- Function: "Research Console"
- Three lines: "Model performance monitoring" / "Strategy backtesting" / "Signal analysis"
- Badge: "MLflow · Databricks"

**RISK** (--color-persona-risk amber):
- Role: "RISK MANAGER"
- Function: "Risk Dashboard"
- Three lines: "VaR Monte Carlo (live)" / "Stress testing scenarios" / "Limit monitoring & credit"
- Badge: "VaR · Credit · Limits"

**PORTFOLIO** (--color-persona-portfolio emerald):
- Role: "PORTFOLIO MANAGER"
- Function: "Portfolio Dashboard"
- Three lines: "Revenue stacking model" / "PPA book & valuation" / "Asset benchmarking"
- Badge: "Revenue · PPA · P&L"

Each card: 1px border --color-border-default, NO rounded corners, on hover border changes to persona colour, background --color-bg-raised, transition 150ms.
Click → navigate to /{persona} route.

Below cards: market status strip (compact). Shows: NEM OPEN $87/MWh | EPEX OPEN €78/MWh | ERCOT OPEN $42/MWh. Data from useMarketSummary hook. Prices in --font-data, refreshed every 30s.

---

## ROUTER: app/frontend/src/router.ts

```
/ — PersonaSelector
/dispatch — DispatchLayout
/dispatch/console — DispatchConsole (main panel, W13)
/dispatch/fleet — FleetOverview
/trader — TradingLayout
/trader/blotter — TradingBlotter (main panel, W14)
/trader/positions — PositionBook
/trader/orders — OrderManagement
/risk — RiskLayout
/risk/var — VaRDashboard (main panel, W15)
/risk/stress — StressTestPanel
/risk/limits — LimitMonitor
/risk/credit — CreditExposure
/quant — QuantLayout
/quant/models — ModelPerformance (main panel, W16)
/quant/backtest — BacktestConsole
/quant/signals — SignalScanner
/portfolio — PortfolioLayout
/portfolio/revenue — RevenueDashboard (main panel, W17)
/portfolio/ppa — PPABook
/portfolio/assets — AssetBenchmarking
```

---

## SHARED LAYOUT: app/frontend/src/layouts/WorkspaceLayout.tsx

Props: persona, children.

Topbar (fixed 40px — tighter than NEXUS):
- Left: "APEX" wordmark (→ PersonaSelector), separator, persona name in persona colour --label-caps
- Centre: market status ticker (NEM RRP, ERCOT LMP, EPEX price, all in --font-data --text-xs, refreshing every 30s)
- Right: clock in --font-data --text-xs (HH:MM:SS local time, updates every second), trader name in --label-caps

Left sidebar (180px — narrower than NEXUS for more content width):
- Navigation items for the persona's panels
- Active item: persona colour border-left, --color-bg-raised

Status bar (fixed bottom, 22px — standard trading terminal pattern):
- Left: Lakebase connection status (dot + "CONNECTED" or "DEGRADED")
- Centre: last data refresh timestamp in --font-data --text-2xs
- Right: session P&L for trading personas: "SESSION P&L: +$42,300" in --font-data pnl-positive or pnl-negative

### Persona-specific layout files:
DispatchLayout.tsx, TradingLayout.tsx, RiskLayout.tsx, QuantLayout.tsx, PortfolioLayout.tsx
Each wraps WorkspaceLayout with correct persona prop and sidebar navigation.

---

## API CLIENT: app/frontend/src/api/client.ts
Axios client: baseURL /api/v1, 30s timeout.
Unwraps APIResponse wrapper. Error interceptor maps to typed errors.
Add X-Persona header from current route (helps backend logging).

## STATE MANAGEMENT: app/frontend/src/store/
Using Zustand:

tradingStore.ts:
- selectedInstrument: string | null
- activePersona: 'dispatch'|'trader'|'quant'|'risk'|'portfolio' | null
- openOrderCount: number
- sessionPnl: Decimal | null
- activeTrade: TradeEntry | null (for trade entry form state)
- setSelectedInstrument, setSessionPnl, etc.

dispatchStore.ts:
- selectedAssetId: string | null
- activeStackDraft: OfferStackDraft | null — the in-progress offer stack being built
- setSelectedAsset, updateBand, clearDraft

---

## HOOKS: app/frontend/src/api/hooks/

### useMarketSummary.ts
GET /api/v1/market/summary. refetchInterval: 30000. Used by status ticker.

### useUserContext.ts
GET /api/v1/user/me + trader context.

### useHealth.ts
GET /api/v1/health. refetchInterval: 60000. Drives status bar connection indicator.

---

## SUCCESS CRITERIA
1. npm run build zero errors
2. localhost:5173 opens to PersonaSelector with 5 persona cards
3. Market status strip shows real prices from Lakebase
4. Click DISPATCH → /dispatch/console (placeholder W13)
5. Click TRADER → /trader/blotter (placeholder W14)
6. Click RISK → /risk/var (placeholder W15)
7. Click QUANT → /quant/models (placeholder W16)
8. Click PORTFOLIO → /portfolio/revenue (placeholder W17)
9. APEX wordmark returns to PersonaSelector
10. Status bar shows connection status and updates every second (clock)
11. Persona colour applied correctly in sidebar and topbar per persona
12. TypeScript strict: zero errors
13. Vitest tests pass for PersonaSelector and WorkspaceLayout

---

## COMPLETION ARTIFACT
completions/W12-frontend-shell.md
Commit message: "feat: W12 complete — APEX frontend shell with persona routing"
