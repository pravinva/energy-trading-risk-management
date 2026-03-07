# W02 — Database Schema
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W00-foundation.md exists.

---

## OBJECTIVE
Create the complete Unity Catalog schema and all table DDL for APEX. This is significantly broader than NEXUS because it includes the full ETRM data model: trade book, position tables, risk tables, reference data, and market data. Every table must be re-creatable from these SQL files alone.

---

## WORKSPACE
Profile: fe-vm. Execute all SQL via Databricks CLI MCP.

---

## STEP 1: Create catalog and schemas

```sql
CREATE CATALOG IF NOT EXISTS apex
  COMMENT 'APEX Energy Trading & Risk Management Platform';

CREATE SCHEMA IF NOT EXISTS apex.market
  COMMENT 'Market data — prices, generation, interconnectors, BESS telemetry';

CREATE SCHEMA IF NOT EXISTS apex.trading
  COMMENT 'Trade book, positions, P&L, offer stacks, orders';

CREATE SCHEMA IF NOT EXISTS apex.risk
  COMMENT 'VaR, stress testing, credit exposure, limit monitoring';

CREATE SCHEMA IF NOT EXISTS apex.portfolio
  COMMENT 'Revenue stacking, PPA book, asset benchmarking';

CREATE SCHEMA IF NOT EXISTS apex.reference
  COMMENT 'Counterparties, instruments, assets, market structure';

CREATE SCHEMA IF NOT EXISTS apex.analytics
  COMMENT 'ML forecasts, backtesting results, model metadata';
```

---

## DDL FILES

### data/schema/01_reference.sql
Reference data tables. Small and largely static.

apex.reference.counterparties:
- counterparty_id VARCHAR(20) PK, name VARCHAR(100), short_name VARCHAR(20), counterparty_type VARCHAR(30) — GENERATOR, RETAILER, TRADER, FINANCIAL, MARKET_OPERATOR, INTERNAL, BANK
- credit_rating VARCHAR(10), credit_limit_aud DECIMAL(18,2), country VARCHAR(10), is_active BOOLEAN DEFAULT TRUE

apex.reference.instruments:
- instrument_id VARCHAR(30) PK, instrument_name VARCHAR(100), instrument_type VARCHAR(30) — SPOT, FUTURES, SWAP, OPTION, CAP, FLOOR, PPA, BILATERAL, FCAS
- market VARCHAR(10) — NEM, EPEX, ERCOT, PJM, ASX, ICE
- region_id VARCHAR(20), currency VARCHAR(3), lot_size_mw DECIMAL(10,2), settlement_type VARCHAR(20) — PHYSICAL, FINANCIAL
- is_active BOOLEAN DEFAULT TRUE, contract_unit VARCHAR(20) — MWh, MW_DAY, MW_QUARTER

apex.reference.assets:
- asset_id VARCHAR(20) PK, asset_name VARCHAR(100), asset_type VARCHAR(30) — BESS, GAS_CCGT, GAS_OCGT, COAL, WIND, SOLAR, HYDRO, NUCLEAR
- operator VARCHAR(100), region_id VARCHAR(10), capacity_mw DECIMAL(10,2), capacity_factor DECIMAL(5,4)
- heat_rate DECIMAL(8,4) COMMENT 'GJ/MWh — for gas/coal spark spread', variable_cost_aud DECIMAL(10,4) COMMENT '$/MWh'
- fuel_type VARCHAR(30), co2_intensity DECIMAL(10,6) COMMENT 'tCO2/MWh'
- duid VARCHAR(20) COMMENT 'AEMO Dispatchable Unit Identifier where applicable'
- commission_date DATE, status VARCHAR(20) DEFAULT 'ACTIVE'

apex.reference.traders:
- trader_id VARCHAR(20) PK, name VARCHAR(100), desk VARCHAR(50), region VARCHAR(10)
- position_limit_mw DECIMAL(10,2), var_limit_aud DECIMAL(18,2), credit_limit_aud DECIMAL(18,2)
- is_active BOOLEAN DEFAULT TRUE

apex.reference.market_structure:
- market_id VARCHAR(10) PK, market_name VARCHAR(50), operator VARCHAR(50)
- dispatch_interval_minutes INTEGER, settlement_interval_minutes INTEGER
- market_timezone VARCHAR(50), currency VARCHAR(3)
- has_capacity_market BOOLEAN, has_fcas BOOLEAN, is_nodal BOOLEAN

### data/schema/02_market_data.sql
Market data tables. High volume. Use LIQUID CLUSTERING on all time-series tables.

apex.market.nem_prices:
- interval_datetime TIMESTAMP NOT NULL, region_id VARCHAR(10) NOT NULL
- rrp DECIMAL(12,4) COMMENT '$/MWh Regional Reference Price'
- lower6sec, lower60sec, lower5min, raise6sec, raise60sec, raise5min DECIMAL(12,4) COMMENT 'FCAS $/MW/hr'
- lowerreg, raisereg DECIMAL(12,4), totaldemand DECIMAL(12,2), netinterchange DECIMAL(12,2)
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (region_id, interval_datetime)

apex.market.nem_generation:
- interval_datetime TIMESTAMP NOT NULL, region_id VARCHAR(10) NOT NULL
- fuel_type VARCHAR(30), generation_mw DECIMAL(12,2), capacity_factor DECIMAL(5,4)
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (region_id, interval_datetime)

apex.market.nem_bess_telemetry:
- asset_id VARCHAR(20) NOT NULL, recorded_at TIMESTAMP NOT NULL
- state_of_charge_pct DECIMAL(5,2), output_mw DECIMAL(10,2) COMMENT 'positive=discharge, negative=charge'
- fcas_raise_mw DECIMAL(10,2), fcas_lower_mw DECIMAL(10,2), temperature_c DECIMAL(6,2)
- cycle_count_cumulative DECIMAL(10,2), available_mw DECIMAL(10,2)
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (asset_id, recorded_at)

apex.market.nem_predispatch:
- predispatch_datetime TIMESTAMP NOT NULL, run_datetime TIMESTAMP NOT NULL, region_id VARCHAR(10) NOT NULL
- forecast_rrp DECIMAL(12,4), forecast_demand DECIMAL(12,2), forecast_raise5min DECIMAL(12,4)
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (region_id, predispatch_datetime)

apex.market.forward_curves:
- curve_date DATE NOT NULL, instrument_id VARCHAR(30) NOT NULL, tenor VARCHAR(20) NOT NULL — Q1-2026, Cal-2027, etc.
- price DECIMAL(12,4), bid DECIMAL(12,4), offer DECIMAL(12,4), volume DECIMAL(14,2)
- data_source VARCHAR(20) DEFAULT 'SIMULATED'

apex.market.epex_prices:
- delivery_datetime TIMESTAMP NOT NULL, bidding_zone VARCHAR(20) NOT NULL
- price_eur_mwh DECIMAL(12,4), volume_mwh DECIMAL(14,4), mtu_minutes INTEGER DEFAULT 60
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (bidding_zone, delivery_datetime)

apex.market.ercot_lmp:
- interval_datetime TIMESTAMP NOT NULL, node_id VARCHAR(50) NOT NULL
- lmp DECIMAL(12,4), energy_component DECIMAL(12,4), congestion_component DECIMAL(12,4), loss_component DECIMAL(12,4)
- rtcb_signal DECIMAL(10,4) COMMENT 'NULL before 2025-12-05'
- data_source VARCHAR(20) DEFAULT 'SIMULATED'
- CLUSTER BY (node_id, interval_datetime)

### data/schema/03_trading.sql
Core ETRM tables. These are the heart of APEX. Written to Lakebase (Postgres-compatible OLTP) for low-latency operational access. Also exist as Delta tables for analytics.

apex.trading.trades:
- trade_id VARCHAR(36) PK DEFAULT gen_random_uuid(), trade_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- instrument_id VARCHAR(30) NOT NULL, counterparty_id VARCHAR(20) NOT NULL, trader_id VARCHAR(20) NOT NULL
- direction VARCHAR(4) NOT NULL CHECK direction IN ('BUY', 'SELL')
- volume_mw DECIMAL(10,2) NOT NULL COMMENT 'always positive — direction determines long/short'
- price DECIMAL(12,4) NOT NULL COMMENT '$/MWh or $/MW-day depending on instrument'
- delivery_start TIMESTAMP NOT NULL, delivery_end TIMESTAMP NOT NULL
- trade_type VARCHAR(20) NOT NULL — SPOT, BILATERAL, FUTURES, SWAP, CAP, PPA, FCAS_OFFER
- region_id VARCHAR(10), node_id VARCHAR(50) COMMENT 'for nodal trades'
- broker_id VARCHAR(20), broker_fee DECIMAL(10,4)
- status VARCHAR(20) DEFAULT 'CONFIRMED' CHECK status IN ('PENDING','CONFIRMED','PARTIALLY_FILLED','FILLED','CANCELLED','REJECTED')
- settlement_status VARCHAR(20) DEFAULT 'UNSETTLED' CHECK settlement_status IN ('UNSETTLED','SETTLED','DISPUTED')
- notes TEXT, created_by VARCHAR(100), updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

apex.trading.positions:
- position_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- instrument_id VARCHAR(30) NOT NULL, region_id VARCHAR(10), trader_id VARCHAR(20)
- delivery_period VARCHAR(20) NOT NULL COMMENT 'e.g. 2026-Q1, 2026-H1, 2026-CAL'
- net_volume_mw DECIMAL(12,2) COMMENT 'positive=long, negative=short'
- avg_price DECIMAL(12,4), total_volume_mw DECIMAL(12,2)
- current_market_price DECIMAL(12,4), mtm_pnl DECIMAL(18,4)
- last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- UNIQUE (instrument_id, region_id, trader_id, delivery_period)

apex.trading.pnl_daily:
- pnl_date DATE NOT NULL, trader_id VARCHAR(20), region_id VARCHAR(10), instrument_type VARCHAR(30)
- realised_pnl DECIMAL(18,4), unrealised_pnl DECIMAL(18,4), total_pnl DECIMAL(18,4)
- trade_count INTEGER, volume_traded_mw DECIMAL(12,2)
- PRIMARY KEY (pnl_date, trader_id, region_id, instrument_type)

apex.trading.offer_stacks:
- stack_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- asset_id VARCHAR(20) NOT NULL, market VARCHAR(10) NOT NULL, service_type VARCHAR(30) NOT NULL
  COMMENT 'ENERGY, FCAS_RAISE6SEC, FCAS_LOWER6SEC, FCAS_RAISEREG, FCAS_LOWERREG, FCAS_RAISE5MIN, FCAS_LOWER5MIN'
- dispatch_interval TIMESTAMP NOT NULL, submission_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- status VARCHAR(20) DEFAULT 'DRAFT' CHECK status IN ('DRAFT','SUBMITTED','DISPATCHED','CANCELLED')
- submitted_by VARCHAR(100), rebid_reason TEXT COMMENT 'Required for rebids — NEL good faith'
- is_rebid BOOLEAN DEFAULT FALSE, original_stack_id VARCHAR(36)

apex.trading.offer_bands:
- band_id BIGINT GENERATED ALWAYS AS IDENTITY PK
- stack_id VARCHAR(36) NOT NULL REFERENCES apex.trading.offer_stacks(stack_id)
- band_number INTEGER NOT NULL CHECK band_number BETWEEN 1 AND 10
- price_per_mwh DECIMAL(12,4) NOT NULL, volume_mw DECIMAL(10,2) NOT NULL
- dispatched_mw DECIMAL(10,2) DEFAULT 0
- UNIQUE (stack_id, band_number)

apex.trading.orders:
- order_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- instrument_id VARCHAR(30) NOT NULL, trader_id VARCHAR(20) NOT NULL
- direction VARCHAR(4) NOT NULL CHECK direction IN ('BUY', 'SELL')
- order_type VARCHAR(20) NOT NULL CHECK order_type IN ('LIMIT','MARKET','STOP','IOC','FOK')
- volume_mw DECIMAL(10,2) NOT NULL, limit_price DECIMAL(12,4)
- filled_volume_mw DECIMAL(10,2) DEFAULT 0, avg_fill_price DECIMAL(12,4)
- status VARCHAR(20) DEFAULT 'OPEN' CHECK status IN ('OPEN','PARTIAL','FILLED','CANCELLED','EXPIRED')
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMP
- linked_trade_id VARCHAR(36)

apex.trading.dispatch_recommendations:
- recommendation_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- asset_id VARCHAR(20) NOT NULL, dispatch_interval TIMESTAMP NOT NULL
- recommended_mw DECIMAL(10,2), recommended_price DECIMAL(12,4)
- service_type VARCHAR(30), confidence_score DECIMAL(5,4)
- model_version VARCHAR(50), expected_revenue DECIMAL(14,4)
- rationale TEXT, generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- accepted BOOLEAN COMMENT 'NULL=pending, TRUE=accepted, FALSE=rejected'
- accepted_by VARCHAR(100), accepted_at TIMESTAMP

### data/schema/04_risk.sql

apex.risk.var_results:
- var_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- calculation_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- trader_id VARCHAR(20), region_id VARCHAR(10), portfolio_scope VARCHAR(50) DEFAULT 'FULL'
- var_95_aud DECIMAL(18,4) COMMENT '1-day 95% VaR in AUD'
- var_99_aud DECIMAL(18,4) COMMENT '1-day 99% VaR'
- cvar_95_aud DECIMAL(18,4) COMMENT 'Expected Shortfall at 95%'
- cvar_99_aud DECIMAL(18,4) COMMENT 'Expected Shortfall at 99%'
- simulation_count INTEGER DEFAULT 10000, price_vol_1day DECIMAL(10,6)
- position_value_aud DECIMAL(18,4), method VARCHAR(20) DEFAULT 'MONTE_CARLO'

apex.risk.stress_test_scenarios:
- scenario_id VARCHAR(30) PK, scenario_name VARCHAR(100), description TEXT
- price_shock_pct DECIMAL(6,4) COMMENT 'e.g. +0.50 = 50% price increase'
- demand_shock_pct DECIMAL(6,4), volume_shock_pct DECIMAL(6,4)
- region_id VARCHAR(10), market_condition VARCHAR(50)
- reference_event VARCHAR(100) COMMENT 'e.g. AUG_2025_NEM_SPIKE, JUNE_2025_SA_EVENT'

apex.risk.stress_test_results:
- result_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- scenario_id VARCHAR(30) NOT NULL, run_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- trader_id VARCHAR(20), portfolio_pnl_impact_aud DECIMAL(18,4)
- worst_case_pnl_aud DECIMAL(18,4), best_case_pnl_aud DECIMAL(18,4)
- positions_breached INTEGER COMMENT 'number of positions that breach limits'

apex.risk.credit_exposure:
- exposure_id BIGINT GENERATED ALWAYS AS IDENTITY PK
- counterparty_id VARCHAR(20) NOT NULL, calculation_date DATE DEFAULT CURRENT_DATE
- mark_to_market_aud DECIMAL(18,4), potential_future_exposure_aud DECIMAL(18,4)
- total_exposure_aud DECIMAL(18,4), credit_limit_aud DECIMAL(18,4)
- utilisation_pct DECIMAL(6,4), is_breach BOOLEAN DEFAULT FALSE

apex.risk.trading_limits:
- limit_id VARCHAR(30) PK, trader_id VARCHAR(20), region_id VARCHAR(10)
- limit_type VARCHAR(30) — POSITION_MW, VAR_AUD, LOSS_AUD, CREDIT_AUD
- limit_value DECIMAL(18,4), current_value DECIMAL(18,4)
- utilisation_pct DECIMAL(6,4), is_breach BOOLEAN DEFAULT FALSE
- breach_timestamp TIMESTAMP, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### data/schema/05_portfolio.sql

apex.portfolio.ppa_book:
- ppa_id VARCHAR(36) PK DEFAULT gen_random_uuid(), ppa_name VARCHAR(100)
- counterparty_id VARCHAR(20), asset_id VARCHAR(20)
- direction VARCHAR(4) CHECK direction IN ('LONG','SHORT') COMMENT 'Long=buying power, Short=selling'
- contracted_mw DECIMAL(10,2), strike_price_mwd DECIMAL(12,4) COMMENT '$/MWh day-ahead'
- start_date DATE NOT NULL, end_date DATE NOT NULL
- indexation_type VARCHAR(20) — FIXED, CPI, CUSTOM
- settlement_type VARCHAR(20) — FINANCIAL, PHYSICAL
- current_mark DECIMAL(12,4) COMMENT 'current market price vs strike'
- mtm_value_aud DECIMAL(18,4), status VARCHAR(20) DEFAULT 'ACTIVE'

apex.portfolio.revenue_actuals:
- asset_id VARCHAR(20) NOT NULL, revenue_date DATE NOT NULL
- energy_revenue_aud DECIMAL(14,4), fcas_raise_revenue_aud DECIMAL(14,4)
- fcas_lower_revenue_aud DECIMAL(14,4), cap_revenue_aud DECIMAL(14,4)
- total_revenue_aud DECIMAL(14,4), revenue_per_mw DECIMAL(12,4)
- PRIMARY KEY (asset_id, revenue_date)

apex.portfolio.revenue_forecast:
- asset_id VARCHAR(20) NOT NULL, forecast_date DATE NOT NULL
- energy_revenue_forecast DECIMAL(14,4), fcas_revenue_forecast DECIMAL(14,4)
- total_revenue_forecast DECIMAL(14,4), scenario VARCHAR(30) DEFAULT 'BASE'
- confidence_low DECIMAL(14,4), confidence_high DECIMAL(14,4)
- PRIMARY KEY (asset_id, forecast_date, scenario)

### data/schema/06_analytics.sql

apex.analytics.price_forecasts:
- forecast_id BIGINT GENERATED ALWAYS AS IDENTITY PK
- region_id VARCHAR(10), forecast_datetime TIMESTAMP
- horizon VARCHAR(20) — 5MIN, 30MIN, 4HR, DAY_AHEAD
- forecast_price DECIMAL(12,4), confidence_low DECIMAL(12,4), confidence_high DECIMAL(12,4)
- model_version VARCHAR(50), mape DECIMAL(8,6), run_datetime TIMESTAMP

apex.analytics.backtest_runs:
- run_id VARCHAR(36) PK DEFAULT gen_random_uuid()
- strategy_name VARCHAR(100), description TEXT
- start_date DATE, end_date DATE, region_id VARCHAR(10)
- total_pnl_aud DECIMAL(18,4), sharpe_ratio DECIMAL(10,6), max_drawdown_aud DECIMAL(18,4)
- win_rate DECIMAL(5,4), total_trades INTEGER
- run_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP, run_by VARCHAR(100)

apex.analytics.backtest_trades:
- bt_trade_id BIGINT GENERATED ALWAYS AS IDENTITY PK, run_id VARCHAR(36) NOT NULL
- trade_datetime TIMESTAMP, direction VARCHAR(4), volume_mw DECIMAL(10,2)
- entry_price DECIMAL(12,4), exit_price DECIMAL(12,4), pnl_aud DECIMAL(14,4)
- signal_name VARCHAR(100), signal_value DECIMAL(12,6)

---

## STEP 2: Execute all DDL via CLI MCP
Execute each file in order. Verify each table with SELECT COUNT(*).

## STEP 3: Write data/README.md
Full documentation of all tables, schemas, re-seed instructions.

---

## SUCCESS CRITERIA
1. All 6 schemas exist in apex catalog
2. All SQL files are valid and re-runnable
3. All time-series tables use CLUSTER BY (not PARTITIONED BY)
4. apex.trading.offer_stacks has FK to offer_bands
5. apex.trading.trades has CHECK constraints on direction and status
6. apex.risk.stress_test_scenarios inserted with at least 5 reference scenarios (NEM historical events)
7. apex.reference.market_structure has 5 rows (NEM, EPEX, ERCOT, PJM, ASX)
8. gen_random_uuid() works for UUID primary keys
9. No hardcoded credentials in any SQL file

---

## COMPLETION ARTIFACT
completions/W02-database-schema.md
Commit message: "feat: W02 complete — APEX ETRM database schema"

---
---

# W03 — Market Data Seeds: ANZ
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W02-database-schema.md exists.

---

## OBJECTIVE
Populate apex.market with ANZ NEM market data. Use and adapt from sourabhghose/databricks-energy-copilot — do not reinvent the simulator. The market data must be sufficient to power realistic P&L calculations and VaR simulations.

---

## REFERENCE REPOS
- https://github.com/sourabhghose/databricks-energy-copilot/tree/main/setup
  Use setup/11_historical_backfill.py and setup/10_nem_simulator.py as the basis.
  Adapt to write to apex.market schema.

- https://github.com/dgokeeffe/databricks-nemweb-lab
  Use nemweb_datasource.py pattern for NEMWEB API ingestion (live data mode).

---

## WHAT TO BUILD

### data/seeds/market/anz_backfill.py
Adapted from sourabhghose's historical_backfill.py. Writes to apex.market.nem_prices, apex.market.nem_generation, apex.market.nem_bess_telemetry. Date range: 2024-01-01 to 2026-03-01.

Realistic NEM price parameters:
- QLD1, NSW1, VIC1, SA1 — 4 regions
- Average RRP: QLD ~$80, NSW ~$90, VIC ~$95, SA ~$110
- Spike probability: ~0.3% of intervals → $3,000-$15,000
- Negative price probability: ~8% of summer midday intervals
- FCAS: raise6sec $2-20/MW/hr with spikes during contingency events
- Include seasonal pattern (summer 20% higher than winter)

The backfill must also populate apex.market.nem_predispatch (30-min forecast data matching the historical actuals with ±15% noise — simulating what a trader would have seen pre-dispatch).

### data/seeds/market/anz_simulator.py
Adapted from sourabhghose's nem_simulator.py. Writes to apex.market tables every 30 seconds. Added to resources/jobs.yml as a continuous job.

### data/seeds/market/forward_curves.sql
Insert ASX Energy futures curve for NEM regions. Cal-2026, Cal-2027, Q1-Q4 2026 for each of NSW1, QLD1, VIC1, SA1. These are the instruments traders hedge against. Realistic forward prices: approximately current spot + 5-15% risk premium. Use a simple random walk with mean reversion from current spot.

### data/seeds/reference/nem_reference.sql
Reference data for ANZ:
- apex.reference.assets: 8 BESS assets (same as NEXUS — HORNSDALE_1 through ERARING_BESS_1)
- apex.reference.counterparties: 10 NEM market participants (AGL, Origin Energy, EnergyAustralia, CS Energy, Stanwell, Neoen, Akaysha, Shell Energy, Snowy Hydro, ARENA)
- apex.reference.instruments: NEM spot (5 regions), ASX futures (cal and quarterly), FCAS (7 services × 5 regions), cap contracts
- apex.reference.traders: 5 simulated traders (Sarah Chen — Head of Trading, James Wu — Senior Trader, Emma Park — Junior Trader, Alex Thompson — Risk Manager, Morgan Lee — Portfolio Manager)
- apex.reference.market_structure: NEM row (5-min dispatch, AUD, has_fcas=TRUE, is_nodal=FALSE)

### data/seeds/market/nem_stress_scenarios.sql
Insert 5 stress test scenarios into apex.risk.stress_test_scenarios:
1. JUNE_2025_SA_SPIKE: SA region, +400% price shock, reference_event='June 26 2025 NEM SA event'
2. AUG_2025_NEM_SPIKE: All regions, +200% price, reference_event='5 Aug 2025 NEM-wide spike'
3. SOLAR_CANNIB_EXTREME: Summer midday, -80% price in QLD/NSW/SA, demand_shock -15%
4. COAL_OUTAGE_WINTER: VIC/NSW, +150% price, supply -20% (major coal unit failure)
5. INTERCONNECTOR_TRIP: SA isolated, SA price +300%, Victoria -10%

---

## SUCCESS CRITERIA
1. apex.market.nem_prices: 400,000-600,000 rows (2 years × 4 regions × 288/day)
2. apex.market.nem_generation: proportional rows
3. apex.market.nem_bess_telemetry: 8 assets × 2 years × 288/day
4. apex.market.nem_predispatch: covers same date range
5. apex.market.forward_curves: 5 tenors × 4 regions = 20 rows minimum
6. apex.reference.assets: 8 rows
7. apex.reference.counterparties: 10 rows
8. apex.reference.traders: 5 rows (matching the 5 APEX personas)
9. apex.reference.instruments: minimum 40 rows covering all instrument types
10. apex.risk.stress_test_scenarios: 5 rows
11. Simulator runs without error and inserts new rows every 30s when triggered
12. RRP verification: SA1 average 80-130, max > 5000, negative count > 0

---

## COMPLETION ARTIFACT
completions/W03-market-data-anz.md
Commit message: "feat: W03 complete — ANZ market data seeds"

---
---

# W04 — Market Data Seeds: Europe + Americas
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W02-database-schema.md exists.

---

## OBJECTIVE
Populate apex.market with Europe (EPEX) and Americas (ERCOT) market data. Europe supports the EPEX trading workflow. ERCOT supports the RTC+B dispatch workflow.

---

## FILES TO CREATE

### data/seeds/market/epex_backfill.py
Python script using Databricks SQL to generate EPEX day-ahead prices.
Target: apex.market.epex_prices
Date range: 2024-01-01 to 2026-03-01
Zones: DE-LU, FR, BE, NL, ES, NO1, NO2, CH (8 zones)
MTU: 60 before 2025-09-01, 15 from 2025-09-01 (critical)
Price patterns: realistic averages per zone, duck curve, wind generation effect, winter peaks, negative prices in DE/ES summer midday

### data/seeds/market/ercot_backfill.py
Python script generating ERCOT LMP data.
Target: apex.market.ercot_lmp
Date range: 2025-01-01 to 2026-03-01 (ERCOT only — no pre-2025 ERCOT in this demo)
Nodes: West Hub, Houston Hub, North Hub, Panhandle Wind (x3), Dallas/Houston load (x2), data center nodes (x2) — 10 total
RTC+B boundary: rtcb_signal = NULL before 2025-12-05, populated after
Price patterns: ERCOT energy-only volatility, summer afternoon spikes, wind generation Panhandle basis

### data/seeds/reference/global_reference.sql
Reference data for non-ANZ markets:

apex.reference.assets: Add 5 ERCOT BESS assets and 3 European gas/wind assets.

apex.reference.counterparties: Add 8 global counterparties:
- Shell Trading (Netherlands), TotalEnergies Trading (France), Axpo (Switzerland), Equinor (Norway)
- Vistra Energy (Texas), NRG Energy (US), Macquarie Energy (US), Vitol (UK)

apex.reference.instruments: Add EPEX spot, ERCOT real-time, ERCOT day-ahead, EU ETS futures instruments.

apex.reference.market_structure:
- EPEX: 15-min MTU from 2025-09-01, EUR, no_fcas, is_nodal=FALSE
- ERCOT: 5-min, USD, no_capacity_market, is_nodal=TRUE, rtcb_live_from=2025-12-05
- PJM: 5-min, USD, has_capacity=TRUE, is_nodal=TRUE

### data/seeds/market/ercot_bess_reference.sql
10 ERCOT BESS assets in apex.reference.assets (in addition to ANZ ones):
- 2 West Texas (near Permian), 3 North Texas, 2 Houston, 3 South Texas
- All rtcb_eligible = TRUE (stored as custom attribute in notes field)

---

## SUCCESS CRITERIA
1. apex.market.epex_prices: MTU=60 before 2025-09-01, MTU=15 after — verified
2. apex.market.ercot_lmp: rtcb_signal IS NULL before 2025-12-05 — verified
3. apex.market.ercot_lmp: rtcb_signal IS NOT NULL from 2025-12-05 — verified
4. All 8 EPEX zones have data
5. apex.reference.counterparties: 18 total rows (10 ANZ + 8 global)
6. apex.reference.market_structure: 5 rows (NEM, EPEX, ERCOT, PJM, ASX)
7. Re-run idempotency confirmed for all scripts

---

## COMPLETION ARTIFACT
completions/W04-market-data-global.md
Commit message: "feat: W04 complete — Europe and Americas market data seeds"

---
---

# W05 — Trade Book Seeds
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W03-market-data-anz.md exists.

---

## OBJECTIVE
Seed a realistic pre-existing trade book so the APEX trading workspace is immediately usable. A blank trade book means no positions, no P&L, nothing for the risk manager to analyse. The pre-seeded book must represent a credible multi-desk energy trading portfolio.

---

## DESIGN: THE APEX PORTFOLIO

The seeded book represents a fictional Australian power generator and trader with a multi-region NEM portfolio. The five APEX traders (from W03 reference data) have the following books:

**Sarah Chen — Head of Trading**
- 20 bilateral trades across NEM regions (mix of buy/sell, different counterparties)
- 10 ASX futures positions (long Cal-2027 NSW and QLD, short Cal-2026 VIC)
- Net long NSW1, net short SA1
- Aggregate portfolio: +450MW long NEM, mixed FCAS positions

**James Wu — Senior Trader**
- 15 spot trades and 8 FCAS offer submissions (last 30 days)
- Focus on QLD1 and SA1 arbitrage
- Net short QLD1 day-ahead, net long SA1 spot

**Emma Park — Junior Trader**
- 10 trades, smaller sizes, mix of instruments
- NEM spot and one PPA (long, Origin Energy, 50MW, 2yr)
- Largely flat book

**Alex Thompson — Risk Manager (read-only trader — no trading, just monitoring)**
- No direct positions. Has a synthetic "portfolio view" showing aggregate across all traders.

**Morgan Lee — Portfolio Manager**
- PPA book: 3 PPAs (long 2 × 100MW, short 1 × 80MW)
- Revenue actuals: 8 BESS assets, last 12 months
- Revenue forecasts: next 24 months BASE/HIGH/LOW scenarios

---

## SQL FILES

### data/seeds/trades/01_trades.sql
INSERT approximately 50 trades into apex.trading.trades covering:
- Date range: last 90 days of trades (use CURRENT_TIMESTAMP - INTERVAL N DAYS pattern)
- Mix of instrument types: 20 SPOT, 10 BILATERAL, 10 FUTURES, 5 CAP, 5 PPA
- Mix of directions: ~55% BUY, 45% SELL
- Prices derived from the seeded forward curves with ±5% noise
- All 5 traders represented
- 8 counterparties used
- Status: 40 CONFIRMED, 5 PARTIALLY_FILLED, 3 CANCELLED, 2 PENDING

### data/seeds/trades/02_positions.sql
Insert calculated positions into apex.trading.positions. These must be CONSISTENT with the trades — positions should equal the net of all trades by instrument and delivery period.

Do this calculation in SQL:
```sql
INSERT INTO apex.trading.positions (instrument_id, region_id, trader_id, delivery_period, net_volume_mw, avg_price, total_volume_mw, current_market_price, mtm_pnl)
SELECT
  t.instrument_id,
  t.region_id,
  t.trader_id,
  -- derive delivery_period from delivery_start
  CONCAT(YEAR(t.delivery_start), '-Q', QUARTER(t.delivery_start)) as delivery_period,
  SUM(CASE WHEN t.direction = 'BUY' THEN t.volume_mw ELSE -t.volume_mw END) as net_volume_mw,
  AVG(t.price) as avg_price,
  SUM(t.volume_mw) as total_volume_mw,
  -- join to current market price from forward_curves or nem_prices
  fc.price as current_market_price,
  -- MTM P&L = (current_price - avg_trade_price) × net_volume_mw × hours
  (fc.price - AVG(t.price)) * SUM(CASE WHEN t.direction = 'BUY' THEN t.volume_mw ELSE -t.volume_mw END) as mtm_pnl
FROM apex.trading.trades t
LEFT JOIN apex.market.forward_curves fc ON fc.instrument_id = t.instrument_id
WHERE t.status IN ('CONFIRMED', 'PARTIALLY_FILLED')
GROUP BY t.instrument_id, t.region_id, t.trader_id, delivery_period, fc.price;
```

### data/seeds/trades/03_offer_stacks.sql
Insert 5 pre-existing offer stacks for BESS assets:
- HORNSDALE_1: energy offer stack for next dispatch interval, 10 bands ($0-$300/MWh, stepped)
- WARATAH_1: energy offer stack + FCAS raise6sec offer stack
- ERARING_BESS_1: energy offer stack (4hr duration — different band structure)

Each stack has 10 offer_bands with realistic price-volume allocation:
- Low bands (1-3): high volume at low prices (charging signal)
- Mid bands (4-7): moderate volume at moderate prices
- High bands (8-10): small volume at high prices (spike capture)

### data/seeds/trades/04_pnl_daily.sql
Insert 90 days of daily P&L into apex.trading.pnl_daily for all 5 traders.
- Base P&L: positive 60% of days, negative 40%
- Range: -$200,000 to +$400,000 per trader per day
- Cumulative: Sarah Chen +$8.2M YTD, James Wu +$4.1M, Emma Park +$0.9M
- Include realistic clustering (good weeks, bad weeks — correlated with price spikes in market data)

### data/seeds/trades/05_ppa_book.sql
Insert 3 PPAs into apex.portfolio.ppa_book:
- APEX_PPA_001: Long 100MW from Pacific Hydro, strike $85/MWh, 3yr, FINANCIAL
- APEX_PPA_002: Long 80MW from Neoen Hornsdale Wind, strike $72/MWh, 5yr, PHYSICAL
- APEX_PPA_003: Short 80MW to AGL (selling), strike $95/MWh, 2yr, FINANCIAL (above market = in the money)

### data/seeds/trades/06_revenue_actuals.sql
Insert 12 months of revenue actuals into apex.portfolio.revenue_actuals for all 8 BESS assets. Revenue consistent with the settlement data from the market data backfill.

### data/seeds/trades/07_revenue_forecasts.sql
Insert 24-month revenue forecasts (BASE/HIGH/LOW scenarios) for all 8 BESS assets.

### data/seeds/trades/00_run_all.sql
Master script: TRUNCATE + sequential execution of all 7 files.

---

## SUCCESS CRITERIA
1. apex.trading.trades: 50 rows, mix of all instrument types
2. apex.trading.positions: rows calculated from trades — net_volume_mw is correct
3. apex.trading.positions: Sarah Chen has net_long position in at least 2 regions
4. apex.trading.offer_stacks: 5 stacks with 10 bands each = 50 band rows
5. apex.trading.pnl_daily: 90 rows per trader = 450 total
6. apex.portfolio.ppa_book: 3 rows, including 1 SHORT direction
7. apex.portfolio.revenue_actuals: 8 assets × 365 days = 2,920 rows
8. apex.portfolio.revenue_forecast: 8 assets × 24 months × 3 scenarios = 576 rows
9. MTM P&L in positions table is non-null and calculated correctly
10. Re-run idempotency confirmed

---

## COMPLETION ARTIFACT
completions/W05-trade-book-seeds.md
Commit message: "feat: W05 complete — APEX trade book and position seeds"
