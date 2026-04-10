# APEX Energy Trading & Risk Management Platform

APEX is a Databricks App for energy trading and risk operations across ANZ, Europe, and Americas market contexts. It ships as a single project containing a FastAPI backend, React/Vite frontend, ingestion jobs, SQL bootstrap assets, and Databricks bundle configuration.

## What This App Does

APEX provides persona-based workspaces for end-to-end energy trading operations:

- Dispatch decisions and offer-stack analysis
- Trading blotter, exposure, and market monitoring
- VaR, stress testing, credit exposure, and limit monitoring
- Quant model performance, lineage, and strategy backtests
- Portfolio revenue stacking, PPA valuation, and benchmarking

Details:
- Capability deep-dive: `docs/APEX_MODULAR_ARCHITECTURE.md`
- Risk function coverage: `docs/APEX_RISK_MANAGEMENT_CAPABILITIES.md`
- Screen and panel parity matrix: `docs/APEX_SCREEN_PARITY_MATRIX.md`

## Markets Supported

The app is built to operate across three power markets:

- `NEM` (Australia / ANZ)
- `EPEX` (Europe)
- `ERCOT` (Texas / Americas)

Market data ingestion and job behavior:
- Ingestion summary: `docs/INGESTION_JOBS_SUMMARY.md`
- Jobs technical detail: `jobs/README.md`

## Persona Workspaces and UI

APEX UI is organized around five personas (each available per market context):

- `Dispatch Operator` (`/workspace/dispatch`): fleet monitor, pre-dispatch strip, offer stack builder, ML recommendations
- `Power Trader` (`/workspace/trading`): flow summary, market snapshot, position book, exposure, trade blotter
- `Risk Manager` (`/workspace/risk`): VaR dashboard, stress scenarios, limit monitor, credit exposure
- `Quant Developer` (`/workspace/quant`): model performance, model lineage, strategy backtests, forecast-vs-actual
- `Portfolio Manager` (`/workspace/portfolio`): revenue stacking simulator, PPA book, asset benchmarking

UI alignment reference:
- Persona and panel mapping: `docs/APEX_SCREEN_PARITY_MATRIX.md`
- Data visibility notes: `docs/SCREEN_DATA_STATUS.md`

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

Repository architecture reference:
- `docs/APEX_MODULAR_ARCHITECTURE.md`

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

Deployment runbook for new workspaces:
- `docs/APEX_Deployment_Runbook_Other_Workspace.pdf`

## Data Platform

- Primary catalog: `apex_fresh`
- Bootstrap scripts: `sql/setup/`
- Setup utility: `scripts/setup_database.py`
- Seed and data notes: `data/README.md`

Data model references:
- Database summary: `docs/DATABASE_SCHEMA_SUMMARY.md`
- Setup order and SQL details: `sql/setup/README.md`

## API Surface (High Level)

- Market data: `/api/v1/market/*`, `/api/v1/nemweb/*`, `/api/v1/epex/*`, `/api/v1/ercot/*`
- Trading and dispatch: `/api/v1/trades/*`, `/api/v1/dispatch/*`, `/api/v1/positions/*`
- Risk and portfolio: `/api/v1/risk/*`, `/api/v1/portfolio/*`, `/api/v1/portfolio-optimization/*`
- Forecasting and analytics: `/api/v1/forecasting/*`, `/api/v1/analytics/*`

## Documentation Index

- Docs landing page: `docs/README.md`
- Architecture: `docs/APEX_MODULAR_ARCHITECTURE.md`
- Risk capabilities: `docs/APEX_RISK_MANAGEMENT_CAPABILITIES.md`
- UI/persona matrix: `docs/APEX_SCREEN_PARITY_MATRIX.md`
- Database summary: `docs/DATABASE_SCHEMA_SUMMARY.md`
- Ingestion jobs summary: `docs/INGESTION_JOBS_SUMMARY.md`
- Jobs deep-dive: `jobs/README.md`
