# APEX Screen Data Status

**Status**: ALL SCREENS POPULATED ✅
**Date**: 2026-03-22
**App URL**: https://apex-etrm-1444828305810485.aws.databricksapps.com
**Database**: apex_fresh catalog

---

## Screen Overview

| Screen | Status | Data Source | Record Count |
|--------|--------|-------------|--------------|
| Trading Blotter | ✅ POPULATED | trading.trades | 72 trades |
| Risk Dashboard | ✅ POPULATED | market prices + trades | 111,000 + 72 |
| Dispatch Console | ✅ POPULATED | dispatch_reference + offer_bands | 5 assets + 25 bands |
| Quant Console | ✅ POPULATED | model_performance + backtest_runs | 12 + 12 |

---

## Detailed Screen Data

### 1. Trading Blotter (`/apex/trading`)

**API Endpoint**: `/api/v1/trades/blotter`

**Data Available**:
- **72 trades** across 7 days
- **3 markets**: NEM, EPEX, ERCOT
- **4 traders**: alice.wong, bob.chen, carol.smith, david.jones
- **Instruments**:
  - NEM: NSW_PEAK_Q2, VIC_BASE_Q3, QLD_OFFPEAK_Q1, SA_CAP_Q4
  - EPEX: DE-LU_BASE_Q2, FR_PEAK_Q3, NL_BASE_Q1
  - ERCOT: ERCOT_NORTH_Q2, ERCOT_HOUSTON_Q3, ERCOT_WEST_Q1

**Sample Query**:
```sql
SELECT * FROM apex_fresh.trading.trades
ORDER BY ingested_at DESC LIMIT 10;
```

**Expected Display**:
- Trade table with real data
- PnL calculations
- Volume and price information
- Market distribution charts

---

### 2. Risk Dashboard (`/apex/risk`)

**API Endpoints**:
- `/api/v1/risk/var/calculate`
- `/api/v1/risk/stress-scenarios`
- `/api/v1/risk/limits/status`
- `/api/v1/risk/credit-exposure`

**Data Available**:
- **Market Prices**: 111,000 records
  - NEM: 53,280 prices (5 regions, 5-min intervals)
  - EPEX: 4,440 prices (5 markets, hourly)
  - ERCOT: 53,280 prices (5 hubs, 5-min intervals)
- **Trades**: 72 records for exposure calculations
- **VaR Calculations**: Based on real position exposure
- **Stress Scenarios**: Using actual market price maxima

**Sample Query**:
```sql
-- Risk exposure
SELECT
  market,
  SUM(CASE WHEN direction='BUY' THEN volume_mw ELSE -volume_mw END) as net_exposure
FROM apex_fresh.trading.trades
GROUP BY market;

-- Price volatility
SELECT
  AVG(rrp) as avg_price,
  STDDEV(rrp) as volatility,
  MAX(rrp) as max_price
FROM apex_fresh.market_nem.prices
WHERE interval_datetime >= CURRENT_DATE() - INTERVAL 7 DAYS;
```

**Expected Display**:
- VaR metrics (95%, 99%)
- Expected Shortfall
- Stress test results
- Credit exposure by counterparty
- Limit breach monitoring

---

### 3. Dispatch Console (`/apex/dispatch`)

**API Endpoints**:
- `/api/v1/dispatch/assets`
- `/api/v1/dispatch/offer-stack/latest`
- `/api/v1/dispatch/recommendations/{asset_id}`
- `/api/v1/dispatch/stack-history`

**Data Available**:
- **5 BESS Assets**:
  - NEM: BESS_DALTON, BESS_GANNAWARRA, BESS_HORNSDALE
  - ERCOT: BESS_HOUSTON_1, BESS_WEST_2
- **25 Offer Bands** (5 bands per asset)
- **Service Types**: FCAS_CONTINGENCY (NEM), ENERGY_ARBITRAGE (ERCOT)
- **Market Prices**: For dispatch recommendations

**Sample Query**:
```sql
-- Assets
SELECT * FROM apex_fresh.trading.dispatch_reference;

-- Latest offer stacks
SELECT
  asset_id,
  scenario,
  band_index,
  price,
  volume_mw,
  created_at
FROM apex_fresh.trading.offer_bands
WHERE created_at IN (
  SELECT MAX(created_at)
  FROM apex_fresh.trading.offer_bands
  GROUP BY asset_id
)
ORDER BY asset_id, band_index;
```

**Expected Display**:
- Asset list by market
- Offer band stacks (price/volume curves)
- Dispatch recommendations (CHARGE/DISCHARGE)
- Confidence scores
- Historical offer submissions

---

### 4. Quant Console (`/apex/quant`)

**API Endpoints**:
- `/api/v1/analytics/model-performance`
- `/api/v1/analytics/backtests`
- `/api/v1/analytics/model-lineage`

**Data Available**:
- **12 ML Model Runs**:
  - Models: ARIMA_v2, LSTM_v3, XGBoost_v1, Prophet_v2
  - Markets: NEM, EPEX, ERCOT (one run per market per model)
  - Metrics: MAPE, RMSE, R²

- **12 Backtest Runs**:
  - Strategies: Mean_Reversion, Momentum, Arbitrage, Statistical_Arb
  - Markets: NEM, EPEX, ERCOT (one run per market per strategy)
  - Metrics: Trades, Win Rate, Total PnL, Sharpe Ratio

**Sample Query**:
```sql
-- Model performance
SELECT
  model_name,
  market,
  mape,
  rmse,
  r2,
  run_timestamp
FROM apex_fresh.analytics.model_performance
ORDER BY market, run_timestamp DESC;

-- Backtest results
SELECT
  strategy,
  market,
  trades,
  win_rate,
  total_pnl,
  sharpe
FROM apex_fresh.analytics.backtest_runs
ORDER BY sharpe DESC;
```

**Expected Display**:
- Model accuracy metrics table
- Backtest performance summary
- Strategy comparison charts
- Model lineage and metadata
- Performance trends over time

---

## Data Summary

### Total Records in Database

| Category | Table | Records |
|----------|-------|---------|
| **Market Data** | | **111,000** |
| NEM Prices | market_nem.prices | 53,280 |
| EPEX Prices | market_epex.prices | 4,440 |
| ERCOT Prices | market_ercot.lmp | 53,280 |
| **Trading** | | **72** |
| Trades | trading.trades | 72 |
| **Analytics** | | **24** |
| Model Performance | analytics.model_performance | 12 |
| Backtest Runs | analytics.backtest_runs | 12 |
| **Dispatch** | | **30** |
| Assets | trading.dispatch_reference | 5 |
| Offer Bands | trading.offer_bands | 25 |
| **TOTAL** | | **111,126** |

---

## Data Coverage

### Time Ranges

- **Market Prices**: Feb 20 - Mar 22, 2026 (37 days)
- **Trades**: Last 7 days
- **Analytics**: Last 30 days (model runs)
- **Analytics**: Last 20 days (backtests)
- **Dispatch**: Last 12 hours (offer stacks)

### Geographic Coverage

- **NEM (Australia)**: 5 regions
- **EPEX (Europe)**: 5 markets (DE, FR, NL, BE, AT)
- **ERCOT (Americas)**: 5 hubs

---

## Verification Commands

### Check all screens have data:

```bash
# Verify market data
python3 scripts/verify_data.py

# Check operational data
python3 -c "
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile='DEFAULT')

# Trading
trades = w.statement_execution.execute_statement(
    warehouse_id='4b9b953939869799',
    statement='SELECT COUNT(*) as cnt FROM apex_fresh.trading.trades',
    wait_timeout='30s'
)
print(f'Trades: {trades.result.data_array[0][0]}')

# Analytics
models = w.statement_execution.execute_statement(
    warehouse_id='4b9b953939869799',
    statement='SELECT COUNT(*) as cnt FROM apex_fresh.analytics.model_performance',
    wait_timeout='30s'
)
print(f'Models: {models.result.data_array[0][0]}')

# Dispatch
assets = w.statement_execution.execute_statement(
    warehouse_id='4b9b953939869799',
    statement='SELECT COUNT(*) as cnt FROM apex_fresh.trading.dispatch_reference',
    wait_timeout='30s'
)
print(f'Assets: {assets.result.data_array[0][0]}')
"
```

---

## Notes

1. **All data is synthetic** - generated for demo purposes
2. **Data patterns are realistic** - includes time-of-day variations, volatility, price spikes
3. **No API keys required** - all data seeded locally
4. **Demo-ready state** - all screens populated with meaningful data
5. **Refresh capability** - scripts can regenerate data anytime

---

**Status**: ✅ ALL SCREENS READY FOR DEMO
**Last Updated**: 2026-03-22
**Next Steps**: Application is fully populated and ready for demonstration
