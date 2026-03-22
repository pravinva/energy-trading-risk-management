# APEX Energy Trading - Data Ingestion Jobs

This directory contains Databricks jobs for real-time market data ingestion from multiple energy markets.

## Job Overview

### 1. NEMWEB Real-Time Ingestion
**File**: `ingestion/nemweb_real_time.py`
**Schedule**: Every 5 minutes
**Purpose**: Fetches 5-minute dispatch prices from Australian NEM market
**Data Source**: NEMWEB Public API
**Regions**: NSW1, VIC1, QLD1, SA1, TAS1
**Target Table**: `apex_fresh.market_nem.prices`

### 2. EPEX Day-Ahead Prices
**File**: `ingestion/epex_day_ahead.py`
**Schedule**: Daily at 14:00 UTC (after day-ahead auction)
**Purpose**: Fetches day-ahead auction prices from European power exchanges
**Data Source**: ENTSOE Transparency Platform API
**Markets**: DE, FR, NL, BE, AT
**Target Table**: `apex_fresh.market_epex.prices`
**Requirements**: `ENTSOE_API_KEY` environment variable

### 3. ERCOT Real-Time Prices
**File**: `ingestion/ercot_real_time.py`
**Schedule**: Every 5 minutes
**Purpose**: Fetches real-time Settlement Point Prices from ERCOT
**Data Source**: ERCOT Public API
**Settlement Points**: HB_BUSAVG, HB_HOUSTON, HB_NORTH, HB_SOUTH, HB_WEST
**Target Table**: `apex_fresh.market_ercot.lmp`
**Requirements**: `ERCOT_API_KEY` (optional, for higher rate limits)

## Job Configuration

All jobs are configured in `databricks.yml` under the `resources.jobs` section:

```yaml
resources:
  jobs:
    apex_nemweb_realtime:
      name: APEX - NEMWEB Real-Time Ingestion
      schedule:
        quartz_cron_expression: "0 0/5 * * * ?"  # Every 5 minutes
        timezone_id: "Australia/Sydney"

    apex_epex_dayahead:
      name: APEX - EPEX Day-Ahead Ingestion
      schedule:
        quartz_cron_expression: "0 0 14 * * ?"   # Daily at 14:00 UTC
        timezone_id: "Europe/Berlin"

    apex_ercot_realtime:
      name: APEX - ERCOT Real-Time Ingestion
      schedule:
        quartz_cron_expression: "0 0/5 * * * ?"  # Every 5 minutes
        timezone_id: "America/Chicago"
```

## Deployment

Deploy all jobs to Databricks workspace:

```bash
# Deploy bundle (includes jobs)
databricks bundle deploy -p DEFAULT

# List deployed jobs
databricks jobs list --profile DEFAULT | grep APEX

# Run a job manually
databricks jobs run-now --job-name "APEX - NEMWEB Real-Time Ingestion" -p DEFAULT
```

## Environment Variables

Required environment variables for jobs:

- **ENTSOE_API_KEY**: ENTSOE Transparency Platform API token (for EPEX)
  - Register at: https://transparency.entsoe.eu/
  - Set in job compute configuration

- **ERCOT_API_KEY** (optional): ERCOT API key for higher rate limits
  - Register at: https://www.ercot.com/services/api
  - Public data available without key

- **DATABRICKS_SQL_WAREHOUSE_ID**: SQL warehouse for Delta table writes
  - Default: 4b9b953939869799 (configured in databricks.yml)

- **APEX_CATALOG**: Unity Catalog name
  - Default: apex_fresh

## Monitoring

### Job Run History
```bash
# Check recent runs
databricks jobs list-runs --job-name "APEX - NEMWEB Real-Time Ingestion" --profile DEFAULT

# Get run details
databricks jobs get-run <run-id> --profile DEFAULT
```

### Ingestion Logs
All ingestion jobs log to:
- **NEMWEB**: `apex_fresh.nemweb.ingestion_log`
- **EPEX**: `apex_fresh.epex.ingestion_log`
- **ERCOT**: `apex_fresh.ercot.ingestion_log`

Query logs:
```sql
-- Check recent NEMWEB ingestions
SELECT * FROM apex_fresh.nemweb.ingestion_log
ORDER BY start_timestamp DESC
LIMIT 10;

-- Failed ingestions today
SELECT market, data_type, error_message, start_timestamp
FROM (
  SELECT 'NEMWEB' as market, * FROM apex_fresh.nemweb.ingestion_log
  UNION ALL
  SELECT 'EPEX' as market, * FROM apex_fresh.epex.ingestion_log
  UNION ALL
  SELECT 'ERCOT' as market, * FROM apex_fresh.ercot.ingestion_log
)
WHERE status = 'FAILED'
  AND DATE(start_timestamp) = CURRENT_DATE()
ORDER BY start_timestamp DESC;
```

## Data Validation

Each ingestion service performs data quality checks:
- Timestamp validation
- Price range validation
- Duplicate detection
- Completeness checks

Failed validations are logged but don't stop ingestion.

## Error Handling

Jobs implement:
- Automatic retry on transient failures (3 retries with exponential backoff)
- Error logging to ingestion_log tables
- Alerting via Databricks job notifications
- Graceful degradation (partial data ingestion)

## Performance

- **NEMWEB**: ~300 records per 5-minute run (5 regions)
- **EPEX**: ~600 records per daily run (5 markets × 24 hours × 4-6 intervals)
- **ERCOT**: ~60 records per 5-minute run (5 settlement points × 12 intervals)

Total daily ingestion: ~100,000 records across all markets

## Dependencies

All jobs require:
```
httpx
pandas
databricks-sdk
python-dotenv
```

These are included in the application requirements.txt.

## Troubleshooting

### Job fails with "Catalog not found"
Ensure `apex_fresh` catalog is created:
```bash
python3 scripts/setup_database.py
```

### Job fails with "API key invalid"
Check environment variables in job compute configuration.

### Missing data for specific dates
Check data source availability:
- NEMWEB: Data available 2-3 minutes after interval
- EPEX: Day-ahead prices published around 13:00-14:00 UTC
- ERCOT: Real-time prices with ~5-10 minute delay

## Future Enhancements

- [ ] Backfill jobs for historical data
- [ ] Real-time streaming ingestion (Structured Streaming)
- [ ] Data quality alerting (Data Quality Monitor)
- [ ] Cross-market price correlation analysis
- [ ] Automated demand forecast ingestion
- [ ] FCAS and ancillary services data (NEMWEB)

## Related Documentation

- Ingestion Services: `app/backend/{nemweb,epex,ercot}/ingestion.py`
- API Clients: `app/backend/{nemweb,epex,ercot}/client.py`
- Database Schema: `DATABASE_SCHEMA_SUMMARY.md`
- Deployment Guide: `databricks.yml`
