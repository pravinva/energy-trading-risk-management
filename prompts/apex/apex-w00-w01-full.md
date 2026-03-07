# APEX — Energy Analytics Platform on Databricks
## W00 + W01: Project Foundation & Design System
### Cursor Agent Instructions

---

# W00 — Project Foundation

## OBJECTIVE
Create the project scaffold for APEX, a multi-market energy analytics platform on Databricks Apps. APEX sits alongside existing ETRM systems (Endur, Aligne, Triple Point) as the analytics, risk, and data intelligence layer. It is NOT a trade execution system.

Three markets: **NEM (Australia) · EPEX (Europe) · ERCOT (Americas)**

## REFERENCE REPOSITORIES
Review before writing any configuration:
- https://github.com/sourabhghose/databricks-energy-copilot — DAB structure, app.yaml, NEM simulator pattern
- https://github.com/dgokeeffe/databricks-nemweb-lab — nemweb_datasource.py for live NEMWEB ingestion

## WORKSPACE
- URL: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
- CLI Profile: fe-vm
- Catalog: apex (created in W02)

## STEP 1: Verify connectivity
Using Databricks CLI MCP with fe-vm profile: list catalogs, list apps, list secret scopes. Report any failures and stop.

## STEP 2: Create GitHub repository
Name: apex-etrm
Description: "APEX — Multi-Market Energy Analytics Platform on Databricks"
Public, main branch, Python + Node .gitignore

## STEP 3: Directory structure

```
apex-etrm/
├── .cursor/rules/project.mdc
├── .github/workflows/
│   └── deploy.yml
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── engines/
│   │   │   ├── pnl.py
│   │   │   ├── var.py
│   │   │   ├── position.py
│   │   │   └── dispatch.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── user.py
│   │   │   ├── market.py
│   │   │   ├── trades.py
│   │   │   ├── positions.py
│   │   │   ├── dispatch.py
│   │   │   ├── risk.py
│   │   │   ├── portfolio.py
│   │   │   └── analytics.py
│   │   └── tests/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── styles/
│   │   │   │   ├── tokens.css
│   │   │   │   ├── global.css
│   │   │   │   └── trading.css
│   │   │   ├── components/
│   │   │   │   ├── primitives/
│   │   │   │   └── trading/
│   │   │   ├── pages/
│   │   │   │   ├── MarketSelector.tsx
│   │   │   │   ├── PersonaSelector.tsx
│   │   │   │   ├── dispatch/
│   │   │   │   ├── trading/
│   │   │   │   ├── risk/
│   │   │   │   ├── quant/
│   │   │   │   └── portfolio/
│   │   │   ├── api/hooks/
│   │   │   ├── store/
│   │   │   │   ├── marketStore.ts
│   │   │   │   ├── tradingStore.ts
│   │   │   │   └── dispatchStore.ts
│   │   │   ├── config/
│   │   │   │   └── genie-questions.ts
│   │   │   ├── router.ts
│   │   │   └── main.tsx
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   ├── pipelines/
│   │   ├── etrm_ingestion.py
│   │   └── market_simulator_orchestrator.py
│   ├── plugins/
│   └── app.yaml
├── data/
│   ├── schema/
│   ├── seeds/
│   │   ├── market/
│   │   │   ├── simulators/
│   │   │   │   ├── nem_simulator.py
│   │   │   │   ├── epex_simulator.py
│   │   │   │   ├── ercot_simulator.py
│   │   │   │   └── orchestrator.py
│   │   │   └── backfill/
│   │   │       ├── nem_backfill.py
│   │   │       ├── epex_backfill.py
│   │   │       ├── ercot_backfill.py
│   │   │       └── run_all_backfills.py
│   │   ├── trades/
│   │   └── reference/
│   └── queries/
│       ├── market/
│       ├── trades/
│       ├── risk/
│       ├── portfolio/
│       └── analytics/
├── resources/
│   ├── app.yml
│   ├── jobs.yml
│   └── pipelines.yml
├── databricks.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## STEP 4: Write .cursor/rules/project.mdc

```
APEX is a multi-market energy analytics platform on Databricks Apps. It provides
analytics, risk, and data intelligence alongside existing ETRM systems
(Endur, Aligne, Triple Point). It is NOT a trade execution system.
APEX ingests from ETRMs via DLT; APEX does not book trades.

Markets: NEM (Australia/AUD), EPEX (Europe/EUR), ERCOT (Americas/USD).

Stack: FastAPI Python 3.11 backend, React 18 TypeScript Vite frontend,
Lakebase (psycopg3) for low-latency operational writes (VaR results,
offer stacks, backtest runs), Delta tables as analytics + Genie layer,
DLT for ETRM ingestion, MLflow for price forecast and dispatch models,
Databricks SQL Warehouse as analytics query engine.

DESIGN SYSTEM — Option D (Slate + Coral):
- Background: #1B1F23. NOT black. Warm slate only.
- Primary accent: #FF6B6B (coral — Databricks brand aligned)
- Positive P&L: #34D399 (emerald green)
- Negative P&L: #FF6B6B (coral red)
- JetBrains Mono for ALL numeric values. No exceptions.
- Inter for all UI text and labels.
- No emoji anywhere. Status via colour only.
- Panel border-radius: 5px (radius-md). Tables: 0px (radius-none).
- Market accent: NEM=#60A5FA, EPEX=#A78BFA, ERCOT=#FBBF24

ARCHITECTURE:
- Lakebase (psycopg3): VaR results, offer stacks, backtest metadata
- Delta tables: trades, positions, market data — all Genie queryable
- DLT pipeline: ETRM → bronze → silver → gold positions
- Three continuous simulators: NEM (30s), EPEX (5min), ERCOT (30s)
- Genie: one space per market, pre-built questions per persona

TRADING CONVENTIONS:
- Positions: long=positive MW, short=negative MW
- P&L: MTM against current market price vs avg entry
- VaR: 1-day 95% and 99%, Monte Carlo 10,000 simulations
- Currency always shown: A$ for NEM, € for EPEX, $ for ERCOT
- Source always shown: which ETRM did this data come from

RULES:
- All financial arithmetic uses Python Decimal, TypeScript decimal.js
- No float for prices, P&L, MW values
- No inline SQL in Python routes — all SQL in data/queries/
- TypeScript strict mode, no any
- mypy --strict on all backend
- API prefix: /api/v1/
- All routes accept ?market=NEM|EPEX|ERCOT parameter
- Every Lakebase write is async-followed by Delta append for Genie
```

## STEP 5: package.json
Dependencies:
- react 18, react-dom 18, typescript 5, vite 5
- @tanstack/react-router, @tanstack/react-query, @tanstack/react-table
- recharts (only charting library)
- zustand
- axios, date-fns, decimal.js
- react-hot-toast
- Dev: vitest, @testing-library/react, eslint, @typescript-eslint

## STEP 6: app.yaml
```yaml
command: uvicorn app.backend.app:app --host 0.0.0.0 --port 8000
resources:
  - name: apex-db
    resource_type: DATABASE
    database:
      engine_name: lakebase
env:
  - name: DATABRICKS_WORKSPACE_URL
  - name: APEX_ENVIRONMENT
    value: dev
```

## STEP 7: databricks.yml
```yaml
bundle:
  name: apex-etrm

workspace:
  host: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com

resources:
  apps:
    apex:
      name: apex
      source_code_path: ./app
  jobs:
    apex-market-simulator:
      source: resources/jobs.yml
  pipelines:
    apex-etrm-ingestion:
      source: resources/pipelines.yml
```

## STEP 8: requirements.txt
```
fastapi>=0.111
uvicorn[standard]
psycopg[binary]>=3.1
databricks-sdk>=0.25
databricks-sql-connector
python-dotenv
pydantic>=2.0
pydantic-settings
numpy
scipy
pytest
httpx
cachetools
```

## STEP 9: .env.example
```
DATABRICKS_HOST=https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com
DATABRICKS_TOKEN=
LAKEBASE_HOST=
LAKEBASE_DATABASE=apex
LAKEBASE_PORT=5432
SQL_WAREHOUSE_ID=
APEX_ENVIRONMENT=dev
```

## STEP 10: README.md
Professional README. What APEX is and what it is NOT (1 paragraph each). Three-market architecture ASCII diagram. Five persona descriptions. Local dev setup. Deployment instructions.

## SUCCESS CRITERIA
1. `databricks --profile fe-vm workspace list` succeeds
2. GitHub repo apex-etrm exists
3. `tree -L 4` matches specification
4. `npm ci` completes
5. `uvicorn app.backend.app:app` starts without import errors
6. `pytest tests/` passes (0 collected OK)

## COMPLETION ARTIFACT
completions/W00-foundation.md
Commit: "chore: W00 complete — APEX project foundation"

---

# W01 — Design System (Option D: Slate + Coral)

## PREREQUISITE CHECK
Verify completions/W00-foundation.md exists.

## OBJECTIVE
Build the APEX design system. Target aesthetic: professional enterprise analytics — Databricks-native, warm dark slate, coral primary accent. Reference: Databricks UI, Grafana Enterprise, Retool dark mode. NOT Bloomberg terminal. NOT pure black.

---

## FILE: app/frontend/src/styles/tokens.css

```css
:root {
  /* ── Backgrounds — warm slate, not cold black ── */
  --color-bg-void:    #13181D;  /* page background */
  --color-bg-base:    #1B1F23;  /* topbar, sidebar */
  --color-bg-surface: #22272C;  /* panel headers, hover */
  --color-bg-raised:  #292E35;  /* selected rows, active nav */
  --color-bg-panel:   #1F2429;  /* panel bodies */
  --color-bg-overlay: #2D333B;  /* modals, dropdowns */
  --color-bg-input:   #13181D;  /* inputs */

  /* ── Borders ── */
  --color-border-subtle:  #2A3038;
  --color-border-default: #343C47;
  --color-border-strong:  #434D5C;
  --color-border-active:  #5A6A7E;

  /* ── Text ── */
  --color-text-primary:   #E2E8F0;
  --color-text-secondary: #8896AA;
  --color-text-tertiary:  #4A5568;
  --color-text-muted:     #2D3748;
  --color-text-inverse:   #13181D;

  /* ── Trading semantics (most critical) ── */
  --color-bid:          #34D399;
  --color-bid-dim:      #34D39915;
  --color-offer:        #FF6B6B;
  --color-offer-dim:    #FF6B6B15;
  --color-pnl-positive: #34D399;
  --color-pnl-negative: #FF6B6B;
  --color-pnl-flat:     #8896AA;
  --color-warning:      #FBBF24;
  --color-warning-dim:  #FBBF2415;
  --color-critical:     #FF6B6B;
  --color-neutral:      #60A5FA;
  --color-neutral-dim:  #60A5FA15;
  --color-accent:       #FF6B6B;

  /* ── Market accent colours ── */
  --color-market-nem:    #60A5FA;
  --color-market-nem-dim:#60A5FA18;
  --color-market-epex:   #A78BFA;
  --color-market-epex-dim:#A78BFA18;
  --color-market-ercot:  #FBBF24;
  --color-market-ercot-dim:#FBBF2418;

  /* ── Market status ── */
  --color-market-open:    #34D399;
  --color-market-closed:  #8896AA;
  --color-market-auction: #FBBF24;
  --color-price-up:       #34D399;
  --color-price-down:     #FF6B6B;
  --color-price-unchanged:#8896AA;

  /* ── Persona colours ── */
  --color-persona-dispatch:  #60A5FA;
  --color-persona-trader:    #FF6B6B;
  --color-persona-risk:      #FBBF24;
  --color-persona-quant:     #A78BFA;
  --color-persona-portfolio: #34D399;

  /* ── Typography ── */
  --font-ui:   'Inter', -apple-system, sans-serif;
  --font-data: 'JetBrains Mono', 'Fira Code', monospace;

  /* ── Font sizes ── */
  --text-2xs: 0.625rem;    /* 10px */
  --text-xs:  0.6875rem;   /* 11px */
  --text-sm:  0.75rem;     /* 12px */
  --text-base:0.8125rem;   /* 13px */
  --text-md:  0.875rem;    /* 14px */
  --text-lg:  1rem;        /* 16px */
  --text-xl:  1.25rem;     /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 2rem;        /* 32px */

  /* ── Spacing ── */
  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px; --space-8: 32px;

  /* ── Radius ── */
  --radius-none: 0;
  --radius-sm:   3px;
  --radius-md:   5px;
  --radius-lg:   8px;

  /* ── Transitions ── */
  --transition-price: background-color 150ms ease;
  --transition-ui:    all 150ms ease;
}
```

## FILE: app/frontend/src/styles/global.css

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  background: var(--color-bg-void);
  color: var(--color-text-primary);
  font-family: var(--font-ui);
  font-size: 13px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

table { border-collapse: collapse; width: 100%; }
td, th { padding: 7px 12px; }
th {
  font-size: var(--text-xs); font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-text-tertiary);
  border-bottom: 1px solid var(--color-border-subtle);
  text-align: left;
}
td { font-size: var(--text-sm); color: var(--color-text-primary); }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--color-bg-base); }
::-webkit-scrollbar-thumb { background: var(--color-border-strong); border-radius: 3px; }

input, select, textarea {
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  padding: 6px 10px;
  outline: none;
  transition: border-color 150ms;
}
input:focus, select:focus { border-color: var(--color-border-active); }

button { cursor: pointer; font-family: var(--font-ui); }
a { color: inherit; text-decoration: none; }
```

## FILE: app/frontend/src/styles/trading.css

```css
/* ── Price flash animation ── */
@keyframes price-flash {
  0%   { background-color: rgba(255,255,255,0.15); }
  100% { background-color: transparent; }
}
.price-flash { animation: price-flash 300ms ease-out; }

/* ── Price direction ── */
.price-up   { color: var(--color-price-up); }
.price-down { color: var(--color-price-down); }

/* ── Bid/offer ── */
.bid   { color: var(--color-bid); }
.offer { color: var(--color-offer); }

/* ── P&L ── */
.pnl-positive { color: var(--color-pnl-positive); font-family: var(--font-data); }
.pnl-negative { color: var(--color-pnl-negative); font-family: var(--font-data); }
.pnl-flat     { color: var(--color-pnl-flat);     font-family: var(--font-data); }

/* ── Data typography ── */
.font-data   { font-family: var(--font-data); }
.tabular     { font-variant-numeric: tabular-nums; letter-spacing: 0; }
.label-caps  { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.1em;
               text-transform: uppercase; color: var(--color-text-secondary); }

/* ── Numeric columns — always apply these ── */
.mono-price  { font-family: var(--font-data); font-variant-numeric: tabular-nums; text-align: right; }
.mono-mw     { font-family: var(--font-data); font-variant-numeric: tabular-nums; text-align: right; }
.mono-pct    { font-family: var(--font-data); font-variant-numeric: tabular-nums; text-align: right; }
.mono-eur    { font-family: var(--font-data); font-variant-numeric: tabular-nums; text-align: right; }

/* ── Row highlights ── */
.row-long  { background: var(--color-bid-dim) !important; }
.row-short { background: var(--color-offer-dim) !important; }

/* ── Market-specific accents ── */
.market-nem   { color: var(--color-market-nem); }
.market-epex  { color: var(--color-market-epex); }
.market-ercot { color: var(--color-market-ercot); }
.market-nem-bg   { background: var(--color-market-nem-dim); border-color: var(--color-market-nem); }
.market-epex-bg  { background: var(--color-market-epex-dim); border-color: var(--color-market-epex); }
.market-ercot-bg { background: var(--color-market-ercot-dim); border-color: var(--color-market-ercot); }

/* ── Source provenance tag ── */
.source-tag {
  display: inline-block; padding: 1px 6px; border-radius: 2px;
  font-size: var(--text-2xs); font-weight: 600; letter-spacing: 0.06em;
  background: var(--color-bg-raised); color: var(--color-text-secondary);
  font-family: var(--font-data);
}
.source-fresh  { color: var(--color-bid); }
.source-stale  { color: var(--color-warning); }
.source-delayed{ color: var(--color-offer); }
```

---

## ETRM PRIMITIVE COMPONENTS

### Panel.tsx
Props: title, subtitle, actions (ReactNode), market ('nem'|'epex'|'ercot'|'neutral'), badge (string), className, children.

Layout:
- Outer: border-radius radius-md, border 1px border-subtle, background bg-panel
- Header: background bg-surface, padding space-3 space-4, border-bottom border-subtle
- Title: label-caps + text-secondary
- Market prop adds a 2px top border in the market accent colour
- Badge: small rounded tag in market colour

### DataTable.tsx
High-frequency update safe. useMemo on data. Support:
- onRowClick, onRowDoubleClick
- selectedRowId
- highlightRowFn: (row) => 'long'|'short'|'flat'|null
- Column types: 'price'|'mw'|'pct'|'eur'|'usd'|'aud'|'text'|'badge'|'source'
  Currency columns auto-select mono-price and prepend correct symbol
- Loading shimmer, empty state
- Compact mode (28px rows) vs default (36px rows)
- Border-radius: none on table itself

### OrderBook.tsx
Bid/offer ladder. Props: bids [{price, volume, cumulative}], offers, spread, lastTradePrice, currency.
- Two columns (Bids left green, Offers right coral)
- Midpoint price in font-data text-md centre
- Cumulative volume bars (CSS, 50px)
- Row flash on price update

### PriceTicker.tsx
Single instrument. Props: instrument, lastPrice, change, changePct, bid, offer, volume, status, currency.
- Last price: font-data text-2xl, colour by change direction
- ▲▼ characters for direction (standard market convention, not emoji)
- Bid in --color-bid, offer in --color-offer

### Metric.tsx
KPI display. Props: label, value, delta, deltaDirection, currency, size ('sm'|'md'|'lg').
- Value always font-data
- Delta: small text below, up/down colour

### StatusBadge.tsx
Colour only. Labels: OPEN/CLOSED/AUCTION/PENDING/FILLED/PARTIAL/CANCELLED/BREACH/FRESH/STALE/DELAYED.
Each maps to specific palette colour. No icons.

### SourceProvenanceBar.tsx
Shows ETRM data freshness inline. Props: sourceSystem, market, lastSyncAt, lagSeconds, recordCount.
- Renders: "[ENDUR_SIM] → last sync 14:32:05 (8s ago) · 847 positions"
- Colour by lag: green <60s, amber 1–5min, red >5min
- Used in every workspace that shows ingested data

### OfferBand.tsx
Single offer stack band for dispatch. Props: bandIndex (1–10), price (Decimal), volume (Decimal), isSelected, onPriceChange, onVolumeChange. Validates ascending price constraint.

### Sparkline.tsx
Compact SVG time series. Props: data[], width=80, height=24, positive (bool for colour).

### GenieSidePanel.tsx
Collapsible right panel. Props: market, persona.
- Width 320px when open, 40px (toggle tab only) when closed
- Shows pre-built question chips from config/genie-questions.ts filtered by market + persona
- Embedded Genie iframe with correct space URL
- "Open in full Genie" external link

### ConfirmationToast.tsx
React-hot-toast custom. Shows action type, instrument, values. Auto-dismiss 4s. No emoji.

### MarketBadge.tsx
Small pill showing market name in its accent colour. Props: market.
Used in topbar and wherever cross-market context is needed.

---

## SUCCESS CRITERIA
1. `npm run build` zero errors
2. Vitest passes for all primitives
3. Option D colours verified: background is #1B1F23 (NOT #080c14)
4. Positive values are #34D399, negative are #FF6B6B — not original green/red
5. All numeric values render in JetBrains Mono (verify computed styles)
6. Panel border-radius is 5px, not 0
7. SourceProvenanceBar renders with correct colour thresholds
8. GenieSidePanel opens/closes correctly

## COMPLETION ARTIFACT
completions/W01-design-system.md
Commit: "feat: W01 complete — APEX design system Option D"
