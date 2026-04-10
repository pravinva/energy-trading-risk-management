# APEX Energy Trading & Risk Management Platform

APEX is a Databricks App for energy trading and risk operations across ANZ, Europe, and Americas market contexts. It ships as a single project containing a FastAPI backend, React/Vite frontend, ingestion jobs, SQL bootstrap assets, and Databricks bundle configuration.

## Current Runtime Architecture

```
React + Vite frontend (app/frontend)
        |
        v
FastAPI backend (app/backend)
        |
        v
Unity Catalog (apex_fresh.* schemas)
        |
        +--> Databricks Workflows jobs (jobs/ingestion/*)
        |
        +--> Analytics/risk/portfolio APIs

Deployment plane:
Local repo -> Workspace path (/Workspace/Users/<user>/apex-etrm)
          -> Databricks App (apex-etrm)
          -> URL: https://apex-etrm-1444828305810485.aws.databricksapps.com/
```

## Repository Layout

- `app/`: backend service, frontend UI, static build artifacts, plugin hooks
- `jobs/`: ingestion and analytics workflow code
- `sql/setup/`: catalog/schema/table bootstrap SQL
- `data/`: query templates, seeds, and schema data helpers
- `docs/`: architecture and operational documentation
- `databricks.yml`: primary bundle (app + jobs resources)

## Local Development

1. Install Python and Node dependencies:
   - `pip install -r requirements.txt`
   - `cd app/frontend && npm install`
2. Start backend:
   - `uvicorn app.backend.app:app --reload`
3. Start frontend dev server in a second terminal:
   - `cd app/frontend && npm run dev`

## Deployment (Current)

Use the workspace/app profile that targets `https://e2-demo-field-eng.cloud.databricks.com`.

1. Sync source to workspace:
   - `databricks sync . /Workspace/Users/<your-user>/apex-etrm -p DEFAULT`
2. Deploy app from workspace source:
   - `databricks apps deploy apex-etrm --source-code-path /Workspace/Users/<your-user>/apex-etrm -p DEFAULT`
3. Verify status:
   - `databricks apps get apex-etrm -p DEFAULT`

## Data Platform

- Primary catalog: `apex_fresh`
- Bootstrap scripts: `sql/setup/`
- Setup utility: `scripts/setup_database.py`
- Seed and data notes: `data/README.md`

## API Surface (High Level)

- Market data: `/api/v1/market/*`, `/api/v1/nemweb/*`, `/api/v1/epex/*`, `/api/v1/ercot/*`
- Trading and dispatch: `/api/v1/trades/*`, `/api/v1/dispatch/*`, `/api/v1/positions/*`
- Risk and portfolio: `/api/v1/risk/*`, `/api/v1/portfolio/*`, `/api/v1/portfolio-optimization/*`
- Forecasting and analytics: `/api/v1/forecasting/*`, `/api/v1/analytics/*`

## Documentation Index

- Docs landing page: `docs/README.md`
- Architecture: `docs/APEX_MODULAR_ARCHITECTURE.md`
- Database summary: `docs/DATABASE_SCHEMA_SUMMARY.md`
- Ingestion jobs summary: `docs/INGESTION_JOBS_SUMMARY.md`
- Jobs deep-dive: `jobs/README.md`
