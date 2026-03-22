# APEX Energy Trading - Historical Data Backfill Jobs

Scripts for backfilling historical market data into Delta tables.

## Overview

These jobs fetch historical data from market APIs and populate the Delta tables with past data. Useful for:
- Initial database population
- Filling data gaps
- Historical analysis
- Model training datasets

---

## Backfill Jobs

### 1. NEMWEB Backfill (Australia)

**Script**: `nemweb_backfill.py`

**Usage**:
```bash
# Backfill last 30 days
python3 jobs/backfill/nemweb_backfill.py \
  --start-date 2026-02-20 \
  --end-date 2026-03-21

# Backfill last 90 days
python3 jobs/backfill/nemweb_backfill.py \
  --start-date 2025-12-22 \
  --end-date 2026-03-21
```

**Features**:
- Backfills all 5 NEM regions (NSW1, VIC1, QLD1, SA1, TAS1)
- 5-minute dispatch price intervals
- Automatic retry on failures
- Progress tracking
- Failed dates summary

**Data Volume**:
- Per day: ~300 records (288 intervals × 5 regions)
- 30 days: ~9,000 records
- 90 days: ~27,000 records

---

### 2. EPEX Backfill (Europe)

**Script**: `epex_backfill.py`

**Usage**:
```bash
# Backfill last 30 days for all markets
python3 jobs/backfill/epex_backfill.py \
  --start-date 2026-02-20 \
  --end-date 2026-03-21

# Backfill specific markets
python3 jobs/backfill/epex_backfill.py \
  --start-date 2026-02-20 \
  --end-date 2026-03-21 \
  --market-areas DE FR
```

**Features**:
- Backfills DE, FR, NL, BE, AT markets
- Day-ahead auction prices
- Hourly intervals
- Rate limiting (1 second between requests)
- ENTSOE API compliance

**Data Volume**:
- Per day per market: ~24-96 records (depends on MTU)
- 30 days, 5 markets: ~6,000 records
- 90 days, 5 markets: ~18,000 records

**Requirements**:
```bash
export ENTSOE_API_KEY="your-api-key-here"
```

---

### 3. ERCOT Backfill (Texas)

**Script**: `ercot_backfill.py`

**Usage**:
```bash
# Backfill last 30 days for all hubs
python3 jobs/backfill/ercot_backfill.py \
  --start-date 2026-02-20 \
  --end-date 2026-03-21

# Backfill specific settlement points
python3 jobs/backfill/ercot_backfill.py \
  --start-date 2026-02-20 \
  --end-date 2026-03-21 \
  --settlement-points HB_BUSAVG HB_HOUSTON
```

**Features**:
- Backfills 5 major hubs
- 5-minute Settlement Point Prices
- Processes in 6-hour chunks to manage API load
- Rate limiting (2 seconds between chunks)

**Data Volume**:
- Per day per settlement point: ~288 records (5-minute intervals)
- 30 days, 5 hubs: ~43,200 records
- 90 days, 5 hubs: ~129,600 records

**Requirements**:
```bash
export ERCOT_API_KEY="your-api-key-here"  # Optional
```

---

## Running Backfill Jobs on Databricks

### Option 1: One-off Job Run

```bash
# Create a job run
databricks jobs run-now \
  --job-name "APEX - NEMWEB Backfill" \
  --python-params '["--start-date", "2026-02-20", "--end-date", "2026-03-21"]' \
  --profile DEFAULT
```

### Option 2: Notebook Execution

Create a notebook that imports and runs the backfill:

```python
# Databricks notebook
import subprocess
import sys

# Run NEMWEB backfill
result = subprocess.run([
    sys.executable,
    "/Workspace/path/to/jobs/backfill/nemweb_backfill.py",
    "--start-date", "2026-02-20",
    "--end-date", "2026-03-21"
], capture_output=True, text=True)

print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    raise Exception(f"Backfill failed with code {result.returncode}")
```

### Option 3: Interactive Execution

```bash
# SSH to Databricks cluster or use Databricks Connect
databricks workspace import \
  jobs/backfill/nemweb_backfill.py \
  /Workspace/Users/your.email@databricks.com/backfill/nemweb_backfill.py \
  --profile DEFAULT

# Run via dbutils
%python
import subprocess
subprocess.run([
    "python",
    "/Workspace/Users/your.email@databricks.com/backfill/nemweb_backfill.py",
    "--start-date", "2026-02-20",
    "--end-date", "2026-03-21"
])
```

---

## Recommended Backfill Strategy

### Initial Setup (First Time)

**Week 1: Recent Data (Last 30 Days)**
```bash
# Critical for immediate analytics
python3 jobs/backfill/nemweb_backfill.py --start-date 2026-02-20 --end-date 2026-03-21
python3 jobs/backfill/epex_backfill.py --start-date 2026-02-20 --end-date 2026-03-21
python3 jobs/backfill/ercot_backfill.py --start-date 2026-02-20 --end-date 2026-03-21
```

**Week 2: Medium History (90 Days)**
```bash
# Good for short-term patterns
python3 jobs/backfill/nemweb_backfill.py --start-date 2025-12-22 --end-date 2026-02-19
python3 jobs/backfill/epex_backfill.py --start-date 2025-12-22 --end-date 2026-02-19
python3 jobs/backfill/ercot_backfill.py --start-date 2025-12-22 --end-date 2026-02-19
```

**Week 3-4: Long History (1 Year)**
```bash
# For seasonal patterns and ML training
python3 jobs/backfill/nemweb_backfill.py --start-date 2025-03-22 --end-date 2025-12-21
python3 jobs/backfill/epex_backfill.py --start-date 2025-03-22 --end-date 2025-12-21
python3 jobs/backfill/ercot_backfill.py --start-date 2025-03-22 --end-date 2025-12-21
```

### Incremental Backfill (Fill Gaps)

```bash
# Find missing dates
SELECT DISTINCT DATE(interval_datetime) as date_loaded
FROM apex_fresh.market_nem.prices
WHERE interval_datetime >= '2025-01-01'
ORDER BY date_loaded;

# Backfill specific gap
python3 jobs/backfill/nemweb_backfill.py \
  --start-date 2025-06-15 \
  --end-date 2025-06-20
```

---

## Performance & Cost Estimates

### NEMWEB Backfill
- **30 days**: ~15-20 minutes runtime, $2-3 compute cost
- **90 days**: ~45-60 minutes runtime, $6-8 compute cost
- **1 year**: ~6-8 hours runtime, $25-35 compute cost

### EPEX Backfill
- **30 days**: ~10-15 minutes runtime, $1-2 compute cost
- **90 days**: ~30-40 minutes runtime, $4-6 compute cost
- **1 year**: ~4-6 hours runtime, $15-25 compute cost

### ERCOT Backfill
- **30 days**: ~20-30 minutes runtime, $3-4 compute cost
- **90 days**: ~60-90 minutes runtime, $8-12 compute cost
- **1 year**: ~8-12 hours runtime, $30-45 compute cost

**Total for 1 Year All Markets**: ~$70-100

---

## Monitoring Backfill Progress

### Real-time Monitoring
```bash
# Watch backfill job logs
tail -f /tmp/backfill_nemweb.log

# Check ingestion logs
databricks sql execute \
  --warehouse-id 4b9b953939869799 \
  --query "SELECT * FROM apex_fresh.nemweb.ingestion_log ORDER BY start_timestamp DESC LIMIT 10" \
  --profile DEFAULT
```

### Verify Data Completeness
```sql
-- Check daily record counts
SELECT
  DATE(interval_datetime) as date,
  COUNT(*) as records,
  COUNT(DISTINCT region_id) as regions
FROM apex_fresh.market_nem.prices
WHERE interval_datetime >= '2026-02-01'
GROUP BY DATE(interval_datetime)
ORDER BY date DESC;

-- Expected: ~288 records per day per region = 1,440 records/day total

-- Find missing dates
WITH date_range AS (
  SELECT explode(sequence(
    DATE'2026-02-01',
    CURRENT_DATE(),
    INTERVAL 1 DAY
  )) as expected_date
)
SELECT dr.expected_date
FROM date_range dr
LEFT JOIN (
  SELECT DISTINCT DATE(interval_datetime) as actual_date
  FROM apex_fresh.market_nem.prices
) p ON dr.expected_date = p.actual_date
WHERE p.actual_date IS NULL
ORDER BY dr.expected_date;
```

---

## Troubleshooting

### Issue: API Rate Limiting
**Solution**: Increase sleep intervals in backfill scripts
```python
# Change from 1 second to 2 seconds
await asyncio.sleep(2)
```

### Issue: Out of Memory
**Solution**: Reduce date range or process fewer settlement points at once
```bash
# Instead of full range
--start-date 2025-01-01 --end-date 2025-12-31

# Break into chunks
--start-date 2025-01-01 --end-date 2025-03-31
--start-date 2025-04-01 --end-date 2025-06-30
# ... etc
```

### Issue: Many Failed Dates
**Solution**: Check API availability for those dates
- NEMWEB: Data available from ~2009
- EPEX: Data available from ~2015 (varies by market)
- ERCOT: Data available from ~2010

Some historical dates may not have data available.

---

## Best Practices

1. **Start Small**: Begin with last 7-30 days before attempting longer ranges
2. **Check API Limits**: Verify rate limits for each API before large backfills
3. **Monitor Progress**: Watch first few iterations to ensure correct operation
4. **Schedule Off-Peak**: Run large backfills during off-peak hours
5. **Incremental Approach**: Backfill in chunks rather than all at once
6. **Verify Data**: Check record counts and data quality after each run
7. **Save Logs**: Keep backfill logs for troubleshooting

---

## Environment Variables

Required for backfill jobs:

```bash
# EPEX backfill (required)
export ENTSOE_API_KEY="your-entsoe-api-key"

# ERCOT backfill (optional, for higher rate limits)
export ERCOT_API_KEY="your-ercot-api-key"

# Database configuration
export APEX_CATALOG="apex_fresh"
export DATABRICKS_SQL_WAREHOUSE_ID="4b9b953939869799"
```

---

**Last Updated**: 2026-03-22
**Status**: ✅ Ready to Run
