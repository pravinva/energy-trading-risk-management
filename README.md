<h1 align="center">APEX Energy Trading and Risk Management Platform</h1>

<p align="center">
  <b>Airflow-style operational simplicity for energy trading workflows</b> — run dispatch, trading, risk, quant, and portfolio personas on one Databricks-native app across NEM, EPEX, and ERCOT.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=111827" alt="React Vite">
  <img src="https://img.shields.io/badge/Databricks-Apps-E36209?logo=databricks&logoColor=white" alt="Databricks Apps">
  <img src="https://img.shields.io/badge/Markets-NEM%20%7C%20EPEX%20%7C%20ERCOT-7C3AED" alt="Markets">
  <img src="https://img.shields.io/badge/License-Apache%202.0-16A34A" alt="License">
  <img src="https://img.shields.io/badge/Tests-Configured-0EA5E9" alt="Tests">
</p>

<p align="center">
  <a href="docs/APEX_NEM_PERSONA_DAY_IN_LIFE.pdf"><b>NEM Day in the Life (PDF)</b></a>
  &nbsp;|&nbsp;
  <a href="docs/APEX_EPEX_PERSONA_DAY_IN_LIFE.pdf"><b>EPEX Day in the Life (PDF)</b></a>
  &nbsp;|&nbsp;
  <a href="docs/APEX_ERCOT_PERSONA_DAY_IN_LIFE.pdf"><b>ERCOT Day in the Life (PDF)</b></a>
</p>

APEX is a Databricks App for wholesale power trading and risk operations across three markets. It combines a FastAPI backend, a React/Vite frontend, Databricks Workflows ingestion jobs, and Unity Catalog data models into one deployable platform.

## Platform Overview

APEX is designed for day-to-day commercial and operational workflows:

- Real-time market and portfolio monitoring
- Trade blotter and exposure management
- Risk analytics (VaR, stress, limits, credit)
- Quant workflows (model performance, lineage, backtests)
- Portfolio optimization and revenue stacking

For full capability detail, see:
- [Architecture](docs/APEX_MODULAR_ARCHITECTURE.md)
- [Risk Capabilities](docs/APEX_RISK_MANAGEMENT_CAPABILITIES.md)

## Markets Covered

The application currently supports:

- `NEM` (Australia / ANZ)
- `EPEX` (Europe)
- `ERCOT` (Texas / Americas)

Operational market-data details:
- [Ingestion Jobs Summary](docs/INGESTION_JOBS_SUMMARY.md)
- [Jobs Deep-Dive](jobs/README.md)

## Persona Workspaces and UI

APEX UI is persona-driven, with consistent role-based screens per market:

- `Dispatch Operator` (`/workspace/dispatch`): fleet monitor, pre-dispatch strip, offer-stack builder, recommendations
- `Power Trader` (`/workspace/trading`): market snapshot, positions, exposure, blotter
- `Risk Manager` (`/workspace/risk`): VaR dashboard, stress scenarios, limits, credit exposure
- `Quant Developer` (`/workspace/quant`): model metrics, lineage, strategy backtests, forecast diagnostics
- `Portfolio Manager` (`/workspace/portfolio`): revenue stacking, PPA book, asset benchmarking

UI references:
- [UI and Persona Matrix](docs/APEX_SCREEN_PARITY_MATRIX.md)
- [Screen Data Status](docs/SCREEN_DATA_STATUS.md)
- [Screen Data Lineage by Market](docs/SCREEN_DATA_LINEAGE_BY_MARKET.md)
- [NEM Persona Day in the Life](docs/APEX_NEM_PERSONA_DAY_IN_LIFE.pdf)
- [EPEX Persona Day in the Life](docs/APEX_EPEX_PERSONA_DAY_IN_LIFE.pdf)
- [ERCOT Persona Day in the Life](docs/APEX_ERCOT_PERSONA_DAY_IN_LIFE.pdf)

## Runtime Architecture

```text
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
        +--> Analytics, risk, and portfolio APIs
```

Deployment plane:

```text
Local repo
  -> /Workspace/Users/<user>/apex-etrm
  -> Databricks App: apex-etrm
```

Architecture detail: [APEX Modular Architecture](docs/APEX_MODULAR_ARCHITECTURE.md)

## Repository Structure

- `app/` - backend services, frontend UI, static assets, integration hooks
- `jobs/` - ingestion and analytics workflow code
- `sql/setup/` - catalog/schema/table bootstrap SQL
- `data/` - query templates, seeds, and data helpers
- `docs/` - architecture and operational documentation
- `databricks.yml` - primary bundle definition

## Local Development

1. Install dependencies:
   - `pip install -r requirements.txt`
   - `cd app/frontend && npm install`
2. Run backend:
   - `uvicorn app.backend.app:app --reload`
3. Run frontend:
   - `cd app/frontend && npm run dev`

## Dependency Files

This repository intentionally separates dependency scopes:

- `requirements.txt`  
  Primary app/backend dependency set for standard development and deployment.

- `requirements-monte-carlo.txt`  
  Optional advanced quantitative stack for professional Monte Carlo and analytics workflows.

- `apex_fresh/remote_app/requirements.txt`  
  Minimal dependency set for the alternate `apex_fresh/remote_app` runtime path.

Install patterns:

- Main app: `pip install -r requirements.txt`
- Main app with quant extras: `pip install -r requirements.txt -r requirements-monte-carlo.txt`
- Alternate remote app path: `pip install -r apex_fresh/remote_app/requirements.txt`

## Deployment

Target workspace profile should match your destination Databricks workspace.

1. Sync source:
   - `databricks sync . /Workspace/Users/<your-user>/apex-etrm -p DEFAULT`
2. Deploy app:
   - `databricks apps deploy apex-etrm --source-code-path /Workspace/Users/<your-user>/apex-etrm -p DEFAULT`
3. Verify:
   - `databricks apps get apex-etrm -p DEFAULT`

Deployment guide:
- [Deployment Runbook (PDF)](docs/APEX_Deployment_Runbook_Other_Workspace.pdf)

## Data Platform

- Primary catalog: `apex_fresh`
- Bootstrap SQL: `sql/setup/`
- Setup utility: `scripts/setup_database.py`
- Seed notes: `data/README.md`

Data references:
- [Database Summary](docs/DATABASE_SCHEMA_SUMMARY.md)
- [SQL Setup Guide](sql/setup/README.md)

## API Surface (High Level)

- Market: `/api/v1/market/*`, `/api/v1/nemweb/*`, `/api/v1/epex/*`, `/api/v1/ercot/*`
- Trading and dispatch: `/api/v1/trades/*`, `/api/v1/dispatch/*`, `/api/v1/positions/*`
- Risk and portfolio: `/api/v1/risk/*`, `/api/v1/portfolio/*`, `/api/v1/portfolio-optimization/*`
- Forecasting and analytics: `/api/v1/forecasting/*`, `/api/v1/analytics/*`

## Documentation

- [Docs Landing Page](docs/README.md)
- [Architecture](docs/APEX_MODULAR_ARCHITECTURE.md)
- [Risk Capabilities](docs/APEX_RISK_MANAGEMENT_CAPABILITIES.md)
- [UI and Persona Matrix](docs/APEX_SCREEN_PARITY_MATRIX.md)
- [Screen Data Lineage by Market](docs/SCREEN_DATA_LINEAGE_BY_MARKET.md)
- [NEM Persona Day in the Life](docs/APEX_NEM_PERSONA_DAY_IN_LIFE.pdf)
- [EPEX Persona Day in the Life](docs/APEX_EPEX_PERSONA_DAY_IN_LIFE.pdf)
- [ERCOT Persona Day in the Life](docs/APEX_ERCOT_PERSONA_DAY_IN_LIFE.pdf)
- [Database Summary](docs/DATABASE_SCHEMA_SUMMARY.md)
- [Ingestion Jobs Summary](docs/INGESTION_JOBS_SUMMARY.md)
- [Jobs Deep-Dive](jobs/README.md)
