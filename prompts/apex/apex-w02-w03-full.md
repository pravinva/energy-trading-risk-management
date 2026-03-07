# APEX W02–W03d: Database Schema + DLT Ingestion + Market Simulators

---

# W02 — Database Schema (Multi-Market)

## PREREQUISITE CHECK
Verify completions/W00-foundation.md exists.

## OBJECTIVE
Create all Unity Catalog schemas and DDL for the three-market APEX platform. All tables must be re-creatable from SQL files alone. Key design principle: `apex.trading.*` tables are analytics tables populated by DLT from ETRM sources — they are NOT operational OLTP tables.

## STEP 1: Create catalog and schemas

```sql
CREATE CATALOG IF NOT EXISTS apex
  COMMENT 'APEX Energy Analytics Platform — NEM · EPEX · ERCOT';

-- Per-market price schemas
CREATE SCHEMA IF NOT EXISTS apex.market_nem
  COMMENT 'NEM (Australia) — spot prices, generation, FCAS, BESS telemetry';
CREATE SCHEMA IF NOT EXISTS apex.market_epex
  COMMENT 'EPEX (Europe) — day-ahead, intraday, EU ETS';
CREATE SCHEMA IF NOT EXISTS apex.market_ercot
  COMMENT 'ERCOT (Americas) — nodal LMP, RTC+B dispatch signals';

-- Shared schemas
CREATE SCHEMA IF NOT EXISTS apex.trading
  COMMENT 'Trade analytics layer — populated by DLT from ETRM sources';
CREATE SCHEMA IF NOT EXISTS apex.risk
  COMMENT 'VaR, stress tests, credit exposure, limit monitoring';
CREATE SCHEMA IF NOT EXISTS apex.portfolio
  COMMENT 'Revenue stacking, PPA book, asset benchmarking';
CREATE SCHEMA IF NOT EXISTS apex.reference
  COMMENT 'Counterparties, instruments, assets, traders — all three markets';
CREATE SCHEMA IF NOT EXISTS apex.ingestion
  COMMENT 'ETRM raw landing zone and sync metadata — DLT source';
CREATE SCHEMA IF NOT EXISTS apex.analytics
  COMMENT 'ML forecasts, backtest results, model metadata';
CREATE SCHEMA IF NOT EXISTS apex.genie
  COMMENT 'Pre-built Genie question sets per market and persona';
```

## DDL FILES

### data/schema/01_reference.sql

```sql
-- Market structure — all 5 markets
CREATE TABLE IF NOT EXISTS apex.reference.market_structure (
  market_id              VARCHAR(10) PRIMARY KEY,
  market_name            VARCHAR(50),
  operator               VARCHAR(50),
  dispatch_interval_min  INTEGER,
  settlement_interval_min INTEGER,
  timezone               VARCHAR(50),
  currency               VARCHAR(3),
  has_capacity_market    BOOLEAN,
  has_fcas               BOOLEAN,
  is_nodal               BOOLEAN,
  mtu_change_date        DATE COMMENT 'For EPEX: date MTU changed to 15 min',
  rtcb_live_date         DATE COMMENT 'For ERCOT: RTC+B go-live date'
);

INSERT INTO apex.reference.market_structure VALUES
('NEM',  'National Electricity Market', 'AEMO',  5,  30, 'Australia/Brisbane',  'AUD', FALSE, TRUE,  FALSE, NULL,         NULL),
('EPEX', 'European Power Exchange',     'EPEX',  60, 60, 'Europe/Paris',        'EUR', FALSE, FALSE, FALSE, '2025-09-01', NULL),
('ERCOT','Electric Reliability Council','ERCOT', 5,  15, 'America/Chicago',     'USD', FALSE, FALSE, TRUE,  NULL,         '2025-12-05'),
('ASX',  'ASX Energy Futures',          'ASX',   NULL,NULL,'Australia/Sydney',  'AUD', FALSE, FALSE, FALSE, NULL,         NULL),
('EEX',  'European Energy Exchange',    'EEX',   NULL,NULL,'Europe/Berlin',     'EUR', FALSE, FALSE, FALSE, NULL,         NULL);

-- Counterparties — all 3 markets (18 rows)
CREATE TABLE IF NOT EXISTS apex.reference.counterparties (
  counterparty_id   VARCHAR(20) PRIMARY KEY,
  name              VARCHAR(100),
  short_name        VARCHAR(20),
  counterparty_type VARCHAR(30), -- GENERATOR|RETAILER|TRADER|FINANCIAL|MARKET_OPERATOR|BANK
  market            VARCHAR(10),
  credit_rating     VARCHAR(10),
  credit_limit      DECIMAL(18,2),
  currency          VARCHAR(3),
  country           VARCHAR(10),
  is_active         BOOLEAN DEFAULT TRUE
);

-- NEM counterparties
INSERT INTO apex.reference.counterparties VALUES
('AGL','AGL Energy','AGL','GENERATOR','NEM','BBB+',50000000,'AUD','AU',TRUE),
('ORIGIN','Origin Energy','ORIGIN','RETAILER','NEM','BBB',40000000,'AUD','AU',TRUE),
('ENERGYAUST','EnergyAustralia','EA','RETAILER','NEM','BBB',35000000,'AUD','AU',TRUE),
('CSENERGY','CS Energy','CS','GENERATOR','NEM','A-',30000000,'AUD','AU',TRUE),
('STANWELL','Stanwell Corporation','STAN','GENERATOR','NEM','A',25000000,'AUD','AU',TRUE),
('NEOEN','Neoen','NEOEN','GENERATOR','NEM','BB+',20000000,'AUD','AU',TRUE),
('SNOWY','Snowy Hydro','SNOWY','GENERATOR','NEM','AA-',60000000,'AUD','AU',TRUE),
('SHELL_AUS','Shell Energy Australia','SHELL_AU','TRADER','NEM','A+',45000000,'AUD','AU',TRUE),
-- EPEX counterparties
('SHELL_EU','Shell Trading EU','SHELL_EU','TRADER','EPEX','A+',80000000,'EUR','NL',TRUE),
('TOTALENERGIES','TotalEnergies Trading','TOTAL','TRADER','EPEX','AA-',100000000,'EUR','FR',TRUE),
('AXPO','Axpo Trading','AXPO','TRADER','EPEX','A',60000000,'EUR','CH',TRUE),
('EQUINOR','Equinor Energy','EQUINOR','GENERATOR','EPEX','AA',90000000,'EUR','NO',TRUE),
('EDF','EDF Trading','EDF','GENERATOR','EPEX','BBB+',75000000,'EUR','FR',TRUE),
-- ERCOT counterparties
('VISTRA','Vistra Energy','VISTRA','GENERATOR','ERCOT','BB+',50000000,'USD','US',TRUE),
('NRG','NRG Energy','NRG','GENERATOR','ERCOT','BB',45000000,'USD','US',TRUE),
('MACQUARIE','Macquarie Energy','MAC','TRADER','ERCOT','A',70000000,'USD','US',TRUE),
('VITOL','Vitol Inc','VITOL','TRADER','ERCOT','A+',65000000,'USD','US',TRUE),
('CALPINE','Calpine Corporation','CALPINE','GENERATOR','ERCOT','BB-',40000000,'USD','US',TRUE);

-- Assets — BESS fleet across all markets
CREATE TABLE IF NOT EXISTS apex.reference.assets (
  asset_id         VARCHAR(20) PRIMARY KEY,
  asset_name       VARCHAR(100),
  asset_type       VARCHAR(30), -- BESS|GAS_CCGT|GAS_OCGT|WIND|SOLAR|HYDRO
  operator         VARCHAR(100),
  market           VARCHAR(10),
  region_id        VARCHAR(20),
  capacity_mw      DECIMAL(10,2),
  duration_hours   DECIMAL(5,2),
  variable_cost    DECIMAL(10,4),
  duid             VARCHAR(20),
  rtcb_eligible    BOOLEAN DEFAULT FALSE,
  commission_date  DATE,
  status           VARCHAR(20) DEFAULT 'ACTIVE'
);

-- NEM BESS assets
INSERT INTO apex.reference.assets VALUES
('HORNSDALE_1','Hornsdale Power Reserve','BESS','Neoen','NEM','SA1',150,1.0,0,'HPRG1',FALSE,'2017-12-01','ACTIVE'),
('HORNSDALE_2','Hornsdale Reserve Ext','BESS','Neoen','NEM','SA1',50,1.0,0,'HPRG2',FALSE,'2020-09-01','ACTIVE'),
('WARATAH_1','Waratah Super Battery','BESS','Akaysha','NEM','NSW1',850,2.0,0,'WARAB1',FALSE,'2024-06-01','ACTIVE'),
('VICTORIAN_BIG','Victorian Big Battery','BESS','Neoen','NEM','VIC1',300,2.0,0,'VBB1',FALSE,'2021-11-01','ACTIVE'),
('ERARING_BESS_1','Eraring BESS','BESS','Origin','NEM','NSW1',460,4.0,0,'ERABSS1',FALSE,'2025-03-01','ACTIVE'),
('TORRENS_BESS','Torrens Island BESS','BESS','AGL','NEM','SA1',200,2.0,0,'TRIBSS1',FALSE,'2024-01-01','ACTIVE'),
('KOORAGANG_BESS','Kooragang BESS','BESS','EnergyAustralia','NEM','NSW1',150,2.0,0,'KOOBSS1',FALSE,'2024-08-01','ACTIVE'),
('LIDDELL_BESS','Liddell BESS','BESS','AGL','NEM','NSW1',500,2.0,0,'LIDBSS1',FALSE,'2025-06-01','ACTIVE'),
-- EPEX BESS assets
('DE_BESS_1','Frankfurt Grid Battery','BESS','RWE','EPEX','DE-LU',200,2.0,0,NULL,FALSE,'2023-05-01','ACTIVE'),
('FR_BESS_1','Lyon Storage Facility','BESS','EDF','EPEX','FR',150,2.0,0,NULL,FALSE,'2023-11-01','ACTIVE'),
('GB_BESS_1','Thurrock BESS','BESS','Glencore','EPEX','GB',100,1.0,0,NULL,FALSE,'2022-09-01','ACTIVE'),
-- ERCOT BESS assets
('TX_WEST_1','West Texas Battery 1','BESS','Vistra','ERCOT','West Hub',300,4.0,0,NULL,TRUE,'2024-01-01','ACTIVE'),
('TX_WEST_2','West Texas Battery 2','BESS','NRG','ERCOT','West Hub',200,4.0,0,NULL,TRUE,'2024-06-01','ACTIVE'),
('TX_HOUSTON_1','Houston Battery 1','BESS','Calpine','ERCOT','Houston Hub',250,2.0,0,NULL,TRUE,'2023-08-01','ACTIVE'),
('TX_NORTH_1','North Texas Battery','BESS','Vistra','ERCOT','North Hub',150,2.0,0,NULL,TRUE,'2025-01-01','ACTIVE');

-- Instruments
CREATE TABLE IF NOT EXISTS apex.reference.instruments (
  instrument_id   VARCHAR(40) PRIMARY KEY,
  instrument_name VARCHAR(100),
  instrument_type VARCHAR(30), -- SPOT|FUTURES|SWAP|OPTION|CAP|PPA|BILATERAL|FCAS|DA|INTRADAY
  market          VARCHAR(10),
  region_id       VARCHAR(20),
  currency        VARCHAR(3),
  lot_size_mw     DECIMAL(10,2),
  settlement_type VARCHAR(20), -- PHYSICAL|FINANCIAL
  is_active       BOOLEAN DEFAULT TRUE
);
-- Insert NEM spot (5 regions), FCAS (7 services x 5 regions), ASX futures
-- Insert EPEX DA (8 zones), EPEX intraday (8 zones)
-- Insert ERCOT real-time (10 nodes), ERCOT DA (10 nodes)
-- Full INSERT statements: 80+ rows — generate programmatically in seeds

-- Traders
CREATE TABLE IF NOT EXISTS apex.reference.traders (
  trader_id          VARCHAR(20) PRIMARY KEY,
  name               VARCHAR(100),
  desk               VARCHAR(50),
  market             VARCHAR(10),
  email              VARCHAR(100),
  position_limit_mw  DECIMAL(10,2),
  var_limit          DECIMAL(18,2),
  currency           VARCHAR(3),
  is_active          BOOLEAN DEFAULT TRUE
);

INSERT INTO apex.reference.traders VALUES
-- NEM desk
('SCHEN','Sarah Chen','NEM Front Office','NEM','sarah.chen@apex.demo',1000,3000000,'AUD',TRUE),
('JWUU','James Wu','NEM Front Office','NEM','james.wu@apex.demo',750,2000000,'AUD',TRUE),
('EPARK','Emma Park','NEM Front Office','NEM','emma.park@apex.demo',400,1000000,'AUD',TRUE),
('ATHOMPSON','Alex Thompson','Risk','NEM','alex.thompson@apex.demo',0,0,'AUD',TRUE),
('MLEE','Morgan Lee','Portfolio','NEM','morgan.lee@apex.demo',0,0,'AUD',TRUE),
-- EPEX desk
('HMÜLLER','Hans Müller','EPEX Front Office','EPEX','hans.muller@apex.demo',800,4000000,'EUR',TRUE),
('SDUPONT','Sophie Dupont','EPEX Front Office','EPEX','sophie.dupont@apex.demo',600,3000000,'EUR',TRUE),
-- ERCOT desk
('TJOHNSON','Tyler Johnson','ERCOT Front Office','ERCOT','tyler.johnson@apex.demo',900,3500000,'USD',TRUE),
('LRODRIGUEZ','Luis Rodriguez','ERCOT Front Office','ERCOT','luis.rodriguez@apex.demo',600,2500000,'USD',TRUE);
```

### data/schema/02_market_data.sql

```sql
-- NEM prices — 5-min intervals, 5 regions
CREATE TABLE IF NOT EXISTS apex.market_nem.prices (
  interval_datetime TIMESTAMP NOT NULL,
  region_id         VARCHAR(10) NOT NULL,
  rrp               DECIMAL(12,4) COMMENT '$/MWh Regional Reference Price',
  lower6sec         DECIMAL(12,4),
  lower60sec        DECIMAL(12,4),
  lower5min         DECIMAL(12,4),
  raise6sec         DECIMAL(12,4),
  raise60sec        DECIMAL(12,4),
  raise5min         DECIMAL(12,4),
  lowerreg          DECIMAL(12,4),
  raisereg          DECIMAL(12,4),
  totaldemand       DECIMAL(12,2),
  netinterchange    DECIMAL(12,2),
  data_source       VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (region_id, interval_datetime);

-- NEM generation by fuel type
CREATE TABLE IF NOT EXISTS apex.market_nem.generation (
  interval_datetime TIMESTAMP NOT NULL,
  region_id         VARCHAR(10) NOT NULL,
  fuel_type         VARCHAR(30),
  generation_mw     DECIMAL(12,2),
  capacity_factor   DECIMAL(5,4),
  data_source       VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (region_id, interval_datetime);

-- NEM BESS telemetry — every interval per asset
CREATE TABLE IF NOT EXISTS apex.market_nem.bess_telemetry (
  asset_id               VARCHAR(20) NOT NULL,
  recorded_at            TIMESTAMP NOT NULL,
  state_of_charge_pct    DECIMAL(5,2),
  output_mw              DECIMAL(10,2) COMMENT 'positive=discharge, negative=charge',
  fcas_raise_mw          DECIMAL(10,2),
  fcas_lower_mw          DECIMAL(10,2),
  temperature_c          DECIMAL(6,2),
  cycle_count_cumulative DECIMAL(10,2),
  available_mw           DECIMAL(10,2),
  data_source            VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (asset_id, recorded_at);

-- NEM pre-dispatch forecasts
CREATE TABLE IF NOT EXISTS apex.market_nem.predispatch (
  predispatch_datetime TIMESTAMP NOT NULL,
  run_datetime         TIMESTAMP NOT NULL,
  region_id            VARCHAR(10) NOT NULL,
  forecast_rrp         DECIMAL(12,4),
  forecast_demand      DECIMAL(12,2),
  forecast_raise5min   DECIMAL(12,4),
  data_source          VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (region_id, predispatch_datetime);

-- NEM forward curves (ASX futures)
CREATE TABLE IF NOT EXISTS apex.market_nem.forward_curves (
  curve_date    DATE NOT NULL,
  instrument_id VARCHAR(40) NOT NULL,
  region_id     VARCHAR(10) NOT NULL,
  tenor         VARCHAR(20) NOT NULL,
  price         DECIMAL(12,4),
  bid           DECIMAL(12,4),
  offer         DECIMAL(12,4),
  volume        DECIMAL(14,2),
  data_source   VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (region_id, curve_date);

-- EPEX day-ahead prices
-- MTU is 60 before 2025-09-01, 15 after — enforced by simulator
CREATE TABLE IF NOT EXISTS apex.market_epex.prices (
  delivery_datetime TIMESTAMP NOT NULL,
  bidding_zone      VARCHAR(20) NOT NULL,
  price_eur_mwh     DECIMAL(12,4),
  volume_mwh        DECIMAL(14,4),
  mtu_minutes       INTEGER,
  auction_type      VARCHAR(20) DEFAULT 'DAY_AHEAD', -- DAY_AHEAD|INTRADAY
  data_source       VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (bidding_zone, delivery_datetime);

-- EPEX forward curves
CREATE TABLE IF NOT EXISTS apex.market_epex.forward_curves (
  curve_date    DATE NOT NULL,
  product       VARCHAR(30) NOT NULL, -- CAL_2026, Q1_2026, M01_2026 etc
  bidding_zone  VARCHAR(20) NOT NULL,
  price_eur_mwh DECIMAL(12,4),
  bid           DECIMAL(12,4),
  offer         DECIMAL(12,4),
  data_source   VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (bidding_zone, curve_date);

-- EPEX BESS telemetry
CREATE TABLE IF NOT EXISTS apex.market_epex.bess_telemetry (
  asset_id            VARCHAR(20) NOT NULL,
  recorded_at         TIMESTAMP NOT NULL,
  state_of_charge_pct DECIMAL(5,2),
  output_mw           DECIMAL(10,2),
  available_mw        DECIMAL(10,2),
  data_source         VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (asset_id, recorded_at);

-- ERCOT real-time LMP — nodal
CREATE TABLE IF NOT EXISTS apex.market_ercot.lmp (
  interval_datetime    TIMESTAMP NOT NULL,
  node_id              VARCHAR(50) NOT NULL,
  lmp                  DECIMAL(12,4),
  energy_component     DECIMAL(12,4),
  congestion_component DECIMAL(12,4),
  loss_component       DECIMAL(12,4),
  rtcb_signal          DECIMAL(10,4) COMMENT 'NULL before 2025-12-05',
  data_source          VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (node_id, interval_datetime);

-- ERCOT day-ahead
CREATE TABLE IF NOT EXISTS apex.market_ercot.dam_prices (
  delivery_datetime TIMESTAMP NOT NULL,
  node_id           VARCHAR(50) NOT NULL,
  dam_lmp           DECIMAL(12,4),
  data_source       VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (node_id, delivery_datetime);

-- ERCOT BESS telemetry
CREATE TABLE IF NOT EXISTS apex.market_ercot.bess_telemetry (
  asset_id            VARCHAR(20) NOT NULL,
  recorded_at         TIMESTAMP NOT NULL,
  state_of_charge_pct DECIMAL(5,2),
  output_mw           DECIMAL(10,2),
  rtcb_signal         DECIMAL(10,4) COMMENT 'NULL before 2025-12-05',
  available_mw        DECIMAL(10,2),
  data_source         VARCHAR(20) DEFAULT 'SIMULATED'
) CLUSTER BY (asset_id, recorded_at);
```

### data/schema/03_trading.sql

```sql
-- ETRM ingestion landing zone
CREATE TABLE IF NOT EXISTS apex.ingestion.raw_etrm_trades (
  raw_id        BIGINT GENERATED ALWAYS AS IDENTITY,
  source_system VARCHAR(30) NOT NULL, -- ENDUR_SIM|ALIGNE_SIM|TRIPLE_POINT_SIM
  market        VARCHAR(10) NOT NULL,
  payload       STRING COMMENT 'JSON blob as-received from simulated ETRM',
  received_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed     BOOLEAN DEFAULT FALSE
) CLUSTER BY (market, received_at);

-- ETRM sync log
CREATE TABLE IF NOT EXISTS apex.ingestion.etrm_sync_log (
  sync_id        VARCHAR(36) DEFAULT gen_random_uuid(),
  source_system  VARCHAR(30),
  market         VARCHAR(10),
  entity_type    VARCHAR(30), -- TRADE|POSITION|CURVE|REFERENCE
  records_synced INTEGER,
  sync_started   TIMESTAMP,
  sync_completed TIMESTAMP,
  status         VARCHAR(20) DEFAULT 'SUCCESS',
  error_message  TEXT
) CLUSTER BY (market, sync_started);

-- Trades analytics table — populated by DLT from raw_etrm_trades
-- NOT written to directly by the application
CREATE TABLE IF NOT EXISTS apex.trading.trades (
  trade_id        VARCHAR(36) NOT NULL,
  trade_timestamp TIMESTAMP,
  instrument_id   VARCHAR(40),
  counterparty_id VARCHAR(20),
  trader_id       VARCHAR(20),
  direction       VARCHAR(4) CHECK (direction IN ('BUY','SELL')),
  volume_mw       DECIMAL(10,2),
  price           DECIMAL(12,4),
  delivery_start  TIMESTAMP,
  delivery_end    TIMESTAMP,
  trade_type      VARCHAR(20), -- SPOT|BILATERAL|FUTURES|SWAP|CAP|PPA|FCAS_OFFER|DA|RT
  market          VARCHAR(10),
  region_id       VARCHAR(20),
  status          VARCHAR(20),
  source_system   VARCHAR(30) COMMENT 'ETRM source system',
  ingested_at     TIMESTAMP   COMMENT 'When DLT wrote this record',
  notes           TEXT
) CLUSTER BY (market, trader_id, trade_timestamp);

-- Positions analytics table — gold layer from DLT
CREATE TABLE IF NOT EXISTS apex.trading.positions (
  position_id         VARCHAR(36) DEFAULT gen_random_uuid(),
  instrument_id       VARCHAR(40),
  region_id           VARCHAR(20),
  trader_id           VARCHAR(20),
  market              VARCHAR(10),
  delivery_period     VARCHAR(20),
  net_volume_mw       DECIMAL(12,2),
  avg_price           DECIMAL(12,4),
  total_volume_mw     DECIMAL(12,2),
  current_market_price DECIMAL(12,4),
  mtm_pnl             DECIMAL(18,4),
  currency            VARCHAR(3),
  source_system       VARCHAR(30),
  last_updated        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_position UNIQUE (instrument_id, region_id, trader_id, market, delivery_period)
) CLUSTER BY (market, trader_id);

-- Daily P&L
CREATE TABLE IF NOT EXISTS apex.trading.pnl_daily (
  pnl_date        DATE NOT NULL,
  trader_id       VARCHAR(20),
  market          VARCHAR(10),
  region_id       VARCHAR(20),
  instrument_type VARCHAR(30),
  realised_pnl    DECIMAL(18,4),
  unrealised_pnl  DECIMAL(18,4),
  total_pnl       DECIMAL(18,4),
  currency        VARCHAR(3),
  trade_count     INTEGER,
  volume_traded_mw DECIMAL(12,2),
  PRIMARY KEY (pnl_date, trader_id, market, region_id, instrument_type)
);

-- Offer stacks — written to Lakebase, then synced to Delta
CREATE TABLE IF NOT EXISTS apex.trading.offer_stacks (
  stack_id          VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  asset_id          VARCHAR(20) NOT NULL,
  market            VARCHAR(10) NOT NULL,
  service_type      VARCHAR(30) NOT NULL,
  dispatch_interval TIMESTAMP NOT NULL,
  submission_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status            VARCHAR(20) DEFAULT 'DRAFT',
  submitted_by      VARCHAR(100),
  rebid_reason      TEXT,
  is_rebid          BOOLEAN DEFAULT FALSE,
  original_stack_id VARCHAR(36)
);

CREATE TABLE IF NOT EXISTS apex.trading.offer_bands (
  band_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  stack_id     VARCHAR(36) NOT NULL,
  band_number  INTEGER NOT NULL CHECK (band_number BETWEEN 1 AND 10),
  price_per_mwh DECIMAL(12,4) NOT NULL,
  volume_mw    DECIMAL(10,2) NOT NULL,
  dispatched_mw DECIMAL(10,2) DEFAULT 0,
  UNIQUE (stack_id, band_number)
);

-- Dispatch recommendations
CREATE TABLE IF NOT EXISTS apex.trading.dispatch_recommendations (
  recommendation_id  VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  asset_id           VARCHAR(20) NOT NULL,
  market             VARCHAR(10) NOT NULL,
  dispatch_interval  TIMESTAMP NOT NULL,
  recommended_mw     DECIMAL(10,2),
  recommended_price  DECIMAL(12,4),
  service_type       VARCHAR(30),
  confidence_score   DECIMAL(5,4),
  model_version      VARCHAR(50),
  expected_revenue   DECIMAL(14,4),
  currency           VARCHAR(3),
  rationale          TEXT,
  generated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  accepted           BOOLEAN,
  accepted_by        VARCHAR(100),
  accepted_at        TIMESTAMP
);
```

### data/schema/04_risk.sql

```sql
CREATE TABLE IF NOT EXISTS apex.risk.var_results (
  var_id               VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  calculation_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  trader_id            VARCHAR(20),
  market               VARCHAR(10),
  portfolio_scope      VARCHAR(50) DEFAULT 'FULL',
  var_95               DECIMAL(18,4),
  var_99               DECIMAL(18,4),
  cvar_95              DECIMAL(18,4),
  cvar_99              DECIMAL(18,4),
  position_value       DECIMAL(18,4),
  currency             VARCHAR(3),
  simulation_count     INTEGER DEFAULT 10000,
  price_vol_1day       DECIMAL(10,6),
  method               VARCHAR(20) DEFAULT 'MONTE_CARLO'
);

CREATE TABLE IF NOT EXISTS apex.risk.stress_test_scenarios (
  scenario_id       VARCHAR(30) PRIMARY KEY,
  scenario_name     VARCHAR(100),
  description       TEXT,
  market            VARCHAR(10),
  price_shock_pct   DECIMAL(6,4),
  demand_shock_pct  DECIMAL(6,4),
  volume_shock_pct  DECIMAL(6,4),
  region_id         VARCHAR(20),
  reference_event   VARCHAR(100)
);

-- NEM scenarios
INSERT INTO apex.risk.stress_test_scenarios VALUES
('NEM_SA_SPIKE','SA June 2025 Spike','SA1 extreme price event','NEM',4.00,-0.05,0.0,'SA1','June 26 2025 NEM SA event'),
('NEM_AUG_SPIKE','NEM-Wide August 2025','Multi-region price spike','NEM',2.00,-0.10,0.0,NULL,'5 Aug 2025 NEM-wide spike'),
('NEM_SOLAR_CANNIB','Solar Cannibalism Extreme','Summer midday negative prices','NEM',-0.80,-0.15,0.0,'QLD1','Solar saturation event'),
('NEM_COAL_OUTAGE','Coal Outage Winter','Major coal unit failure VIC/NSW','NEM',1.50,0.10,-0.20,'VIC1','Loy Yang A unit trip'),
('NEM_INTERCON_TRIP','SA Islanding Event','SA interconnector trip','NEM',3.00,0.05,0.0,'SA1','Heywood interconnector trip'),
-- EPEX scenarios
('EPEX_COLD_SNAP','European Cold Snap','Extended cold weather demand spike','EPEX',1.20,0.25,-0.10,'DE-LU','Jan 2025 cold snap'),
('EPEX_NEGATIVE_FLOOD','Renewable Flood','Excess wind+solar negative prices','EPEX',-0.60,-0.20,0.0,'DE-LU','April 2025 renewables surplus'),
('EPEX_GAS_CRISIS','Gas Supply Disruption','Gas price shock affecting thermal','EPEX',0.80,0.15,-0.30,NULL,'Supply disruption scenario'),
-- ERCOT scenarios
('ERCOT_SUMMER_PEAK','ERCOT Summer Scarcity','Peak demand price spike','ERCOT',1.80,0.30,-0.15,'West Hub','Aug 2025 scarcity event'),
('ERCOT_WIND_DROP','Wind Generation Drop','Panhandle wind calm event','ERCOT',1.40,0.10,-0.40,'West Hub','Low wind scarcity');

CREATE TABLE IF NOT EXISTS apex.risk.stress_test_results (
  result_id              VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  scenario_id            VARCHAR(30),
  run_datetime           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  trader_id              VARCHAR(20),
  market                 VARCHAR(10),
  portfolio_pnl_impact   DECIMAL(18,4),
  worst_case_pnl         DECIMAL(18,4),
  best_case_pnl          DECIMAL(18,4),
  positions_breached     INTEGER,
  currency               VARCHAR(3)
);

CREATE TABLE IF NOT EXISTS apex.risk.credit_exposure (
  exposure_id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  counterparty_id           VARCHAR(20),
  market                    VARCHAR(10),
  calculation_date          DATE DEFAULT CURRENT_DATE,
  mark_to_market            DECIMAL(18,4),
  potential_future_exposure DECIMAL(18,4),
  total_exposure            DECIMAL(18,4),
  credit_limit              DECIMAL(18,4),
  utilisation_pct           DECIMAL(6,4),
  currency                  VARCHAR(3),
  is_breach                 BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS apex.risk.trading_limits (
  limit_id       VARCHAR(30) PRIMARY KEY,
  trader_id      VARCHAR(20),
  market         VARCHAR(10),
  limit_type     VARCHAR(30), -- POSITION_MW|VAR|LOSS|CREDIT
  limit_value    DECIMAL(18,4),
  current_value  DECIMAL(18,4),
  utilisation_pct DECIMAL(6,4),
  currency       VARCHAR(3),
  is_breach      BOOLEAN DEFAULT FALSE,
  breach_timestamp TIMESTAMP,
  last_updated   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### data/schema/05_portfolio.sql

```sql
CREATE TABLE IF NOT EXISTS apex.portfolio.ppa_book (
  ppa_id          VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  ppa_name        VARCHAR(100),
  counterparty_id VARCHAR(20),
  asset_id        VARCHAR(20),
  market          VARCHAR(10),
  direction       VARCHAR(5) CHECK (direction IN ('LONG','SHORT')),
  contracted_mw   DECIMAL(10,2),
  strike_price    DECIMAL(12,4),
  start_date      DATE,
  end_date        DATE,
  indexation_type VARCHAR(20),
  settlement_type VARCHAR(20),
  currency        VARCHAR(3),
  current_mark    DECIMAL(12,4),
  mtm_value       DECIMAL(18,4),
  status          VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS apex.portfolio.revenue_actuals (
  asset_id              VARCHAR(20) NOT NULL,
  revenue_date          DATE NOT NULL,
  market                VARCHAR(10) NOT NULL,
  energy_revenue        DECIMAL(14,4),
  fcas_raise_revenue    DECIMAL(14,4),
  fcas_lower_revenue    DECIMAL(14,4),
  cap_revenue           DECIMAL(14,4),
  rtcb_revenue          DECIMAL(14,4) COMMENT 'ERCOT RTC+B revenue — NULL before 2025-12-05',
  total_revenue         DECIMAL(14,4),
  revenue_per_mw        DECIMAL(12,4),
  currency              VARCHAR(3),
  PRIMARY KEY (asset_id, revenue_date, market)
);

CREATE TABLE IF NOT EXISTS apex.portfolio.revenue_forecast (
  asset_id              VARCHAR(20) NOT NULL,
  forecast_date         DATE NOT NULL,
  market                VARCHAR(10) NOT NULL,
  energy_revenue_forecast DECIMAL(14,4),
  fcas_revenue_forecast DECIMAL(14,4),
  total_revenue_forecast DECIMAL(14,4),
  scenario              VARCHAR(30) DEFAULT 'BASE',
  confidence_low        DECIMAL(14,4),
  confidence_high       DECIMAL(14,4),
  currency              VARCHAR(3),
  PRIMARY KEY (asset_id, forecast_date, market, scenario)
);
```

### data/schema/06_analytics.sql

```sql
CREATE TABLE IF NOT EXISTS apex.analytics.price_forecasts (
  forecast_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  market           VARCHAR(10),
  region_id        VARCHAR(20),
  forecast_datetime TIMESTAMP,
  horizon          VARCHAR(20), -- 5MIN|30MIN|4HR|DAY_AHEAD
  forecast_price   DECIMAL(12,4),
  confidence_low   DECIMAL(12,4),
  confidence_high  DECIMAL(12,4),
  currency         VARCHAR(3),
  model_version    VARCHAR(50),
  mape             DECIMAL(8,6),
  run_datetime     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex.analytics.backtest_runs (
  run_id          VARCHAR(36) DEFAULT gen_random_uuid() PRIMARY KEY,
  strategy_name   VARCHAR(100),
  description     TEXT,
  market          VARCHAR(10),
  region_id       VARCHAR(20),
  start_date      DATE,
  end_date        DATE,
  total_pnl       DECIMAL(18,4),
  sharpe_ratio    DECIMAL(10,6),
  max_drawdown    DECIMAL(18,4),
  win_rate        DECIMAL(5,4),
  total_trades    INTEGER,
  currency        VARCHAR(3),
  run_datetime    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  run_by          VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS apex.analytics.backtest_trades (
  bt_trade_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id        VARCHAR(36),
  trade_datetime TIMESTAMP,
  direction     VARCHAR(4),
  volume_mw     DECIMAL(10,2),
  entry_price   DECIMAL(12,4),
  exit_price    DECIMAL(12,4),
  pnl           DECIMAL(14,4),
  signal_name   VARCHAR(100),
  signal_value  DECIMAL(12,6)
);
```

### data/schema/07_genie.sql

```sql
-- Pre-built Genie questions per market and persona
CREATE TABLE IF NOT EXISTS apex.genie.questions (
  question_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  market       VARCHAR(10) NOT NULL,
  persona      VARCHAR(20) NOT NULL,
  question     TEXT NOT NULL,
  category     VARCHAR(50),
  sort_order   INTEGER DEFAULT 0
);
-- Populated by W19 seed script
```

## STEP 2: Execute all DDL in order 01 through 07 via Databricks CLI MCP.
Verify each schema and table with SELECT COUNT(*).

## SUCCESS CRITERIA
1. All 9 schemas exist in apex catalog
2. apex.market_ercot.lmp has rtcb_signal column
3. apex.trading.trades has source_system and ingested_at columns
4. apex.risk.stress_test_scenarios has 10 rows (5 NEM + 3 EPEX + 2 ERCOT)
5. apex.reference.assets has 15 rows across 3 markets
6. apex.reference.counterparties has 18 rows
7. apex.reference.market_structure has 5 rows
8. All CLUSTER BY clauses on time-series tables

## COMPLETION ARTIFACT
completions/W02-schema.md
Commit: "feat: W02 complete — multi-market schema"

---

# W02b — ETRM Ingestion DLT Pipeline

## PREREQUISITE CHECK
Verify completions/W02-schema.md exists.

## OBJECTIVE
Build the DLT pipeline that simulates ingestion from upstream ETRM systems into Databricks. This is the **key architectural story**: Databricks reads from the ETRM; Databricks is not the ETRM. The pipeline provides bronze → silver → gold lineage visible in the Databricks UI.

## FILE: app/pipelines/etrm_ingestion.py

```python
"""
APEX ETRM Ingestion Pipeline
Simulates ingestion from: ALIGNE_SIM (NEM), ENDUR_SIM (EPEX), TRIPLE_POINT_SIM (ERCOT)
Runs continuously — new records arrive from market simulators.
"""
import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

# ── BRONZE: Raw landing from simulated ETRM ──────────────────────

@dlt.table(
  name="bronze_etrm_trades",
  comment="Raw trade payloads as received from upstream ETRM systems (Aligne/Endur/Triple Point)",
  table_properties={"quality": "bronze", "pipelines.reset.allowed": "true"}
)
def bronze_etrm_trades():
    return (
        spark.readStream
            .format("delta")
            .option("ignoreChanges", "true")
            .table("apex.ingestion.raw_etrm_trades")
            .filter("processed = FALSE")
    )

@dlt.table(
  name="bronze_market_prices_nem",
  comment="Raw NEM price records from simulator",
  table_properties={"quality": "bronze"}
)
def bronze_nem_prices():
    return spark.readStream.format("delta").table("apex.market_nem.prices")

@dlt.table(
  name="bronze_market_prices_epex",
  comment="Raw EPEX price records from simulator",
  table_properties={"quality": "bronze"}
)
def bronze_epex_prices():
    return spark.readStream.format("delta").table("apex.market_epex.prices")

@dlt.table(
  name="bronze_market_prices_ercot",
  comment="Raw ERCOT LMP records from simulator",
  table_properties={"quality": "bronze"}
)
def bronze_ercot_lmp():
    return spark.readStream.format("delta").table("apex.market_ercot.lmp")

# ── SILVER: Parsed, validated, enriched ──────────────────────────

@dlt.table(
  name="silver_trades",
  comment="Validated and parsed trades from all ETRM sources",
  table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_direction",  "direction IN ('BUY', 'SELL')")
@dlt.expect_or_drop("positive_volume",  "volume_mw > 0")
@dlt.expect_or_drop("valid_market",     "market IN ('NEM', 'EPEX', 'ERCOT')")
@dlt.expect_or_drop("valid_price",      "price > -1000 AND price < 20000")
@dlt.expect_or_drop("delivery_ordering","delivery_end > delivery_start")
def silver_trades():
    return (
        dlt.read_stream("bronze_etrm_trades")
            .select(
                F.get_json_object("payload", "$.trade_id").alias("trade_id"),
                F.get_json_object("payload", "$.market").alias("market"),
                F.get_json_object("payload", "$.direction").alias("direction"),
                F.get_json_object("payload", "$.volume_mw").cast(DecimalType(10,2)).alias("volume_mw"),
                F.get_json_object("payload", "$.price").cast(DecimalType(12,4)).alias("price"),
                F.get_json_object("payload", "$.instrument_id").alias("instrument_id"),
                F.get_json_object("payload", "$.counterparty_id").alias("counterparty_id"),
                F.get_json_object("payload", "$.trader_id").alias("trader_id"),
                F.get_json_object("payload", "$.region_id").alias("region_id"),
                F.get_json_object("payload", "$.trade_type").alias("trade_type"),
                F.get_json_object("payload", "$.status").alias("status"),
                F.to_timestamp(F.get_json_object("payload", "$.trade_timestamp")).alias("trade_timestamp"),
                F.to_timestamp(F.get_json_object("payload", "$.delivery_start")).alias("delivery_start"),
                F.to_timestamp(F.get_json_object("payload", "$.delivery_end")).alias("delivery_end"),
                F.col("source_system"),
                F.col("received_at").alias("ingested_at")
            )
    )

@dlt.table(
  name="silver_nem_prices_enriched",
  comment="NEM prices with derived fields (is_spike, is_negative, fcas_total)",
  table_properties={"quality": "silver"}
)
def silver_nem_prices():
    return (
        dlt.read_stream("bronze_market_prices_nem")
            .withColumn("is_spike", F.col("rrp") > 1000)
            .withColumn("is_negative", F.col("rrp") < 0)
            .withColumn("fcas_total", F.col("raise6sec") + F.col("lower6sec") +
                        F.col("raise5min") + F.col("lower5min") +
                        F.col("raisereg") + F.col("lowerreg"))
    )

# ── GOLD: Analytics-ready, Genie queryable ───────────────────────

@dlt.table(
  name="gold_positions",
  comment="Net positions aggregated from validated trades — analytics system of record. Genie queryable.",
  table_properties={"quality": "gold", "pipelines.autoOptimize.managed": "true"}
)
def gold_positions():
    trades = dlt.read("silver_trades").filter("status IN ('CONFIRMED', 'PARTIALLY_FILLED')")
    return (
        trades
            .groupBy(
                "instrument_id", "region_id", "trader_id", "market",
                F.concat(
                    F.year("delivery_start").cast("string"),
                    F.lit("-Q"),
                    F.quarter("delivery_start").cast("string")
                ).alias("delivery_period")
            )
            .agg(
                F.sum(
                    F.when(F.col("direction") == "BUY", F.col("volume_mw"))
                     .otherwise(-F.col("volume_mw"))
                ).alias("net_volume_mw"),
                F.avg("price").alias("avg_price"),
                F.sum("volume_mw").alias("total_volume_mw"),
                F.max("source_system").alias("source_system"),
                F.max("ingested_at").alias("last_sync_at"),
                F.count("*").alias("trade_count")
            )
    )

@dlt.table(
  name="gold_pnl_daily",
  comment="Daily P&L aggregation across all markets — Genie queryable",
  table_properties={"quality": "gold"}
)
def gold_pnl_daily():
    return (
        dlt.read("silver_trades")
            .filter("status IN ('CONFIRMED', 'PARTIALLY_FILLED')")
            .groupBy(
                F.to_date("trade_timestamp").alias("pnl_date"),
                "trader_id", "market", "region_id", "trade_type"
            )
            .agg(
                F.count("*").alias("trade_count"),
                F.sum("volume_mw").alias("volume_traded_mw")
            )
    )

@dlt.table(
  name="gold_market_summary",
  comment="Latest price summary per market — Genie queryable",
  table_properties={"quality": "gold"}
)
def gold_market_summary():
    """Unified price summary across all 3 markets for cross-market queries."""
    nem = (dlt.read("silver_nem_prices_enriched")
               .groupBy("region_id")
               .agg(F.last("rrp").alias("last_price"),
                    F.avg("rrp").alias("avg_24h"),
                    F.max("rrp").alias("max_24h"))
               .withColumn("market", F.lit("NEM"))
               .withColumn("currency", F.lit("AUD")))
    return nem  # EPEX and ERCOT joined similarly
```

## FILE: resources/pipelines.yml

```yaml
pipelines:
  etrm_ingestion:
    name: apex-etrm-ingestion
    target: apex
    catalog: apex
    libraries:
      - notebook:
          path: /app/pipelines/etrm_ingestion
    continuous: true
    channel: CURRENT
    development: false
    clusters:
      - label: default
        autoscale:
          min_workers: 1
          max_workers: 4
          mode: ENHANCED
    configuration:
      pipelines.enableTrackHistory: "true"
```

## SUCCESS CRITERIA
1. DLT pipeline visible in Databricks UI with bronze/silver/gold lineage graph
2. Writing one row to apex.ingestion.raw_etrm_trades propagates to gold_positions within 60s
3. DLT expectation on valid_direction rejects 'HOLD' — verify quarantine table
4. silver_trades shows correct field parsing from JSON payload
5. gold_positions shows correct net_volume_mw: BUY 100MW + SELL 40MW = +60MW net
6. Pipeline status: RUNNING continuously (not triggered)

## COMPLETION ARTIFACT
completions/W02b-dlt-ingestion.md
Commit: "feat: W02b complete — ETRM ingestion DLT pipeline"

---

# W03–W03d — Continuous Market Data Simulators

## PREREQUISITE CHECK
Verify completions/W02-schema.md exists.

## OBJECTIVE
Build always-on market data simulators for all three markets. These are NOT one-time backfill scripts — they write continuously while the app is running, making prices, SOC, and forecasts update live on screen. Backfill scripts run once to populate historical data.

---

## FILE: data/seeds/market/simulators/nem_simulator.py

```python
"""
NEM Continuous Simulator
Writes to: apex.market_nem.prices, apex.market_nem.bess_telemetry,
           apex.market_nem.generation, apex.market_nem.predispatch
Interval: 30 seconds (simulates 5-min dispatch intervals)
"""
import time, random, logging, json
from decimal import Decimal
from datetime import datetime, timedelta
from databricks.connect import DatabricksSession
from pyspark.sql import Row

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nem_simulator")

spark = DatabricksSession.builder.profile("fe-vm").getOrCreate()

REGIONS = ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]
BASE_PRICES = {"QLD1": 80, "NSW1": 90, "VIC1": 95, "SA1": 110, "TAS1": 75}
BASE_DEMAND  = {"QLD1": 7200, "NSW1": 9800, "VIC1": 6400, "SA1": 1900, "TAS1": 1200}

NEM_ASSETS = [
    "HORNSDALE_1","HORNSDALE_2","WARATAH_1","VICTORIAN_BIG",
    "ERARING_BESS_1","TORRENS_BESS","KOORAGANG_BESS","LIDDELL_BESS"
]
ASSET_CAPACITIES = {
    "HORNSDALE_1": 150, "HORNSDALE_2": 50, "WARATAH_1": 850,
    "VICTORIAN_BIG": 300, "ERARING_BESS_1": 460, "TORRENS_BESS": 200,
    "KOORAGANG_BESS": 150, "LIDDELL_BESS": 500
}

prev_prices = dict(BASE_PRICES)
asset_soc = {a: random.uniform(30, 80) for a in NEM_ASSETS}

def hour_factor(hour: int) -> float:
    if hour in [17, 18, 19, 20]: return 1.35   # evening peak
    if hour in [11, 12, 13]:     return 0.82   # solar midday dip
    if hour in [2, 3, 4]:        return 0.70   # overnight trough
    return 1.0

def seasonal_factor(month: int) -> float:
    return 1.20 if month in [12, 1, 2] else (0.92 if month in [6, 7, 8] else 1.0)

def generate_nem_price(region: str, now: datetime) -> dict:
    base = BASE_PRICES[region]
    factor = hour_factor(now.hour) * seasonal_factor(now.month)
    mean_rev = prev_prices[region] * 0.65 + base * factor * 0.35
    noise = random.gauss(0, base * 0.10)
    price = mean_rev + noise

    # Spike event (0.3% probability)
    is_spike = random.random() < 0.003
    if is_spike:
        price = random.uniform(3000, 15200)

    # Negative prices: summer midday QLD/SA/VIC
    if (now.month in [12, 1, 2] and 10 <= now.hour <= 14
            and region in ["QLD1", "SA1", "VIC1"] and random.random() < 0.07):
        price = random.uniform(-200, -5)

    # FCAS pricing — spikes when contingency
    raise6sec = random.gauss(8, 3) * (20 if is_spike else 1)
    lower6sec  = random.gauss(4, 2) * (10 if is_spike else 1)
    raisereg   = random.gauss(12, 4)
    lowerreg   = random.gauss(6, 2)

    prev_prices[region] = float(price) if abs(float(price)) < 3000 else prev_prices[region]

    return {
        "interval_datetime": now,
        "region_id": region,
        "rrp": round(price, 4),
        "raise6sec": round(max(0, raise6sec), 4),
        "lower6sec": round(max(0, lower6sec), 4),
        "raise60sec": round(max(0, raise6sec * 0.7), 4),
        "lower60sec": round(max(0, lower6sec * 0.7), 4),
        "raise5min": round(max(0, raise6sec * 0.5), 4),
        "lower5min": round(max(0, lower6sec * 0.5), 4),
        "raisereg": round(max(0, raisereg), 4),
        "lowerreg": round(max(0, lowerreg), 4),
        "totaldemand": round(BASE_DEMAND[region] + random.gauss(0, BASE_DEMAND[region]*0.05), 2),
        "netinterchange": round(random.gauss(0, 200), 2),
        "data_source": "SIMULATED"
    }

def update_bess_soc(asset_id: str, price: float, now: datetime) -> dict:
    soc = asset_soc[asset_id]
    cap = ASSET_CAPACITIES[asset_id]
    # Dispatch logic: high price → discharge, low price → charge
    if price > 150 and soc > 20:
        output_mw = cap * random.uniform(0.6, 0.95)
        soc -= (output_mw / cap) * 2  # simplified SOC depletion
    elif price < 60 and soc < 85:
        output_mw = -cap * random.uniform(0.4, 0.80)
        soc += (abs(output_mw) / cap) * 2
    else:
        output_mw = random.gauss(0, cap * 0.05)
    soc = max(5, min(98, soc))
    asset_soc[asset_id] = soc
    return {
        "asset_id": asset_id,
        "recorded_at": now,
        "state_of_charge_pct": round(soc, 2),
        "output_mw": round(output_mw, 2),
        "fcas_raise_mw": round(max(0, cap * 0.10 * (soc / 100)), 2),
        "fcas_lower_mw": round(max(0, cap * 0.10 * ((100 - soc) / 100)), 2),
        "temperature_c": round(random.gauss(28, 4), 2),
        "cycle_count_cumulative": round(random.uniform(100, 800), 2),
        "available_mw": round(cap * (soc / 100) * 0.95, 2),
        "data_source": "SIMULATED"
    }

def write_to_delta(rows: list, table: str):
    df = spark.createDataFrame([Row(**r) for r in rows])
    df.write.mode("append").saveAsTable(table)

def run_nem_simulator(interval_seconds: int = 30):
    logger.info("NEM simulator starting")
    while True:
        try:
            now = datetime.utcnow()
            price_rows, bess_rows, predispatch_rows = [], [], []

            for region in REGIONS:
                price_rows.append(generate_nem_price(region, now))

            # BESS telemetry — use SA1 price for SA assets, NSW1 for NSW, etc.
            region_map = {
                "HORNSDALE_1":"SA1","HORNSDALE_2":"SA1","TORRENS_BESS":"SA1",
                "WARATAH_1":"NSW1","ERARING_BESS_1":"NSW1","KOORAGANG_BESS":"NSW1","LIDDELL_BESS":"NSW1",
                "VICTORIAN_BIG":"VIC1"
            }
            avg_price = sum(r["rrp"] for r in price_rows) / len(price_rows)
            for asset in NEM_ASSETS:
                asset_price = next((r["rrp"] for r in price_rows
                                    if r["region_id"] == region_map.get(asset, "NSW1")), avg_price)
                bess_rows.append(update_bess_soc(asset, float(asset_price), now))

            # Pre-dispatch: generate 12 forward forecasts
            for i in range(1, 13):
                future = now + timedelta(minutes=i * 5)
                for region in REGIONS:
                    base_rrp = next(r["rrp"] for r in price_rows if r["region_id"] == region)
                    predispatch_rows.append({
                        "predispatch_datetime": future,
                        "run_datetime": now,
                        "region_id": region,
                        "forecast_rrp": round(float(base_rrp) * random.uniform(0.85, 1.15), 4),
                        "forecast_demand": round(BASE_DEMAND[region] * random.uniform(0.97, 1.03), 2),
                        "forecast_raise5min": round(max(0, random.gauss(8, 3)), 4),
                        "data_source": "SIMULATED"
                    })

            write_to_delta(price_rows,      "apex.market_nem.prices")
            write_to_delta(bess_rows,       "apex.market_nem.bess_telemetry")
            write_to_delta(predispatch_rows,"apex.market_nem.predispatch")
            logger.info(f"NEM: wrote {len(price_rows)} prices, {len(bess_rows)} BESS, {len(predispatch_rows)} predispatch")

        except Exception as e:
            logger.error(f"NEM simulator error: {e}")
        time.sleep(interval_seconds)
```

---

## FILE: data/seeds/market/simulators/epex_simulator.py

```python
"""
EPEX Continuous Simulator
Writes to: apex.market_epex.prices, apex.market_epex.bess_telemetry,
           apex.market_epex.forward_curves
Interval: 300 seconds (simulates day-ahead auction cycle — each run = one new hour slot)
MTU: 60 min before 2025-09-01, 15 min after
"""
import time, random, logging
from datetime import datetime, date, timedelta, time as dtime
from databricks.connect import DatabricksSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("epex_simulator")
spark = DatabricksSession.builder.profile("fe-vm").getOrCreate()

ZONES = ["DE-LU", "FR", "BE", "NL", "ES", "NO1", "NO2", "CH"]
BASE_PRICES_EUR = {"DE-LU": 70, "FR": 68, "BE": 72, "NL": 73, "ES": 65,
                   "NO1": 48, "NO2": 44, "CH": 62}
EPEX_ASSETS = ["DE_BESS_1", "FR_BESS_1", "GB_BESS_1"]

MTU_CHANGE_DATE = date(2025, 9, 1)
prev_prices_eur = dict(BASE_PRICES_EUR)
epex_soc = {a: random.uniform(30, 75) for a in EPEX_ASSETS}

def get_mtu(d: date) -> int:
    return 15 if d >= MTU_CHANGE_DATE else 60

def generate_epex_price(zone: str, delivery_dt: datetime, mtu: int) -> dict:
    base = BASE_PRICES_EUR[zone]
    hour = delivery_dt.hour
    solar_zones = ["DE-LU", "ES", "FR"]
    wind_zones  = ["NO1", "NO2"]

    # Duck curve for solar zones
    solar_dip  = -28 if (zone in solar_zones and 10 <= hour <= 14) else 0
    # Evening ramp
    evening    = 22  if 17 <= hour <= 21 else 0
    # Weekend reduction
    weekday    = delivery_dt.weekday()
    weekend    = -10 if weekday >= 5 else 0
    # Hydro zones are flatter
    hydro_flat = 0.4 if zone in wind_zones else 1.0

    noise = random.gauss(0, base * 0.07)
    price = (base + solar_dip + evening + weekend + noise) * hydro_flat

    # Negative prices: DE-LU and ES on Sunday mornings high solar
    if zone in ["DE-LU", "ES"] and 9 <= hour <= 14 and weekday == 6:
        if random.random() < 0.06:
            price = random.uniform(-60, -5)

    # EU ETS carbon cost floor for thermal-heavy zones
    if zone in ["DE-LU", "BE", "NL"] and price > 0:
        price = max(price, 25)  # carbon floor ~€25/MWh thermal dispatch floor

    prev_prices_eur[zone] = float(price) if price > -100 else prev_prices_eur[zone]

    return {
        "delivery_datetime": delivery_dt,
        "bidding_zone": zone,
        "price_eur_mwh": round(price, 4),
        "volume_mwh": round(random.uniform(300, 3000), 2),
        "mtu_minutes": mtu,
        "auction_type": "DAY_AHEAD",
        "data_source": "SIMULATED"
    }

def update_epex_bess(asset_id: str, zone_price: float, now: datetime) -> dict:
    soc = epex_soc[asset_id]
    cap = {"DE_BESS_1": 200, "FR_BESS_1": 150, "GB_BESS_1": 100}[asset_id]
    if zone_price > 100 and soc > 20:
        output_mw = cap * random.uniform(0.5, 0.9)
        soc -= (output_mw / cap) * 1.5
    elif zone_price < 40 and soc < 85:
        output_mw = -cap * random.uniform(0.4, 0.8)
        soc += (abs(output_mw) / cap) * 1.5
    else:
        output_mw = random.gauss(0, cap * 0.05)
    soc = max(5, min(97, soc))
    epex_soc[asset_id] = soc
    return {
        "asset_id": asset_id, "recorded_at": now,
        "state_of_charge_pct": round(soc, 2),
        "output_mw": round(output_mw, 2),
        "available_mw": round(cap * soc / 100 * 0.95, 2),
        "data_source": "SIMULATED"
    }

def run_epex_simulator(interval_seconds: int = 300):
    logger.info("EPEX simulator starting")
    while True:
        try:
            now = datetime.utcnow()
            today = now.date()
            mtu = get_mtu(today)
            intervals_per_hour = 60 // mtu

            # Simulate next 4 hours of day-ahead prices
            price_rows, bess_rows = [], []
            for h_offset in range(4):
                for slot in range(intervals_per_hour):
                    delivery_dt = datetime.combine(today, dtime(now.hour)) \
                                  + timedelta(hours=h_offset, minutes=slot * mtu)
                    for zone in ZONES:
                        price_rows.append(generate_epex_price(zone, delivery_dt, mtu))

            de_price = next(r["price_eur_mwh"] for r in price_rows
                            if r["bidding_zone"] == "DE-LU" and
                            r["delivery_datetime"].hour == now.hour)
            fr_price = next(r["price_eur_mwh"] for r in price_rows
                            if r["bidding_zone"] == "FR" and
                            r["delivery_datetime"].hour == now.hour)

            bess_rows.append(update_epex_bess("DE_BESS_1", float(de_price), now))
            bess_rows.append(update_epex_bess("FR_BESS_1", float(fr_price), now))
            bess_rows.append(update_epex_bess("GB_BESS_1",
                             float(next(r["price_eur_mwh"] for r in price_rows
                             if r["bidding_zone"]=="FR")), now))

            spark.createDataFrame(price_rows).write.mode("append").saveAsTable("apex.market_epex.prices")
            spark.createDataFrame(bess_rows).write.mode("append").saveAsTable("apex.market_epex.bess_telemetry")
            logger.info(f"EPEX: wrote {len(price_rows)} prices (MTU={mtu}), {len(bess_rows)} BESS")

        except Exception as e:
            logger.error(f"EPEX simulator error: {e}")
        time.sleep(interval_seconds)
```

---

## FILE: data/seeds/market/simulators/ercot_simulator.py

```python
"""
ERCOT Continuous Simulator
Writes to: apex.market_ercot.lmp, apex.market_ercot.bess_telemetry,
           apex.market_ercot.dam_prices
Interval: 30 seconds
RTC+B signal: NULL before 2025-12-05, populated after
"""
import time, random, logging
from datetime import datetime, date
from databricks.connect import DatabricksSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ercot_simulator")
spark = DatabricksSession.builder.profile("fe-vm").getOrCreate()

RTCB_LIVE_DATE = date(2025, 12, 5)

NODES = [
    "West Hub", "Houston Hub", "North Hub", "South Hub",
    "Panhandle Wind 1", "Panhandle Wind 2", "Panhandle Wind 3",
    "Dallas Load", "Houston Load", "Corpus Christi"
]
HUB_BASE = {
    "West Hub": 45, "Houston Hub": 50, "North Hub": 42, "South Hub": 44,
    "Dallas Load": 48, "Houston Load": 52, "Corpus Christi": 43
}
WIND_NODES = {"Panhandle Wind 1", "Panhandle Wind 2", "Panhandle Wind 3"}
ERCOT_ASSETS = ["TX_WEST_1", "TX_WEST_2", "TX_HOUSTON_1", "TX_NORTH_1"]
ASSET_NODE = {
    "TX_WEST_1": "West Hub", "TX_WEST_2": "West Hub",
    "TX_HOUSTON_1": "Houston Hub", "TX_NORTH_1": "North Hub"
}
ASSET_CAP = {"TX_WEST_1": 300, "TX_WEST_2": 200, "TX_HOUSTON_1": 250, "TX_NORTH_1": 150}

prev_lmp = {n: HUB_BASE.get(n, 20) for n in NODES}
ercot_soc = {a: random.uniform(25, 75) for a in ERCOT_ASSETS}

def is_rtcb_live(d: date) -> bool:
    return d >= RTCB_LIVE_DATE

def generate_ercot_lmp(node: str, now: datetime) -> dict:
    is_wind = node in WIND_NODES
    base = 20 if is_wind else HUB_BASE.get(node, 45)

    summer_peak = (now.month in [6, 7, 8] and 14 <= now.hour <= 19)
    scarcity = random.uniform(25, 100) if summer_peak and random.random() < 0.3 else 0
    wind_gen  = random.uniform(0.3, 1.0)  # wind capacity factor

    energy     = base + scarcity + random.gauss(0, base * 0.10)
    # Wind nodes: large negative congestion when wind is heavy
    congestion = (random.gauss(-18, 8) * (1 - wind_gen)) if is_wind else random.gauss(0, 3)
    loss       = random.gauss(0.5, 0.3)
    lmp        = energy + congestion + loss

    # RTC+B: small real-time adjustment, only after go-live
    rtcb = None
    if is_rtcb_live(now.date()):
        rtcb = round(lmp + random.gauss(0, 1.5), 4)

    prev_lmp[node] = float(lmp) if abs(float(lmp)) < 500 else prev_lmp[node]

    return {
        "interval_datetime": now,
        "node_id": node,
        "lmp": round(lmp, 4),
        "energy_component": round(energy, 4),
        "congestion_component": round(congestion, 4),
        "loss_component": round(loss, 4),
        "rtcb_signal": rtcb,
        "data_source": "SIMULATED"
    }

def update_ercot_bess(asset_id: str, hub_lmp: float, now: datetime) -> dict:
    soc = ercot_soc[asset_id]
    cap = ASSET_CAP[asset_id]
    rtcb = None
    if is_rtcb_live(now.date()):
        # RTC+B drives more aggressive dispatch
        if hub_lmp > 80 and soc > 20:
            output_mw = cap * random.uniform(0.7, 1.0)
            soc -= (output_mw / cap) * 2
            rtcb = round(hub_lmp * random.uniform(0.95, 1.05), 4)
        elif hub_lmp < 30 and soc < 85:
            output_mw = -cap * random.uniform(0.5, 0.85)
            soc += (abs(output_mw) / cap) * 2
        else:
            output_mw = random.gauss(0, cap * 0.05)
    else:
        if hub_lmp > 100 and soc > 25:
            output_mw = cap * random.uniform(0.6, 0.9)
            soc -= (output_mw / cap) * 2
        elif hub_lmp < 35 and soc < 80:
            output_mw = -cap * random.uniform(0.4, 0.8)
            soc += (abs(output_mw) / cap) * 2
        else:
            output_mw = random.gauss(0, cap * 0.05)
    soc = max(5, min(97, soc))
    ercot_soc[asset_id] = soc
    return {
        "asset_id": asset_id, "recorded_at": now,
        "state_of_charge_pct": round(soc, 2),
        "output_mw": round(output_mw, 2),
        "rtcb_signal": rtcb,
        "available_mw": round(cap * soc / 100 * 0.95, 2),
        "data_source": "SIMULATED"
    }

def run_ercot_simulator(interval_seconds: int = 30):
    logger.info("ERCOT simulator starting")
    while True:
        try:
            now = datetime.utcnow()
            lmp_rows, bess_rows = [], []
            for node in NODES:
                lmp_rows.append(generate_ercot_lmp(node, now))
            west_lmp = next(r["lmp"] for r in lmp_rows if r["node_id"] == "West Hub")
            houston_lmp = next(r["lmp"] for r in lmp_rows if r["node_id"] == "Houston Hub")
            north_lmp = next(r["lmp"] for r in lmp_rows if r["node_id"] == "North Hub")
            node_prices = {
                "TX_WEST_1": west_lmp, "TX_WEST_2": west_lmp,
                "TX_HOUSTON_1": houston_lmp, "TX_NORTH_1": north_lmp
            }
            for asset in ERCOT_ASSETS:
                bess_rows.append(update_ercot_bess(asset, float(node_prices[asset]), now))

            spark.createDataFrame(lmp_rows).write.mode("append").saveAsTable("apex.market_ercot.lmp")
            spark.createDataFrame(bess_rows).write.mode("append").saveAsTable("apex.market_ercot.bess_telemetry")
            rtcb_live = is_rtcb_live(now.date())
            logger.info(f"ERCOT: wrote {len(lmp_rows)} LMPs, {len(bess_rows)} BESS "
                       f"(RTC+B: {'LIVE' if rtcb_live else 'PRE-LAUNCH'})")

        except Exception as e:
            logger.error(f"ERCOT simulator error: {e}")
        time.sleep(interval_seconds)
```

---

## FILE: data/seeds/market/simulators/orchestrator.py

```python
"""
APEX Market Data Orchestrator
Runs NEM, EPEX, ERCOT simulators concurrently as daemon threads.
Deployed as: resources/jobs.yml → apex-market-simulator (infinite retry, no timeout)
"""
import threading, time, logging, sys
from nem_simulator   import run_nem_simulator
from epex_simulator  import run_epex_simulator
from ercot_simulator import run_ercot_simulator

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("orchestrator")

SIMULATORS = [
    {"name": "NEM",   "fn": run_nem_simulator,   "kwargs": {"interval_seconds": 30}},
    {"name": "EPEX",  "fn": run_epex_simulator,  "kwargs": {"interval_seconds": 300}},
    {"name": "ERCOT", "fn": run_ercot_simulator, "kwargs": {"interval_seconds": 30}},
]

def make_thread(sim: dict) -> threading.Thread:
    return threading.Thread(
        target=sim["fn"], kwargs=sim["kwargs"],
        daemon=True, name=f"sim-{sim['name'].lower()}"
    )

def run_all():
    threads = {s["name"]: make_thread(s) for s in SIMULATORS}
    for name, t in threads.items():
        logger.info(f"Starting {name} simulator")
        t.start()

    logger.info("All simulators running. Health check every 60s.")
    while True:
        time.sleep(60)
        for sim in SIMULATORS:
            name = sim["name"]
            if not threads[name].is_alive():
                logger.error(f"{name} simulator died — restarting")
                threads[name] = make_thread(sim)
                threads[name].start()
                logger.info(f"{name} simulator restarted")
        running = sum(1 for t in threads.values() if t.is_alive())
        logger.info(f"Health check: {running}/{len(SIMULATORS)} simulators alive")

if __name__ == "__main__":
    run_all()
```

## FILE: resources/jobs.yml

```yaml
jobs:
  apex-market-simulator:
    name: apex-market-simulator
    description: "Always-on market data simulator for NEM, EPEX, ERCOT"
    tasks:
      - task_key: run_simulators
        notebook_task:
          notebook_path: /app/pipelines/market_simulator_orchestrator
          base_parameters: {}
        libraries:
          - pypi: {package: "databricks-connect>=14.0"}
    max_concurrent_runs: 1
    max_retries: -1
    min_retry_interval_millis: 10000
    retry_on_timeout: true
    timeout_seconds: 0
    trigger:
      pause_status: UNPAUSED
    email_notifications:
      on_failure: []
```

## Backfill scripts

### data/seeds/market/backfill/nem_backfill.py
- Date range: 2024-01-01 to present
- All 5 NEM regions × 288 intervals/day = ~600k rows in nem.prices
- All 8 BESS assets × same range for bess_telemetry
- Uses same generate_nem_price() logic from simulator (consistent distributions)
- Batch writes in 10k-row chunks

### data/seeds/market/backfill/epex_backfill.py
- Date range: 2024-01-01 to present
- All 8 zones
- MTU=60 before 2025-09-01, MTU=15 after — CRITICAL to get right
- Verify: `SELECT mtu_minutes, COUNT(*) FROM apex.market_epex.prices GROUP BY mtu_minutes`

### data/seeds/market/backfill/ercot_backfill.py
- Date range: 2025-01-01 to present (ERCOT only — no pre-2025)
- All 10 nodes
- rtcb_signal IS NULL before 2025-12-05, float after — CRITICAL
- Verify: `SELECT rtcb_signal IS NULL, COUNT(*) FROM apex.market_ercot.lmp GROUP BY 1`

### data/seeds/market/backfill/run_all_backfills.py
- Sequential execution: NEM → EPEX → ERCOT
- Progress logging per 10k rows
- Idempotent: TRUNCATE then INSERT (or use MERGE on primary key)

## SUCCESS CRITERIA
1. Orchestrator job shows RUNNING in Databricks Jobs UI
2. `SELECT COUNT(*) FROM apex.market_nem.prices` increases every 30s
3. `SELECT COUNT(*) FROM apex.market_ercot.lmp` increases every 30s
4. EPEX MTU transition verified: rows before 2025-09-01 have mtu_minutes=60, after=15
5. ERCOT RTC+B verified: rtcb_signal IS NULL before 2025-12-05
6. NEM spike events present: `SELECT COUNT(*) FROM apex.market_nem.prices WHERE rrp > 1000`
7. EPEX negative prices present: `SELECT COUNT(*) FROM apex.market_epex.prices WHERE price_eur_mwh < 0`
8. BESS SOC varies realistically (5–98%) across all markets
9. After orchestrator restart, all 3 threads restart within 60s
10. DLT pipeline picks up new simulator rows within 60s

## COMPLETION ARTIFACT
completions/W03-market-simulators.md
Commit: "feat: W03 complete — multi-market continuous simulators"
