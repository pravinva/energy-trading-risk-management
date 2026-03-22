# APEX Energy Trading Platform - Database Schema

## Deployment Summary

**Date**: 2026-03-22
**Workspace**: e2-demo-field-eng.cloud.databricks.com
**Catalog**: `apex_fresh`
**Status**: ✅ **Successfully Created**

---

## Catalog Information

```
Name: apex_fresh
Type: MANAGED_CATALOG
Owner: pravin.varma@databricks.com
Created: 2026-03-22
Comment: APEX Energy Analytics Platform — NEM · EPEX · ERCOT
```

---

## Schemas (8 total)

### 1. **apex_fresh.market_nem**
**Purpose**: NEM (Australia) — spot prices, generation, FCAS, BESS telemetry

**Tables**:
- `prices` - NEM spot prices by region and 5-minute interval
  - interval_datetime, region_id, rrp, data_source

---

### 2. **apex_fresh.market_epex**
**Purpose**: EPEX (Europe) — day-ahead, intraday, EU ETS

**Tables**:
- `prices` - EPEX SPOT day-ahead and intraday prices
  - delivery_datetime, bidding_zone, price_eur_mwh, mtu_minutes, data_source

---

### 3. **apex_fresh.market_ercot**
**Purpose**: ERCOT (Americas) — nodal LMP, RTC+B dispatch signals

**Tables**:
- `lmp` - ERCOT nodal LMP and RTCB dispatch signals
  - interval_datetime, node_id, lmp, rtcb_signal, data_source

---

### 4. **apex_fresh.ingestion**
**Purpose**: ETRM raw landing zone and sync metadata — DLT source

**Tables**:
- `raw_etrm_trades` - Raw ETRM trade data landing zone
  - source_system, market, payload, processed, received_at

---

### 5. **apex_fresh.trading**
**Purpose**: Trade analytics layer — populated by DLT from ETRM sources

**Tables**:
- `trades` - Processed trade records from ETRM systems
  - trade_id, market, instrument_id, trader_id, direction, volume_mw, price, source_system, ingested_at
- `offer_stacks` - Offer stack definitions for dispatch optimization
  - asset_id, scenario, created_at
- `offer_bands` - Individual price-volume bands within offer stacks
  - asset_id, scenario, band_index, price, volume_mw, created_at
- `dispatch_reference` - Asset dispatch configuration and service mappings
  - market, asset_id, service_type

---

### 6. **apex_fresh.risk**
**Purpose**: VaR, stress tests, credit exposure, limit monitoring

**Tables**:
- `var_results` - Value at Risk and Expected Shortfall calculations
  - run_id, market, exposure_mw, var_95, var_99, expected_shortfall_95, calculated_at
- `limit_definitions` - Risk limit definitions and thresholds
  - metric, limit_value

---

### 7. **apex_fresh.portfolio**
**Purpose**: Revenue stacking, PPA book, asset benchmarking

**Tables**:
- `ppa_book` - Power Purchase Agreement portfolio book
  - ppa_id, market, counterparty, volume_mw, strike_price, tenor_years, as_of_timestamp
- `revenue_rates` - Revenue stacking component rates and percentages
  - component, rate_value
- `simulation_defaults` - Market-specific simulation parameter defaults and limits
  - market, duration_hours_default, duration_hours_max, ancillary_pct_default, ancillary_pct_max, ppa_mw_default, ppa_mw_max, ppa_mtm_factor

---

### 8. **apex_fresh.analytics**
**Purpose**: ML forecasts, backtest results, model metadata

**Tables**:
- `model_performance` - ML model performance metrics and evaluation results
  - model_name, market, mape, rmse, r2, run_timestamp
- `backtest_runs` - Strategy backtest results and performance metrics
  - strategy, market, trades, win_rate, total_pnl, sharpe, run_timestamp
- `price_forecasts` - Price and demand forecasts from ML models
  - market, instrument, forecast_datetime, forecast_price, forecast_demand_mw, model_name, run_timestamp
- `model_lineage` - ML model training lineage and reproducibility tracking
  - market, model_name, run_timestamp, training_start_utc, training_end_utc, feature_set, feature_hash
- `strategy_catalog` - Available trading strategies per market
  - market, strategy, available

---

## Table Statistics

| Schema | Table Count | Purpose |
|--------|-------------|---------|
| market_nem | 1 | Australian NEM market data |
| market_epex | 1 | European EPEX market data |
| market_ercot | 1 | US ERCOT market data |
| ingestion | 1 | Raw ETRM data landing |
| trading | 4 | Trade capture & dispatch |
| risk | 2 | Risk management |
| portfolio | 3 | Portfolio & PPA management |
| analytics | 5 | ML models & forecasts |
| **TOTAL** | **18** | |

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ETRM Source Systems                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              apex_fresh.ingestion                           │
│              └─ raw_etrm_trades                             │
└────────────────────┬────────────────────────────────────────┘
                     │ (DLT Pipeline)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              apex_fresh.trading                             │
│              └─ trades, offer_stacks, etc.                  │
└────────┬────────────────────────┬───────────────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────────────────┐
│ apex_fresh.risk  │     │ apex_fresh.portfolio         │
│ └─ var_results   │     │ └─ ppa_book                  │
│ └─ limits        │     │ └─ revenue_rates             │
└──────────────────┘     └──────────────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────────────┐
                         │ apex_fresh.analytics         │
                         │ └─ model_performance         │
                         │ └─ price_forecasts           │
                         │ └─ backtest_runs             │
                         └──────────────────────────────┘
```

---

## Market Data Sources

### NEM (Australia)
- **Schema**: `apex_fresh.market_nem`
- **Data**: NEMWEB 5-minute spot prices, FCAS, generation
- **Regions**: NSW1, QLD1, SA1, TAS1, VIC1

### EPEX SPOT (Europe)
- **Schema**: `apex_fresh.market_epex`
- **Data**: Day-ahead and intraday prices
- **Zones**: DE-LU, FR, NL, BE, AT, CH
- **MTU**: 15-minute and 60-minute products

### ERCOT (Texas, USA)
- **Schema**: `apex_fresh.market_ercot`
- **Data**: Nodal LMP, RTCB dispatch signals
- **Nodes**: 4000+ settlement points
- **Intervals**: 5-minute and 15-minute

---

## Application Configuration

The apex-etrm application is configured to use this catalog via environment variables:

```yaml
# app.yaml
env:
  - name: APEX_CATALOG
    value: apex_fresh
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: 01370556fad60fda  # TPCDS_L warehouse
```

---

## Setup Files

All SQL setup scripts are available in:
- **Location**: `sql/setup/`
- **Setup Script**: `scripts/setup_database.py`

**Files**:
1. `00_create_catalog.sql` - Creates apex_fresh catalog
2. `01_create_schemas.sql` - Creates 8 schemas
3. `02_create_market_tables.sql` - Market data tables
4. `03_create_trading_tables.sql` - Trading tables
5. `04_create_risk_tables.sql` - Risk tables
6. `05_create_portfolio_tables.sql` - Portfolio tables
7. `06_create_analytics_tables.sql` - Analytics tables

---

## Next Steps

### 1. Load Seed Data (Optional)
```bash
# Run seed data scripts if available
databricks bundle run seed_data -p DEFAULT
```

### 2. Verify Tables
```sql
-- List all tables
SHOW TABLES IN apex_fresh.market_nem;
SHOW TABLES IN apex_fresh.trading;
SHOW TABLES IN apex_fresh.risk;
SHOW TABLES IN apex_fresh.portfolio;
SHOW TABLES IN apex_fresh.analytics;

-- Count tables
SELECT COUNT(*) as table_count
FROM apex_fresh.information_schema.tables
WHERE table_schema NOT IN ('default', 'information_schema');
```

### 3. App Integration
The deployed apex-etrm app will automatically use this catalog for:
- Market data ingestion
- Trade processing
- Risk calculations
- Portfolio analytics
- ML forecasting

---

## Access & Permissions

**Owner**: pravin.varma@databricks.com
**Isolation Mode**: OPEN
**Predictive Optimization**: ENABLED (inherited from metastore)

---

## Technical Notes

- **Format**: All tables use Delta Lake
- **Timestamps**: UTC timezone recommended
- **Column Defaults**: Not enabled (removed from DDL)
- **Collation**: UTF8_BINARY
- **Warehouse**: 01370556fad60fda (TPCDS_L)

---

## Related Documentation

- Application: `README.md`
- Setup Guide: `sql/setup/README.md`
- Color Reference: `docs/COLOR_REFERENCE.md`
- Design System: `docs/DESIGN_SYSTEM_UPDATE.md`
- Deployment: `databricks.yml`

---

**Document Version**: 1.0
**Last Updated**: 2026-03-22
**Workspace**: e2-demo-field-eng.cloud.databricks.com
