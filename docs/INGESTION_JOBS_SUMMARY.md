# APEX Ingestion Jobs Summary

## Active Market Jobs

Databricks jobs are defined in `databricks.yml` and deploy under bundle `apex-etrm`.

- `APEX - NEMWEB Real-Time Ingestion`
  - Script: `jobs/ingestion/nemweb_real_time.py`
  - Cadence: every 5 minutes
  - Target: `apex_fresh.market_nem.prices`

- `APEX - EPEX Day-Ahead Ingestion`
  - Script: `jobs/ingestion/epex_day_ahead.py`
  - Cadence: daily (Europe/Berlin schedule)
  - Target: `apex_fresh.market_epex.prices`

- `APEX - ERCOT Real-Time Ingestion`
  - Script: `jobs/ingestion/ercot_real_time.py`
  - Cadence: every 5 minutes
  - Target: `apex_fresh.market_ercot.lmp`

## Runtime Notes

- Jobs run as Databricks Workflows with bundle-managed metadata.
- HTTP ingestion dependencies are provided through `httpx` and `pandas`.
- API keys (for external providers) should be configured via environment variables or secrets.

## Deployment

Use the bundle to update workflow resources:

```bash
databricks bundle deploy -t dev -p DEFAULT
```

Inspect deployed jobs:

```bash
databricks jobs list -p DEFAULT
```

## Related Docs

- Job details: `jobs/README.md`
- Catalog/schema summary: `DATABASE_SCHEMA_SUMMARY.md`
- App architecture and deploy flow: `../README.md`
