# APEX — Energy Trading & Risk Management Platform
## Workstream Index

This is a complete, from-scratch ETRM demo platform for power generation personas. It is NOT the NEXUS market intelligence app. It is a functioning trading, dispatch, and risk management system where traders, dispatch operators, quants, risk managers, and portfolio managers actually work — entering trades, building offer stacks, running VaR, backtesting strategies, and managing portfolio P&L.

The Databricks platform is the engine: Lakebase is the operational trade and position database, MLflow serves pricing and dispatch models, Genie answers risk and P&L queries in natural language, DLT maintains the market data foundation.

**App name: APEX**
**Repo: apex-etrm**
**Workspace: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/**
**CLI Profile: fe-vm**

### Workstream Map
- W00: Project Foundation
- W01: Design System
- W02: Database Schema (trade book, positions, risk, market data)
- W03: Market Data Seeds — ANZ
- W04: Market Data Seeds — Europe + Americas
- W05: Trade Book Seeds (counterparties, instruments, pre-seeded positions)
- W06: Backend Core (FastAPI, four-tier serving, auth)
- W07: Market Data API
- W08: Trade Management API (deal entry, position calc, P&L engine)
- W09: Dispatch & Offer Stack API
- W10: Risk Engine API (VaR Monte Carlo, stress testing, limits)
- W11: Portfolio API (revenue stacking, PPA, benchmarking)
- W12: Frontend Shell (persona selector, workspace layout)
- W13: Dispatch Console
- W14: Trading Blotter
- W15: Risk Dashboard
- W16: Quant Console
- W17: Portfolio Dashboard
- W18: Integration & Deployment

---

# W00 — Project Foundation
## APEX ETRM Platform
### Cursor Agent Instructions

---

## OBJECTIVE
Create the project scaffold for APEX, a functioning energy trading and risk management demo platform. This is a separate application from NEXUS. New GitHub repository. Same target workspace.

---

## REFERENCE REPOSITORIES
Review before writing any configuration:
- https://github.com/sourabhghose/databricks-energy-copilot — DAB structure, app.yaml pattern, NEM simulator
- https://github.com/dgokeeffe/databricks-nemweb-lab — nemweb_datasource.py for live NEMWEB ingestion, liquid clustering recommendation

---

## WORKSPACE
- URL: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
- CLI Profile: fe-vm
- Catalog: apex (new — created in W02)

---

## STEP 1: Verify connectivity
Using Databricks CLI MCP with fe-vm profile: list catalogs, list apps, list secret scopes. Report any failures and stop.

---

## STEP 2: Create GitHub repository
Name: apex-etrm
Description: "APEX — Energy Trading & Risk Management Platform on Databricks"
Public, main branch, Python + Node .gitignore

---

## STEP 3: Directory structure

```
apex-etrm/
├── .cursor/rules/project.mdc
├── .github/workflows/
│   └── deploy-public.yml
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── pnl.py          # P&L calculation engine
│   │   │   ├── var.py          # VaR Monte Carlo engine
│   │   │   ├── position.py     # Position aggregation engine
│   │   │   └── dispatch.py     # Dispatch recommendation engine
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── user.py
│   │   │   ├── market.py
│   │   │   ├── trades.py
│   │   │   ├── positions.py
│   │   │   ├── dispatch.py
│   │   │   ├── risk.py
│   │   │   └── portfolio.py
│   │   └── tests/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── styles/
│   │   │   ├── components/
│   │   │   │   ├── primitives/
│   │   │   │   └── trading/    # ETRM-specific components
│   │   │   ├── pages/
│   │   │   │   ├── PersonaSelector.tsx
│   │   │   │   ├── dispatch/
│   │   │   │   ├── trading/
│   │   │   │   ├── risk/
│   │   │   │   ├── quant/
│   │   │   │   └── portfolio/
│   │   │   ├── api/
│   │   │   │   └── hooks/
│   │   │   ├── store/          # Zustand state for trading session
│   │   │   ├── router.ts
│   │   │   └── main.tsx
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   ├── plugins/
│   │   └── __init__.py
│   └── app.yaml
├── data/
│   ├── schema/
│   ├── seeds/
│   │   ├── market/
│   │   ├── trades/
│   │   └── reference/
│   └── queries/
│       ├── market/
│       ├── trades/
│       ├── risk/
│       └── portfolio/
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

---

## STEP 4: Write .cursor/rules/project.mdc

APEX is an energy trading and risk management (ETRM) demo platform on Databricks Apps. It serves five power generation personas: dispatch operator, power trader, quant developer, risk manager, portfolio manager.

Stack: FastAPI (Python 3.11) backend, React 18 TypeScript Vite frontend, Lakebase (psycopg3) as the operational trade and position database, MLflow model serving for price forecasts and dispatch recommendations, Databricks SQL Warehouse as analytics fallback.

APEX is a functioning ETRM application — users enter trades, build offer stacks, run VaR, backtest strategies. It is not a dashboard. Every workflow must be completable end-to-end.

Design principles:
- Dark theme only. Background #080c14. No light mode. Ever.
- JetBrains Mono for ALL numerical values. Price, MW, %, P&L, VaR — all monospace. No exceptions.
- Inter for all UI text, labels, headings.
- No emoji anywhere. No icons for status — colour only. No decorative elements.
- Data density is a feature. Traders work on multi-monitor setups. Use the space.
- Positive P&L: #00c99a. Negative P&L: #e05252. Flat/neutral: #7d92b0.
- Bid/offer convention: green for bids/longs, red for offers/shorts (universal trading convention).
- Column headers: uppercase, 0.08em letter-spacing, --color-text-secondary.
- Numbers: always right-aligned in tables. Always tabular numerals.
- No rounded corners on data tables, order books, blotters. Sharp edges.
- Status: colour-coded only. No icons, no emoji, no tick/cross characters.
- Price flash on update: white at 0% opacity, 300ms fade — standard trading terminal behaviour.

Architecture principles:
- Lakebase (psycopg3): primary operational store for trades, positions, bid stacks, VaR results.
- Four-tier serving (from sourabhghose/databricks-energy-copilot): Lakebase → snapshots → SQL Warehouse → cache.
- All SQL in data/queries/ — never inline in Python.
- Python type hints mandatory. TypeScript strict mode. No any.
- API prefix: /api/v1/
- Engines (pnl.py, var.py, position.py, dispatch.py) are pure Python calculation modules — no FastAPI imports, fully testable in isolation.

Trading domain conventions:
- Positions: long is positive MW, short is negative MW.
- P&L: mark-to-market (MTM) against current market price vs. trade price × volume.
- VaR: 1-day 95% and 99% confidence intervals, Monte Carlo 10,000 simulations.
- Offer stack: price bands in $/MWh ascending, MW allocation per band.
- FCAS: separate offer stacks per service (raise6sec, lower6sec, raisereg, lowerreg, raise5min, lower5min).

Testing:
- Every engine function must have a unit test.
- Every API route must have an integration test.
- Every frontend component must have a Vitest snapshot test.
- No commit without green tests.

---

## STEP 5: Write package.json

Dependencies:
- react 18, react-dom 18, typescript 5, vite 5
- @tanstack/react-router, @tanstack/react-query, @tanstack/react-table
- recharts (ONLY charting library)
- zustand (trading session state — selected instrument, active persona, open orders)
- axios, date-fns, decimal.js (for precise financial arithmetic — never use floating point for prices)
- react-hot-toast (trade confirmation notifications — professional style, no emoji)
- Dev: vitest, @testing-library/react, eslint, @typescript-eslint

---

## STEP 6: Write app.yaml
command: uvicorn app.backend.app:app --host 0.0.0.0 --port 8000
resources: Lakebase database "apex-db"
env: DATABRICKS_WORKSPACE_URL, APEX_ENVIRONMENT

## STEP 7: Write databricks.yml
Use sourabhghose/databricks-energy-copilot structure as reference.
Workspace: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
Targets: dev (fe-vm) and prod.
Includes: resources/*.yml

## STEP 8: Write requirements.txt
fastapi, uvicorn[standard], psycopg[binary], databricks-sdk, databricks-sql-connector, python-dotenv, pydantic>=2.0, numpy, scipy (for VaR calculations), pytest, httpx, cachetools

## STEP 9: Write .env.example and .gitignore (standard patterns)

## STEP 10: Write README.md
Professional README. What APEX is (1 paragraph). Architecture ASCII diagram. Five persona descriptions. Local dev setup. Deployment.

---

## SUCCESS CRITERIA
1. databricks --profile fe-vm workspace list returns without error
2. GitHub repo apex-etrm exists
3. Directory structure matches specification — tree -L 4
4. npm ci completes without errors
5. uvicorn backend.app:app starts without import errors
6. pytest tests/ passes (0 collected is fine)
7. decimal.js importable in frontend TypeScript

---

## COMPLETION ARTIFACT
completions/W00-foundation.md
Commit message: "chore: W00 complete — APEX project foundation"

---
---

# W01 — Design System
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W00-foundation.md exists.

---

## OBJECTIVE
Build the APEX design system. APEX must look and feel like a professional institutional trading terminal — denser, darker, and more data-focused than NEXUS. The reference aesthetic is Trading Technologies TT platform, ION OpenLink front-end, and Bloomberg multi-asset trading. Every UI decision should optimise for a trader spending 10+ hours in this interface.

---

## ETRM-SPECIFIC DESIGN REQUIREMENTS

### Colour Tokens: app/frontend/src/styles/tokens.css

Background (deeper dark than typical apps — terminal aesthetic):
- --color-bg-void: #04070f
- --color-bg-base: #080c14
- --color-bg-elevated: #0d1219
- --color-bg-raised: #111827
- --color-bg-panel: #0f1520
- --color-bg-overlay: #161f2e
- --color-bg-input: #0a0f1a

Border:
- --color-border-subtle: #161f2e
- --color-border-default: #1e2d40
- --color-border-strong: #2a3f5a
- --color-border-active: #3b5a80

Text:
- --color-text-primary: #dce8f4
- --color-text-secondary: #6b8099
- --color-text-tertiary: #3d5066
- --color-text-inverse: #04070f
- --color-text-muted: #2a3d52

Trading semantics (these are the most important colours in the system):
- --color-bid: #00c99a (long/buy/bid — standard green on dark terminal)
- --color-bid-dim: #00c99a18
- --color-offer: #e05252 (short/sell/offer — standard red on dark terminal)
- --color-offer-dim: #e0525218
- --color-pnl-positive: #00c99a
- --color-pnl-negative: #e05252
- --color-pnl-flat: #6b8099
- --color-warning: #d4921e
- --color-warning-dim: #d4921e18
- --color-critical: #c0392b
- --color-neutral: #3b7dd8

Market status colours:
- --color-market-open: #00c99a
- --color-market-closed: #6b8099
- --color-market-auction: #d4921e
- --color-price-up: #00c99a
- --color-price-down: #e05252
- --color-price-unchanged: #6b8099

Persona accent colours (subtle — used in persona selector and workspace header):
- --color-persona-dispatch: #00b4b4 (teal — operations)
- --color-persona-trader: #3b7dd8 (blue — front office)
- --color-persona-quant: #8b5cf6 (purple — quantitative)
- --color-persona-risk: #d4921e (amber — risk/compliance)
- --color-persona-portfolio: #10b981 (emerald — commercial)

Typography:
- --font-ui: 'Inter', -apple-system, sans-serif
- --font-data: 'JetBrains Mono', 'Fira Code', monospace
- --font-display: 'Inter', sans-serif (headings only — same as UI but called out explicitly)

Font sizes (smaller than typical — information density):
- --text-2xs: 0.625rem (10px — ticker strips, overflow labels)
- --text-xs: 0.6875rem (11px — dense table data)
- --text-sm: 0.75rem (12px — standard table, most UI)
- --text-base: 0.8125rem (13px — body text)
- --text-md: 0.875rem (14px — panel headers)
- --text-lg: 1rem (16px — section titles)
- --text-xl: 1.25rem (20px — KPI values)
- --text-2xl: 1.5rem (24px — large metrics)
- --text-3xl: 2rem (32px — hero P&L display)

Font weights: 400, 500, 600, 700

Trading-specific spacing (tighter than NEXUS — density is a feature):
- --space-0.5: 2px
- --space-1: 4px
- --space-2: 8px
- --space-3: 12px
- --space-4: 16px
- --space-5: 20px
- --space-6: 24px
- --space-8: 32px

Border radius: --radius-none: 0, --radius-sm: 2px, --radius-md: 3px only
Data tables, order books, blotters: always radius-none.

Transitions: --transition-price: background-color 150ms ease (faster than NEXUS — trading terminals flash fast)

---

### File: app/frontend/src/styles/global.css
- html body: bg-void, text-primary, font-ui, font-size 12px (denser than NEXUS), antialiased
- table: border-collapse collapse, width 100%
- td th: padding 6px 10px, font-size text-sm (11px in tables)
- th: uppercase, letter-spacing 0.08em, color text-secondary, border-bottom 1px border-subtle
- Scrollbar: width 5px (narrower than NEXUS), thumb border-strong
- input select: bg-input, border-default, color text-primary, radius-sm

### File: app/frontend/src/styles/trading.css
Trading-specific utilities:
- .price-up — color price-up, with 150ms flash animation
- .price-down — color price-down, with 150ms flash animation
- .price-flash — keyframe: white at 0% → transparent at 100%, 150ms
- .bid — color bid
- .offer — color offer
- .pnl-positive — color pnl-positive, font-data
- .pnl-negative — color pnl-negative, font-data
- .pnl-flat — color pnl-flat, font-data
- .font-data — font-family var(--font-data)
- .tabular — font-variant-numeric tabular-nums; letter-spacing: 0
- .label-caps — uppercase, tracking 0.08em, text-xs, weight 600, color text-secondary
- .mono-price — font-data + tabular + text-right (apply to ALL price columns)
- .mono-mw — font-data + tabular + text-right (apply to ALL MW columns)
- .mono-pct — font-data + tabular + text-right (apply to ALL percentage columns)
- .row-long — background bid-dim on hover
- .row-short — background offer-dim on hover

---

## ETRM PRIMITIVE COMPONENTS

### Panel.tsx
Same concept as NEXUS Panel but with tighter padding (space-3 not space-4) and optional persona border colour.
Props: title, subtitle, actions, persona ('dispatch'|'trader'|'quant'|'risk'|'portfolio'|'neutral'), badge (string optional), className, children.

### DataTable.tsx
Must handle high-frequency updates without full re-render. Use useMemo on data. Support:
- onRowClick, onRowDoubleClick (double-click opens detail for blotter rows)
- selectedRowId (controlled selection)
- highlightRowFn: (row: T) => 'long'|'short'|'flat'|null — applies row-long/row-short class
- Columns can declare type: 'price'|'mw'|'pct'|'text'|'badge'|'action' — auto-applies correct class
- Price columns: always mono-price. MW columns: always mono-mw. Pct: mono-pct.
- Loading: CSS shimmer
- Empty: centred message

### OrderBook.tsx
A specialised bid/offer ladder component — not generic, not a DataTable. Fundamental ETRM primitive.
Props: bids list[{price, volume, cumulative}], offers list[{price, volume, cumulative}], spread, lastTradePrice.

Layout: two columns (Bids left, Offers right) with midpoint price in centre.
Bid rows: right-aligned price in --color-bid, volume, cumulative volume bar (CSS, not SVG, 50px width)
Offer rows: left-aligned price in --color-offer, volume, cumulative bar
Centre: last trade price in --font-data --text-md, spread in --text-xs --color-text-secondary
On price change: flash the changed row using --transition-price

### PriceTicker.tsx
A single instrument price display. Props: instrument, lastPrice, change, changePct, bid, offer, volume, status.
Last price: --font-data --text-2xl. Colour based on change direction (price-up/price-down).
Change: arrow character (▲ or ▼) + value in same colour — this is the ONE place a Unicode character is acceptable because ▲▼ are standard market convention, not emoji.
Bid/offer: --color-bid and --color-offer.

### Metric.tsx
KPI display. Same as NEXUS but with font-data on value always.

### StatusBadge.tsx
Colour-only. No icons. Labels: OPEN / CLOSED / AUCTION / PENDING / FILLED / PARTIAL / CANCELLED / BREACH.
Each maps to a specific colour from the trading palette.

### OfferBand.tsx
A single offer stack band — used in the dispatch offer stack builder.
Props: bandIndex (1-10), price (editable, decimal.js), volume (editable), isSelected, onPriceChange, onVolumeChange, onSelect.
Renders: band number (label-caps), price input (font-data, right-aligned), MW input (font-data, right-aligned), small drag handle for reordering.
Input validation: price must be a valid decimal, MW must be positive.

### Sparkline.tsx
Same as NEXUS. Compact SVG time series. Props: data, width=80, height=24, positive.

### ConfirmationToast.tsx
Trade confirmation notification (react-hot-toast custom component). Shows:
- Trade type (BUY/SELL) in bid/offer colour
- Instrument, volume MW, price $/MWh
- Auto-dismisses after 4 seconds
- No emoji.

---

## SUCCESS CRITERIA
1. npm run build zero errors
2. Vitest tests pass for all primitives
3. OrderBook renders with bid/offer colour convention correct
4. PriceTicker flash animation works (price-flash keyframe fires on update)
5. OfferBand validates decimal input correctly using decimal.js
6. ConfirmationToast renders without emoji
7. All numeric values use JetBrains Mono in all components
8. No hardcoded colour values in components — CSS custom properties only

---

## COMPLETION ARTIFACT
completions/W01-design-system.md
Commit message: "feat: W01 complete — APEX ETRM design system"
