# APEX Energy Trading Platform - Database Setup

This directory contains SQL scripts to create the complete database schema for the APEX energy trading platform.

## Overview

The APEX platform uses the **`apex_fresh`** catalog with 8 schemas covering:
- 3 market-specific schemas (NEM, EPEX, ERCOT)
- 5 operational schemas (ingestion, trading, risk, portfolio, analytics)

## Execution Order

Run the SQL scripts in this order:

1. **00_create_catalog.sql** - Creates the `apex_fresh` catalog
2. **01_create_schemas.sql** - Creates all 8 schemas
3. **02_create_market_tables.sql** - Creates market data tables (NEM, EPEX, ERCOT)
4. **03_create_trading_tables.sql** - Creates trading and ingestion tables
5. **04_create_risk_tables.sql** - Creates risk management tables
6. **05_create_portfolio_tables.sql** - Creates portfolio and PPA tables
7. **06_create_analytics_tables.sql** - Creates analytics and ML tables

## Schema Structure

### apex_fresh.market_nem
- `prices` - NEM spot prices by region and 5-minute interval

### apex_fresh.market_epex
- `prices` - EPEX SPOT day-ahead and intraday prices

### apex_fresh.market_ercot
- `lmp` - ERCOT nodal LMP and RTCB signals

### apex_fresh.ingestion
- `raw_etrm_trades` - Raw ETRM data landing zone

### apex_fresh.trading
- `trades` - Processed trade records
- `offer_stacks` - Offer stack definitions
- `offer_bands` - Price-volume bands
- `dispatch_reference` - Asset dispatch configuration

### apex_fresh.risk
- `var_results` - VaR and Expected Shortfall calculations
- `limit_definitions` - Risk limit thresholds

### apex_fresh.portfolio
- `ppa_book` - Power Purchase Agreements
- `revenue_rates` - Revenue stacking rates
- `simulation_defaults` - Market simulation parameters

### apex_fresh.analytics
- `model_performance` - ML model metrics
- `backtest_runs` - Strategy backtest results
- `price_forecasts` - Price and demand forecasts
- `model_lineage` - Model training lineage
- `strategy_catalog` - Available strategies

## Running the Scripts

### Option 1: Databricks SQL Editor
1. Open Databricks SQL Editor
2. Copy and paste each script in order
3. Execute

### Option 2: Databricks CLI
```bash
databricks sql execute \
  --warehouse-id <warehouse-id> \
  --file sql/setup/00_create_catalog.sql \
  --profile DEFAULT

databricks sql execute \
  --warehouse-id <warehouse-id> \
  --file sql/setup/01_create_schemas.sql \
  --profile DEFAULT

# ... repeat for all scripts
```

### Option 3: DABS Job (Automated)
The `databricks.yml` includes a job resource that runs all scripts automatically:

```bash
databricks bundle deploy -p DEFAULT
databricks bundle run setup_apex_schema -p DEFAULT
```

## Warehouse Configuration

Default warehouse ID configured in app.yaml:
```yaml
DATABRICKS_SQL_WAREHOUSE_ID: a62624c51dced859
```

## Verification

After running all scripts, verify the setup:

```sql
-- List all schemas
SHOW SCHEMAS IN apex_fresh;

-- Verify tables in each schema
SHOW TABLES IN apex_fresh.market_nem;
SHOW TABLES IN apex_fresh.market_epex;
SHOW TABLES IN apex_fresh.market_ercot;
SHOW TABLES IN apex_fresh.trading;
SHOW TABLES IN apex_fresh.risk;
SHOW TABLES IN apex_fresh.portfolio;
SHOW TABLES IN apex_fresh.analytics;
```

## Notes

- All tables use Delta Lake format
- Tables include comprehensive comments for documentation
- Timestamps default to CURRENT_TIMESTAMP() where appropriate
- All schemas have descriptive comments explaining their purpose

## Related Files

- Application config: `app.yaml`
- Bundle config: `databricks.yml`
- Schema DDL: `apex_fresh/data/schema/01_catalog_and_core.sql` (reference)
