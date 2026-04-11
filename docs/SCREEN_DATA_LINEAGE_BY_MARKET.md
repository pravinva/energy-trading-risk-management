# Screen Data Lineage by Market

This document maps each UI screen to:
- frontend component and hooks
- backend APIs and route handlers
- SQL query files and Unity Catalog tables
- upstream Databricks jobs, notebooks, scripts, and DLT pipelines

It is intended as a detailed, market-aware traceability reference for `NEM`, `EPEX`, and `ERCOT`.

---

## 1) Shared Upstream Producers (All Screens)

### 1.1 Batch Jobs (`databricks.yml`)

- `APEX - NEMWEB Real-Time Ingestion`  
  - Task: `jobs/ingestion/nemweb_real_time.py`  
  - Primary writes/read path: NEM ingestion service (`app.backend.nemweb.ingestion`) -> `apex_fresh.market_nem.*`
- `APEX - EPEX Day-Ahead Ingestion`  
  - Task: `jobs/ingestion/epex_day_ahead.py`  
  - Primary writes/read path: EPEX ingestion service (`app.backend.epex.ingestion`) -> `apex_fresh.market_epex.*`
- `APEX - ERCOT Real-Time Ingestion`  
  - Task: `jobs/ingestion/ercot_real_time.py`  
  - Primary writes/read path: ERCOT ingestion service (`app.backend.ercot.ingestion`) -> `apex_fresh.market_ercot.*`
- `APEX - Daily Model Training` (currently paused)  
  - Notebooks: `notebooks/01_price_forecast_automl.py`, `notebooks/02_demand_forecast_automl.py`  
  - Writes: `apex_fresh.forecasting.price_forecast_automl`, `apex_fresh.forecasting.demand_forecast_automl`, `apex_fresh.forecasting.model_performance`
- `APEX - Overnight VaR Calculation` (paused)  
  - Task: `jobs/analytics/var_batch.py`  
  - Writes: `apex_fresh.trading.var_calculations`, `apex_fresh.trading.risk_alerts`
- `APEX - End of Day Reconciliation` (paused)  
  - Task: `jobs/analytics/eod_reconciliation.py`  
  - Writes: `apex_fresh.trading.reconciliation_results`, `apex_fresh.trading.reconciliation_alerts`, `apex_fresh.trading.reconciliation_summary`
- `APEX - Model Drift Monitoring` (paused)  
  - Task: `jobs/analytics/model_drift_monitor.py`  
  - Reads/writes: `apex_fresh.forecasting.model_performance` -> `apex_fresh.forecasting.drift_monitoring`, `apex_fresh.forecasting.model_alerts`

### 1.2 DLT Pipeline

- Pipeline: `apex_fresh/resources/pipelines.yml` -> `apex-fresh-etrm-ingestion`
- Notebook: `apex_fresh/app/pipelines/etrm_ingestion.py`
- Tables created by pipeline:
  - `apex_fresh.bronze_etrm_trades`
  - `apex_fresh.silver_trades`
  - `apex_fresh.gold_positions`
- Note: current FastAPI screens primarily query `apex_fresh.trading.*` and market schemas directly; this DLT flow is an additional ingestion lane, not the main read path for current UI routes.

### 1.3 Bootstrap / Seed Scripts

- `scripts/setup_database.py` + SQL in `sql/setup/*.sql` create catalog/schemas/tables.
- `scripts/seed_market_data.py` seeds:
  - `apex_fresh.market_nem.prices`
  - `apex_fresh.market_epex.prices`
  - `apex_fresh.market_ercot.lmp`
- `scripts/seed_operational_data.py` seeds:
  - `apex_fresh.trading.trades`
  - `apex_fresh.analytics.model_performance`
  - `apex_fresh.analytics.backtest_runs`
  - `apex_fresh.trading.dispatch_reference`
  - `apex_fresh.trading.offer_bands`
- `sql/setup/05_create_portfolio_tables.sql` seeds:
  - `apex_fresh.portfolio.revenue_rates`
  - `apex_fresh.portfolio.simulation_defaults`

---

## 2) Global and Entry Screens

### Region Selector (`/`)
- Frontend: `app/frontend/src/pages/RegionSelector.tsx`
- Hooks: `useCurrentPrices`
- API: `GET /api/v1/market/current-prices`
- Backend: `app/backend/routes/market.py::current_prices`
- Tables:
  - `apex_fresh.market_nem.prices`
  - `apex_fresh.market_epex.prices`
  - `apex_fresh.market_ercot.lmp`
- Upstream:
  - Jobs: NEMWEB, EPEX day-ahead, ERCOT real-time ingestion
  - Script fallback: `scripts/seed_market_data.py`

### Market Persona Entry (`/nem`, `/epex`, `/ercot`)
- Frontend: `app/frontend/src/pages/MarketPersonaEntry.tsx`
- Data usage: no direct API/table reads; sets selected market context only.

### Persona Selector (`/personas`)
- Frontend: `app/frontend/src/pages/PersonaSelector.tsx`
- Data usage: local state routing; no direct API/table reads.

---

## 3) Workspace Screens (`/workspace/*`) - Market-aware (`NEM`, `EPEX`, `ERCOT`)

## 3.1 Dispatch Console (`/workspace/dispatch`)
- Frontend: `DispatchConsole.tsx`
- Hooks / APIs:
  - `useMarketSummary` -> `GET /market/summary`
  - `usePredispatch` -> `GET /market/predispatch?market=...`
  - `useForecastMetadata` -> `GET /market/forecast-metadata?market=...`
  - `useModelLineage` -> `GET /analytics/model-lineage?market=...`
  - `useDispatchAssets` -> `GET /dispatch/assets?market=...`
  - `useDispatchServiceTypes` -> `GET /dispatch/service-types?market=...`
  - `useDispatchRecommendation` -> `GET /dispatch/recommendations/{asset_id}`
  - `useDispatchStackHistory` -> `GET /dispatch/stack-history`
  - `useLatestOfferStack` -> `GET /dispatch/offer-stack/latest`
- Backend routes:
  - `app/backend/routes/market.py`
  - `app/backend/routes/analytics.py`
  - `app/backend/routes/dispatch.py`
- Core tables:
  - Forecasts/metadata: `apex_fresh.analytics.price_forecasts`
  - Lineage: `apex_fresh.analytics.model_lineage`
  - Dispatch config/state: `apex_fresh.trading.dispatch_reference`, `apex_fresh.trading.offer_bands`, `apex_fresh.trading.offer_stacks`, `apex_fresh.trading.dispatch_recommendations`
  - Market spot inputs in recommendation calc:
    - NEM: `apex_fresh.market_nem.prices`
    - EPEX: `apex_fresh.market_epex.prices`
    - ERCOT: `apex_fresh.market_ercot.lmp`
- Upstream assets:
  - Jobs: market ingestion jobs + model training job (for forecast table)
  - Scripts: `scripts/seed_operational_data.py` for dispatch reference/bands

## 3.2 Trading Blotter (`/workspace/trading`)
- Frontend: `TradingBlotter.tsx`
- Hooks / APIs:
  - `useMarketTradeBlotter` -> `GET /trades/blotter?market=...`
  - `usePositions` -> `GET /positions/book`
  - `useExposureHeatmap` -> `GET /trades/exposure-heatmap?market=...`
  - `useMarketInstruments` -> `GET /market/instruments?market=...`
  - `useInstrumentQuote` -> `GET /market/instrument-quote?market=...&instrument=...`
- Backend routes:
  - `app/backend/routes/trades.py`
  - `app/backend/routes/positions.py`
  - `app/backend/routes/market.py`
  - SQL file: `data/queries/trades/trade_blotter.sql`
- Core tables:
  - Trades/positions: `apex_fresh.trading.trades`
  - Mark-to-market source by market:
    - NEM: `apex_fresh.market_nem.prices`
    - EPEX: `apex_fresh.market_epex.prices`
    - ERCOT: `apex_fresh.market_ercot.lmp`
- Upstream assets:
  - DLT optional lane: `apex_fresh/app/pipelines/etrm_ingestion.py`
  - Scripts: `scripts/seed_operational_data.py`
  - Jobs: market ingestion jobs update mark prices used in MTM

## 3.3 Risk Dashboard (`/workspace/risk`)
- Frontend: `RiskDashboard.tsx`
- Hooks / APIs:
  - `useVaR` -> `POST /risk/var/calculate`
  - `useLimitStatus` -> `GET /risk/limits/status`
  - `useMarketSpotPrice` -> `GET /market/spot-price?market=...`
  - `usePredispatch` -> `GET /market/predispatch?market=...`
  - `useForecastMetadata` -> `GET /market/forecast-metadata?market=...`
  - `useModelLineage` -> `GET /analytics/model-lineage?market=...`
  - `useStressScenarios` -> `GET /risk/stress-scenarios?market=...`
  - `useTraders` -> `GET /user/traders`
- Backend routes:
  - `app/backend/routes/risk.py`
  - `app/backend/routes/market.py`
  - `app/backend/routes/analytics.py`
  - `app/backend/routes/user.py`
- Core tables:
  - Exposure and limits: `apex_fresh.trading.trades`, `apex_fresh.risk.limit_definitions`
  - Spot/strip inputs:
    - NEM: `apex_fresh.market_nem.prices`
    - EPEX: `apex_fresh.market_epex.prices`
    - ERCOT: `apex_fresh.market_ercot.lmp`
  - Forecast/lineage: `apex_fresh.analytics.price_forecasts`, `apex_fresh.analytics.model_lineage`
- Upstream assets:
  - Jobs: market ingestion + model training
  - Scripts: `scripts/seed_market_data.py`, `scripts/seed_operational_data.py`
  - Optional batch comparator: `jobs/analytics/var_batch.py`

## 3.4 Stress Testing (`/workspace/risk/stress-testing`)
- Frontend: `StressTesting.tsx`
- Hooks / APIs:
  - `useMarketSpotPrice` -> `GET /market/spot-price`
  - `useStressRunset` -> `GET /risk/stress-runset`
- Backend routes: `market.py`, `risk.py`
- Core tables:
  - `apex_fresh.trading.trades`
  - `apex_fresh.market_nem.prices` / `apex_fresh.market_epex.prices` / `apex_fresh.market_ercot.lmp`
- Upstream assets: market ingestion jobs + trade seed/ingestion.

## 3.5 Limit Monitor (`/workspace/risk/limit-monitor`)
- Frontend: `LimitMonitor.tsx`
- Hook / API: `useLimitStatus` -> `GET /risk/limits/status`
- Backend route: `risk.py::limits_status`
- Core tables:
  - `apex_fresh.trading.trades`
  - `apex_fresh.risk.limit_definitions`
- Upstream assets:
  - SQL setup: `sql/setup/04_create_risk_tables.sql`
  - Script: `scripts/setup_database.py`

## 3.6 Credit Exposure (`/workspace/risk/credit-exposure`)
- Frontend: `CreditExposure.tsx`
- Hooks / APIs:
  - `useCreditExposure` -> `GET /risk/credit-exposure?market=...`
  - `usePositions` -> `GET /positions/book`
- Backend routes: `risk.py::credit_exposure`, `positions.py::position_book`
- Core tables:
  - `apex_fresh.trading.trades` (counterparty grouping via `source_system`)
- Upstream assets: `scripts/seed_operational_data.py` / trading ingestion.

## 3.7 Quant Console (`/workspace/quant`)
- Frontend: `QuantConsole.tsx`
- Hooks / APIs:
  - `useModelPerformance` -> `GET /analytics/model-performance`
  - `useBacktests` -> `GET /analytics/backtests`
  - `useBacktestStrategies` -> `GET /analytics/strategies?market=...`
  - `useModelLineage` -> `GET /analytics/model-lineage?market=...`
  - `usePredispatch` -> `GET /market/predispatch?market=...`
  - `useForecastMetadata` -> `GET /market/forecast-metadata?market=...`
- Backend routes:
  - `analytics.py`, `market.py`
- Core tables:
  - `apex_fresh.analytics.model_performance`
  - `apex_fresh.analytics.backtest_runs`
  - `apex_fresh.analytics.strategy_catalog`
  - `apex_fresh.analytics.model_lineage`
  - `apex_fresh.analytics.price_forecasts`
- Upstream assets:
  - Jobs: model training (`notebooks/01_*`, `02_*`) and optional drift monitor
  - Scripts: `scripts/seed_operational_data.py`

## 3.8 Portfolio Dashboard (`/workspace/portfolio`)
- Frontend: `PortfolioDashboard.tsx`
- Hooks / APIs:
  - `useRevenueStacking` -> `GET /portfolio/revenue-stacking?market=...`
  - `usePPABook` -> `GET /portfolio/ppa-book?market=...`
  - `useAssetBenchmark` -> `GET /portfolio/asset-benchmark?market=...`
  - `usePortfolioSimulationDefaults` -> `GET /portfolio/simulation-defaults?market=...`
  - `usePortfolioSimulation` -> `GET /portfolio/simulation?...`
- Backend route: `app/backend/routes/portfolio.py`
- Core tables:
  - `apex_fresh.trading.trades` (market-filtered)
  - `apex_fresh.portfolio.revenue_rates`
  - `apex_fresh.portfolio.simulation_defaults`
- Market behavior:
  - `NEM`, `EPEX`, `ERCOT` all use identical formulas with market-filtered trade base.
  - Missing rows in `revenue_rates` / `simulation_defaults` will suppress realistic output.
- Upstream assets:
  - SQL setup and seed: `sql/setup/05_create_portfolio_tables.sql`
  - Bootstrap runner: `scripts/setup_database.py`
  - Operational trade feed: DLT or seed/ingestion scripts

---

## 4) ANZ Region Screens (`/anz/*`) - Market focus: NEM/ANZ

## 4.1 ANZ Market Dashboard (`/anz/market`)
- Frontend: `ANZMarketDashboard.tsx`
- APIs:
  - `GET /anz/prices/current`
  - `GET /anz/prices/history`
  - `GET /anz/fcas/summary`
  - `GET /anz/spikes`
- Backend route: `app/backend/routes/anz.py`
- SQL files:
  - `data/queries/anz/rrp_current.sql`
  - `data/queries/anz/rrp_by_region.sql`
  - `data/queries/anz/fcas_market_summary.sql`
  - `data/queries/anz/spike_events.sql`
- Physical tables (query source):
  - `serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals`
- Upstream:
  - NEMWEB job (`apex_nemweb_realtime`) + NEM ingestion service

## 4.2 ANZ BESS Intelligence (`/anz/bess`)
- Frontend: `ANZBESSIntelligence.tsx`
- APIs:
  - `GET /anz/bess/fleet`
  - `GET /anz/bess/{duid}/telemetry`
  - `GET /anz/bess/{duid}/revenue`
- Backend route: `anz.py`
- SQL files:
  - `data/queries/anz/bess_fleet_summary.sql`
  - `data/queries/anz/bess_telemetry_timeseries.sql`
  - `data/queries/anz/revenue_attribution.sql`
- Physical tables:
  - `serverless_sandbox_tladem_catalog.nexus_anz.bess_assets`
  - `serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry`
  - `serverless_sandbox_tladem_catalog.nexus_anz.settlement_revenues`

## 4.3 ANZ ETRM Positioning (`/anz/etrm`)
- Frontend: `ANZETRMPositioning.tsx`
- Data: static content only (no API, no table).

---

## 5) Europe Screens (`/europe/*`) - Market focus: EPEX/Europe

## 5.1 Europe Market Dashboard (`/europe/market`)
- Frontend: `EuropeMarketDashboard.tsx`
- APIs:
  - `GET /europe/prices/current`
  - `GET /europe/prices/history?bidding_zone=...`
  - `GET /europe/flows/cross-border`
- Backend route: `app/backend/routes/europe.py`
- SQL files:
  - `data/queries/europe/epex_current_prices.sql`
  - `data/queries/europe/epex_price_history.sql`
  - `data/queries/europe/cross_border_utilisation.sql`
- Physical tables:
  - `serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices`
  - `serverless_sandbox_tladem_catalog.nexus_europe.cross_border_flows`
- Upstream:
  - EPEX day-ahead ingestion job + `EPEXIngestionService`

## 5.2 Europe Portfolio Intelligence (`/europe/portfolio`)
- Frontend: `EuropePortfolioIntelligence.tsx`
- APIs:
  - `GET /europe/assets/openlink-incumbent`
  - `GET /europe/spreads/spark?bidding_zone=...`
- SQL files:
  - `data/queries/europe/openlink_displacement_summary.sql`
  - `data/queries/europe/spark_spread_history.sql`
- Physical tables:
  - `serverless_sandbox_tladem_catalog.nexus_europe.generation_portfolio`
  - `serverless_sandbox_tladem_catalog.nexus_europe.spark_spreads`

## 5.3 Europe ETRM Positioning (`/europe/etrm`)
- Frontend: `EuropeETRMPositioning.tsx`
- API:
  - `GET /europe/audit/remit?bidding_zone=...&audit_date=...`
- SQL file:
  - `data/queries/europe/remit_audit_example.sql`
- Physical table:
  - `serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices`

---

## 6) Americas Screens (`/americas/*`) - Market focus: ERCOT and multi-ISO

## 6.1 Americas Market Dashboard (`/americas/market`)
- Frontend: `AmericasMarketDashboard.tsx`
- APIs:
  - `GET /americas/prices/current?iso_id=...`
  - `GET /americas/prices/history?iso_id=...`
- Backend route: `app/backend/routes/americas.py`
- SQL files:
  - `data/queries/americas/multi_iso_lmp_current.sql`
  - `data/queries/americas/multi_iso_lmp_history.sql`
- Physical tables:
  - `serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime`
  - `serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes`
- Upstream:
  - ERCOT job contributes ERCOT slice; other ISO rows depend on source synchronization for `nexus_americas`.

## 6.2 Americas BESS Intelligence (`/americas/bess`)
- Frontend: `AmericasBESSIntelligence.tsx`
- API:
  - `GET /americas/ercot/rtcb-comparison/{resource_id}`
- SQL file:
  - `data/queries/americas/ercot_rtcb_comparison.sql`
- Physical table:
  - `serverless_sandbox_tladem_catalog.nexus_americas.ercot_bess_telemetry`

## 6.3 Americas ETRM Positioning (`/americas/etrm`)
- Frontend: `AmericasETRMPositioning.tsx`
- APIs:
  - `GET /americas/pjm/capacity-auctions`
  - `GET /americas/ieso/nodal-basis`
  - `GET /americas/prices/current` (row-count probe)
- SQL files:
  - `data/queries/americas/pjm_capacity_auction_history.sql`
  - `data/queries/americas/ieso_nodal_basis_leaders.sql`
  - `data/queries/americas/multi_iso_lmp_current.sql`
- Physical tables:
  - `serverless_sandbox_tladem_catalog.nexus_americas.pjm_capacity_auctions`
  - `serverless_sandbox_tladem_catalog.nexus_americas.ieso_nodal_prices`
  - `serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes`
  - `serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime`

---

## 7) Market-to-Table Quick Map (Core Workspace Screens)

For `/workspace/*` screens, market-sensitive table resolution is:

- `NEM` -> `apex_fresh.market_nem.prices`
- `EPEX` -> `apex_fresh.market_epex.prices`
- `ERCOT` -> `apex_fresh.market_ercot.lmp`

Shared non-market tables used across screens:

- `apex_fresh.trading.trades`
- `apex_fresh.trading.dispatch_reference`
- `apex_fresh.trading.offer_bands`
- `apex_fresh.analytics.price_forecasts`
- `apex_fresh.analytics.model_performance`
- `apex_fresh.analytics.backtest_runs`
- `apex_fresh.analytics.model_lineage`
- `apex_fresh.analytics.strategy_catalog`
- `apex_fresh.risk.limit_definitions`
- `apex_fresh.portfolio.revenue_rates`
- `apex_fresh.portfolio.simulation_defaults`

---

## 8) Maintenance Guidance

When adding a new screen or metric:

1. Add/confirm route in `app/frontend/src/router.tsx`.
2. Add hook in `app/frontend/src/api/hooks/*.ts`.
3. Add backend endpoint in `app/backend/routes/*.py`.
4. Add SQL query file in `data/queries/...` (if applicable).
5. Record upstream producer (job/notebook/script/pipeline) for each new table.
6. Update this document with:
   - route
   - APIs
   - tables
   - producer path

