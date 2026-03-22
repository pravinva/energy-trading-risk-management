# APEX Energy Trading - Real-Time Data Ingestion Jobs

## ✅ Created and Configured

All real-time data ingestion jobs have been created and are ready for deployment.

---

## Job Summary

### 1. NEMWEB Real-Time Ingestion 🇦🇺
**Job Name**: `APEX - NEMWEB Real-Time Ingestion`
**Schedule**: Every 5 minutes
**Timezone**: Australia/Sydney
**Script**: `jobs/ingestion/nemweb_real_time.py`

**Data Source**:
- NEMWEB Public API
- 5-minute dispatch prices

**Regions Covered**:
- NSW1 (New South Wales)
- VIC1 (Victoria)
- QLD1 (Queensland)
- SA1 (South Australia)
- TAS1 (Tasmania)

**Target Table**: `apex_fresh.market_nem.prices`

**Expected Volume**: ~60 records per run (12 intervals × 5 regions)

---

### 2. EPEX Day-Ahead Prices 🇪🇺
**Job Name**: `APEX - EPEX Day-Ahead Ingestion`
**Schedule**: Daily at 14:00 UTC (after auction results)
**Timezone**: Europe/Berlin
**Script**: `jobs/ingestion/epex_day_ahead.py`

**Data Source**:
- ENTSOE Transparency Platform API
- Day-ahead auction prices

**Markets Covered**:
- DE (Germany)
- FR (France)
- NL (Netherlands)
- BE (Belgium)
- AT (Austria)

**Target Table**: `apex_fresh.market_epex.prices`

**Expected Volume**: ~600 records per run (5 markets × 24 hours × 4-6 intervals)

**Requirements**:
- `ENTSOE_API_KEY` environment variable
- Register at: https://transparency.entsoe.eu/

---

### 3. ERCOT Real-Time Prices 🇺🇸
**Job Name**: `APEX - ERCOT Real-Time Ingestion`
**Schedule**: Every 5 minutes
**Timezone**: America/Chicago
**Script**: `jobs/ingestion/ercot_real_time.py`

**Data Source**:
- ERCOT Public API
- Real-time Settlement Point Prices (SPP)

**Settlement Points**:
- HB_BUSAVG (System average)
- HB_HOUSTON (Houston hub)
- HB_NORTH (North hub)
- HB_SOUTH (South hub)
- HB_WEST (West hub)

**Target Table**: `apex_fresh.market_ercot.lmp`

**Expected Volume**: ~60 records per run (12 intervals × 5 hubs)

**Requirements**:
- `ERCOT_API_KEY` optional (for higher rate limits)
- Register at: https://www.ercot.com/services/api

---

## Infrastructure Configuration

### Cluster Configuration
All jobs use **single-node clusters** for cost optimization:
- **Spark Version**: 14.3.x-scala2.12
- **Node Type**: i3.xlarge
- **Workers**: 0 (single-node)
- **Resource Class**: SingleNode

### Libraries
- httpx (HTTP client)
- pandas (data manipulation)
- databricks-sdk (Unity Catalog access)

### Timeouts
- **NEMWEB**: 600 seconds (10 minutes)
- **EPEX**: 1200 seconds (20 minutes)
- **ERCOT**: 600 seconds (10 minutes)

---

## Deployment Status

### Files Created ✅
- `jobs/ingestion/nemweb_real_time.py`
- `jobs/ingestion/epex_day_ahead.py`
- `jobs/ingestion/ercot_real_time.py`
- `jobs/README.md`
- Updated `databricks.yml` with job definitions

### Git Commits ✅
- Commit: `e1d49ec`
- Branch: `wave5-energy-trading-expansion`
- Pushed to GitHub: ✅

### Deployment to Workspace
```bash
# Deploy all jobs
databricks bundle deploy -t dev -p DEFAULT

# Verify deployment
databricks jobs list --profile DEFAULT | grep APEX

# View job details
databricks jobs get --job-name "APEX - NEMWEB Real-Time Ingestion" -p DEFAULT
```

---

## Activation & Monitoring

### Manual Job Execution (Testing)
```bash
# Test NEMWEB ingestion
databricks jobs run-now --job-name "APEX - NEMWEB Real-Time Ingestion" -p DEFAULT

# Test EPEX ingestion
databricks jobs run-now --job-name "APEX - EPEX Day-Ahead Ingestion" -p DEFAULT

# Test ERCOT ingestion
databricks jobs run-now --job-name "APEX - ERCOT Real-Time Ingestion" -p DEFAULT
```

### Schedule Status
All jobs are configured with `pause_status: UNPAUSED` and will start running automatically once deployed.

To pause a job:
```bash
databricks jobs update --job-id <job-id> --pause-status PAUSED -p DEFAULT
```

### Monitoring Queries
```sql
-- Check recent NEMWEB ingestions
SELECT * FROM apex_fresh.market_nem.ingestion_log
ORDER BY start_timestamp DESC LIMIT 10;

-- Check recent EPEX ingestions
SELECT * FROM apex_fresh.market_epex.ingestion_log
ORDER BY start_timestamp DESC LIMIT 10;

-- Check recent ERCOT ingestions
SELECT * FROM apex_fresh.market_ercot.ingestion_log
ORDER BY start_timestamp DESC LIMIT 10;

-- Count records ingested today
SELECT
  'NEMWEB' as market,
  COUNT(*) as records,
  MIN(interval_datetime) as earliest,
  MAX(interval_datetime) as latest
FROM apex_fresh.market_nem.prices
WHERE DATE(interval_datetime) = CURRENT_DATE()

UNION ALL

SELECT
  'EPEX' as market,
  COUNT(*) as records,
  MIN(delivery_datetime) as earliest,
  MAX(delivery_datetime) as latest
FROM apex_fresh.market_epex.prices
WHERE DATE(delivery_datetime) = CURRENT_DATE()

UNION ALL

SELECT
  'ERCOT' as market,
  COUNT(*) as records,
  MIN(interval_datetime) as earliest,
  MAX(interval_datetime) as latest
FROM apex_fresh.market_ercot.lmp
WHERE DATE(interval_datetime) = CURRENT_DATE();
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Market APIs                         │
│                                                                  │
│  NEMWEB API       ENTSOE API           ERCOT API                │
│  (5-min)          (day-ahead)          (5-min)                  │
└────────┬──────────────────┬─────────────────┬────────────────────┘
         │                  │                 │
         │ Every 5 min      │ Daily 14:00 UTC │ Every 5 min
         ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Databricks Scheduled Jobs                           │
│                                                                  │
│  NEMWEB Job       EPEX Job             ERCOT Job                │
│  (Single-node)    (Single-node)        (Single-node)            │
└────────┬──────────────────┬─────────────────┬────────────────────┘
         │                  │                 │
         ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Unity Catalog Delta Tables                          │
│                                                                  │
│  market_nem       market_epex          market_ercot             │
│  └─ prices        └─ prices            └─ lmp                   │
└─────────────────────────────────────────────────────────────────┘
         │                  │                 │
         └──────────────────┴─────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                APEX Energy Trading App                           │
│                                                                  │
│  - Real-time price charts                                       │
│  - Trading signals                                               │
│  - Risk analytics (VaR, portfolio optimization)                 │
│  - Monte Carlo simulations                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance & Costs

### Expected Data Volume (Daily)
- **NEMWEB**: ~17,280 records (288 runs × 60 records)
- **EPEX**: ~600 records (1 run × 600 records)
- **ERCOT**: ~17,280 records (288 runs × 60 records)
- **Total**: ~35,000 records/day

### Storage (Estimated)
- Daily: ~5-10 MB (compressed Delta)
- Monthly: ~150-300 MB
- Yearly: ~2-4 GB

### Compute Costs (Estimated)
- Per job run: $0.10-0.20 (single-node cluster)
- NEMWEB: $28-57/day (288 runs)
- EPEX: $0.10-0.20/day (1 run)
- ERCOT: $28-57/day (288 runs)
- **Total**: ~$50-100/day for real-time data

**Cost Optimization Options**:
- Use Spot instances
- Reduce ingestion frequency to 15-minute intervals
- Use Databricks serverless compute (when available)

---

## Environment Variables Required

### ENTSOE API (for EPEX)
```bash
export ENTSOE_API_KEY="your-api-key-here"
```

Set in Databricks job configuration:
- Workflows > Job > Tasks > Environment Variables
- Or use Databricks Secrets

### ERCOT API (optional)
```bash
export ERCOT_API_KEY="your-api-key-here"
```

### Catalog Configuration
```bash
export APEX_CATALOG="apex_fresh"
export DATABRICKS_SQL_WAREHOUSE_ID="4b9b953939869799"
```

---

## Next Steps

### 1. Create Ingestion Log Tables
```sql
-- NEMWEB ingestion log
CREATE TABLE IF NOT EXISTS apex_fresh.market_nem.ingestion_log (
  log_id STRING,
  data_type STRING,
  date_loaded DATE,
  region_id STRING,
  records_loaded BIGINT,
  records_failed BIGINT,
  start_timestamp TIMESTAMP,
  end_timestamp TIMESTAMP,
  duration_seconds DOUBLE,
  status STRING,
  error_message STRING
) USING DELTA;

-- EPEX ingestion log
CREATE TABLE IF NOT EXISTS apex_fresh.market_epex.ingestion_log (
  log_id STRING,
  market STRING,
  data_type STRING,
  date_loaded DATE,
  market_area STRING,
  records_loaded BIGINT,
  records_failed BIGINT,
  start_timestamp TIMESTAMP,
  status STRING,
  duration_seconds DOUBLE,
  error_message STRING
) USING DELTA;

-- ERCOT ingestion log
CREATE TABLE IF NOT EXISTS apex_fresh.market_ercot.ingestion_log (
  log_id STRING,
  market STRING,
  data_type STRING,
  date_loaded DATE,
  settlement_point STRING,
  records_loaded BIGINT,
  records_failed BIGINT,
  start_timestamp TIMESTAMP,
  status STRING,
  duration_seconds DOUBLE,
  error_message STRING
) USING DELTA;
```

### 2. Set Up API Keys
- Register for ENTSOE API: https://transparency.entsoe.eu/
- Register for ERCOT API (optional): https://www.ercot.com/services/api
- Store keys in Databricks Secrets

### 3. Test Jobs
```bash
# Run each job manually to verify
databricks jobs run-now --job-name "APEX - NEMWEB Real-Time Ingestion" -p DEFAULT
databricks jobs run-now --job-name "APEX - EPEX Day-Ahead Ingestion" -p DEFAULT
databricks jobs run-now --job-name "APEX - ERCOT Real-Time Ingestion" -p DEFAULT
```

### 4. Monitor First 24 Hours
- Check ingestion logs for errors
- Verify data quality
- Monitor compute costs
- Adjust schedules if needed

---

## Troubleshooting

### Job Fails with "Table not found"
Run database setup script:
```bash
python3 scripts/setup_database.py
```

### Job Fails with "API Key Invalid"
Check environment variables in job configuration:
- Workflows > Jobs > Select Job > Tasks > Configure
- Add environment variables or reference secrets

### Missing Data for Specific Hours
- NEMWEB: Data available 2-3 minutes after interval
- EPEX: Day-ahead prices published around 13:00-14:00 UTC
- ERCOT: Real-time prices with ~5-10 minute delay

### High Failure Rate
- Check API rate limits
- Increase retry logic
- Add exponential backoff

---

**Last Updated**: 2026-03-22
**Version**: 1.0
**Status**: ✅ Ready for Deployment
