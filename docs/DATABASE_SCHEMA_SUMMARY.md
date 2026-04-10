# APEX Database Schema Summary

## Deployment Context

- Workspace: `e2-demo-field-eng.cloud.databricks.com`
- Catalog: `apex_fresh`
- App: `apex-etrm`

## Schemas

`apex_fresh` is organized into these logical schemas:

- `market_nem`: Australian NEM market prices and operational feeds
- `market_epex`: EPEX day-ahead and related Europe pricing
- `market_ercot`: ERCOT real-time settlement point prices
- `ingestion`: landing and ingestion control data
- `trading`: trade records, offer stacks, dispatch references
- `risk`: VaR outputs and limit definitions
- `portfolio`: PPA book and revenue stacking inputs
- `analytics`: model performance, forecasts, and backtests

## Core Data Flow

1. External market APIs ingest into market schemas.
2. ETRM/raw operational payloads land in `ingestion`.
3. Normalized business entities are written to `trading`.
4. Risk and portfolio services compute downstream views.
5. Analytics/forecasting and strategy outputs are served through API routes.

## Setup Sources

- SQL bootstrap scripts: `sql/setup/`
- Setup runner: `scripts/setup_database.py`
- App/runtime config: `app.yaml`

## Related Docs

- Platform README: `../README.md`
- Setup sequence: `../sql/setup/README.md`
- Ingestion jobs: `INGESTION_JOBS_SUMMARY.md`
