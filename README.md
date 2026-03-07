# APEX Energy Trading & Risk Management Platform

APEX is a Databricks Apps-based energy trading and risk management platform with persona workspaces for dispatch, trading, risk, quant, and portfolio workflows. It combines a FastAPI backend, a React/TypeScript frontend, and Lakebase-oriented operational storage into one deployable application via Databricks Asset Bundles.

## Architecture

```
[React + Vite frontend] -> [FastAPI API + static host] -> [Lakebase Postgres]
                                      |
                                      v
                           [Databricks Apps Runtime]
                                      |
                                      v
                           [Databricks Asset Bundles]
```

## Local Development

1. Ensure Python 3.11 and Node 20 are installed.
2. Install Python deps: `pip install -r requirements.txt`
3. Install frontend deps: `cd app/frontend && npm install`
4. Start backend: `uvicorn app.backend.app:app --reload`
5. In another shell, start frontend dev server: `cd app/frontend && npm run dev`

## Data Re-Seeding

Data schema and seed flow are documented in `data/README.md`.

## Deployment (DAB)

1. Authenticate Databricks CLI profile: `databricks auth login https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com --profile fe-vm`
2. Validate bundle: `databricks bundle validate --profile fe-vm`
3. Deploy to dev target: `databricks bundle deploy -t dev --profile fe-vm`
4. Deploy app: `databricks apps deploy nexus-energy-trading-app --profile fe-vm`

## Standalone Fresh App (New Catalog)

For the clean implementation path that does not modify the existing app:

- App package: `apex_fresh/`
- New catalog: `apex_fresh`
- Ordered workflow runner: `python -m apex_fresh.scripts.run_w04_w05_w03`
- Databricks bundle: `databricks.apex-fresh.yml`
- App config: `app.apex-fresh.yaml`

This path enforces `W04` before `W05`, and `W05` before `W03` simulator startup.

## APEX API Surface

- `GET /api/v1/market/*` market summary, current prices, predispatch, forward curves
- `POST /api/v1/trades/entry` and `GET /api/v1/trades/blotter`
- `GET /api/v1/positions/book`
- `POST /api/v1/dispatch/offer-stack`, `GET /api/v1/dispatch/recommendations/{asset_id}`
- `POST /api/v1/risk/var/calculate`, `GET /api/v1/risk/limits/status`
- `GET /api/v1/portfolio/revenue-stacking`, `GET /api/v1/portfolio/ppa-book`
- `GET /api/v1/analytics/model-performance`, `GET /api/v1/analytics/backtests`

## Plugin Interface Pattern

Plugin entry points live under `app/plugins/` and are imported by feature modules. Each plugin should expose a typed integration boundary so private integrations can be added without changing public frontend and backend contracts.
