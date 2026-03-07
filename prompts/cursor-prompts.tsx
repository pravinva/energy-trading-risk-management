import { useState } from "react";

const prompts = [
  {
    id: "P00",
    title: "Project Foundation",
    subtitle: "Repository scaffold, toolchain, local dev setup, Databricks configuration",
    prereqs: [],
    content: `# P00 — Project Foundation
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## OBJECTIVE
Establish the complete project foundation: repository structure, toolchain, local development environment, Databricks Asset Bundle configuration, and verified connectivity to the target workspace. Nothing functional is built here. Everything subsequent depends on this being correct.

---

## ARCHITECTURE DECISION: BACKEND RUNTIME
Rust cannot be used as the Databricks Apps runtime. Databricks Apps supports Python and Node.js only. The confirmed production stack from Databricks engineering is:
- Backend: Python 3.11 + FastAPI + uvicorn (served via Databricks Apps Python runtime)
- Frontend: React 18 + TypeScript + Vite (built to static files, served by FastAPI StaticFiles)
- Database: Lakebase (Postgres-compatible OLTP, accessed via psycopg3)
- Deployment: Databricks Asset Bundles (DABs)
- Auth: Databricks Apps native OBO (On-Behalf-Of) token authentication

Do NOT use Rust. Do NOT use Streamlit, Gradio, or Dash. Do NOT use a separate Node.js server for the backend.

---

## WORKSPACE TARGET
- Workspace URL: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
- CLI Profile: fe-vm
- All databricks CLI commands must use --profile fe-vm
- Verify connectivity before proceeding

---

## STEPS

### Step 1: Verify Databricks CLI connectivity
Using the Databricks CLI MCP tool, run a connectivity check against the fe-vm profile targeting the workspace URL above. Confirm the following are accessible:
- Unity Catalog (list catalogs)
- Databricks Apps (list apps — may be empty, that is fine)
- Secrets (list scopes)

If any of these fail, stop and report the specific error. Do not proceed.

### Step 2: Create GitHub repository
Create a public GitHub repository named: nexus-energy-trading-app
- Description: "Energy Trading Intelligence Platform — Databricks Apps"
- Initialize with README.md
- Add .gitignore for Python and Node
- Default branch: main

### Step 3: Create project directory structure
Create the following structure exactly. Do not add any files beyond what is listed here — subsequent prompts will populate each directory.

\`\`\`
nexus-energy-trading-app/
├── .cursor/
│   └── rules/
│       └── project.mdc          # Cursor project rules (see Step 5)
├── .github/
│   └── workflows/
│       └── deploy-public.yml    # Empty placeholder — Step 6
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI entry point — Step 7
│   │   ├── config.py            # Empty placeholder
│   │   ├── auth.py              # Empty placeholder
│   │   └── routes/
│   │       └── __init__.py
│   ├── frontend/
│   │   ├── src/
│   │   │   └── .gitkeep
│   │   ├── public/
│   │   │   └── .gitkeep
│   │   ├── index.html           # Empty placeholder
│   │   ├── package.json         # Step 8
│   │   ├── tsconfig.json        # Step 8
│   │   └── vite.config.ts       # Step 8
│   ├── plugins/
│   │   └── __init__.py          # Plugin interface — see P16
│   └── app.yaml                 # Databricks Apps config — Step 9
├── data/
│   ├── schema/
│   │   └── .gitkeep             # Populated in P02
│   ├── seeds/
│   │   ├── anz/
│   │   │   └── .gitkeep         # Populated in P03
│   │   ├── europe/
│   │   │   └── .gitkeep         # Populated in P04
│   │   └── americas/
│   │       └── .gitkeep         # Populated in P05
│   └── README.md                # Documents how to re-seed data
├── databricks.yml               # DAB root config — Step 10
├── requirements.txt             # Python deps — Step 11
├── .env.example                 # Environment variable template — Step 12
├── .gitignore                   # Step 13
└── README.md                    # Step 14
\`\`\`

### Step 4: Use Databricks CLI MCP to verify catalog
Run the following using the MCP tool with fe-vm profile:
- List available catalogs in the workspace
- Identify whether a catalog named "nexus" exists
- If it does not exist, note this — it will be created in P02
- Do NOT create it here

### Step 5: Write .cursor/rules/project.mdc
This file governs Cursor's behaviour throughout the entire project. Write the following content exactly:

The project is NEXUS, an energy trading intelligence platform deployed on Databricks Apps.

Stack: FastAPI (Python 3.11) backend, React 18 TypeScript frontend, Vite build tool, Lakebase (psycopg3), Databricks Asset Bundles.

Design principles:
- Dark theme only. Background #0a0d14. No light mode.
- Monospace font (JetBrains Mono) for ALL numerical data without exception.
- Inter font for all UI labels, headings, navigation.
- No emoji anywhere in the UI. No decorative illustrations. No gradient blobs.
- Information density over whitespace. This is a professional trading platform.
- Numbers are always right-aligned in tables.
- Positive values: #00d4aa. Negative values: #e05c5c. Neutral: #3b82f6.
- All column headers uppercase with 0.08em letter-spacing.
- Status indicators are colour-coded only — never use icons for status.
- Subtle 1px borders only. Border colour: #1e2d3d.
- No rounded corners on data tables or market data panels.
- Micro-animations on data updates only (number flash #ffffff10 → transparent, 300ms).

Code principles:
- TypeScript strict mode. No any types.
- Python type hints on all function signatures.
- All API routes prefixed /api/v1/
- All SQL in separate .sql files under data/ — never inline SQL strings in Python.
- No TODO comments. No commented-out code. No placeholder functions.
- Every file must be complete and functional when committed.

Testing:
- Every backend route must have a corresponding test in app/backend/tests/.
- Frontend components must have Vitest snapshot tests.
- No commit without passing tests.

### Step 6: Write .github/workflows/deploy-public.yml
Write a GitHub Actions workflow that:
- Triggers on push to main
- Checks out the repository
- Installs Python 3.11 and Node 20
- Runs backend tests (pytest app/backend/tests/)
- Runs frontend build (cd app/frontend && npm ci && npm run build)
- Syncs the built app to the Databricks workspace using databricks sync
- Deploys using databricks apps deploy
- Uses GitHub Secrets: DATABRICKS_HOST, DATABRICKS_TOKEN
- Does NOT include any step that clones, references, or mentions any private repository

### Step 7: Write app/backend/app.py
Write the FastAPI application entry point. It must:
- Import FastAPI and configure it with title "NEXUS API", version "1.0.0"
- Mount the React build output directory as StaticFiles at "/"
- Register a catch-all route that returns index.html for all non-API paths (SPA routing support)
- Import and include the routes router from app.routes (empty for now — routes added in P06)
- Configure CORS for local development only (origin localhost:5173)
- Include a startup event that logs the workspace URL from environment
- Be deployable immediately: running uvicorn app.backend.app:app --reload must start without errors

### Step 8: Write frontend configuration files
Write package.json, tsconfig.json, and vite.config.ts.

package.json must include:
- React 18, React DOM 18
- TypeScript 5
- Vite 5
- TanStack Router (@tanstack/react-router)
- TanStack Query (@tanstack/react-query)
- TanStack Table (@tanstack/react-table)
- Recharts (for time-series charts — this is the ONLY charting library)
- Axios
- date-fns
- Dev deps: Vitest, @testing-library/react, eslint with typescript rules

tsconfig.json must use strict mode with path aliases: @ maps to src/

vite.config.ts must:
- Build output to ../backend/static/
- Set base to "/"
- Configure proxy for /api → http://localhost:8000 in dev mode
- Configure path alias @ → src/

### Step 9: Write app/app.yaml
Write the Databricks Apps configuration:
- command: ["uvicorn", "app.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
- resources: include a Lakebase database resource named "nexus-db"
- env: DATABRICKS_WORKSPACE_URL from the workspace secrets

### Step 10: Write databricks.yml
Write the DAB root configuration for the nexus app targeting the fe-sandbox workspace using the fe-vm profile. Include:
- workspace host: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
- A targets section with: dev (using fe-vm profile) and prod
- The app resource pointing to app/app.yaml
- The Lakebase database resource

### Step 11: Write requirements.txt
Include exactly:
- fastapi
- uvicorn[standard]
- psycopg[binary]
- databricks-sdk
- python-dotenv
- pydantic>=2.0
- pytest
- httpx (for testing FastAPI)

### Step 12: Write .env.example
Document every environment variable the app will use:
- DATABRICKS_HOST
- DATABRICKS_TOKEN (local dev only — OBO in production)
- LAKEBASE_HOST (auto-injected by Databricks Apps in production)
- LAKEBASE_DATABASE (auto-injected)
- NEXUS_ENVIRONMENT (dev or prod)

### Step 13: Write .gitignore
Include: __pycache__, .env, node_modules, dist, .venv, *.pyc, .DS_Store, app/backend/static/ (the built frontend — not committed to git, built at deploy time)

### Step 14: Write README.md
Write a professional README that describes:
- What NEXUS is (1 paragraph, no marketing language, no emoji)
- Architecture diagram in ASCII
- Local development setup instructions (step by step)
- How to re-seed data (points to data/README.md)
- Deployment instructions using DABs
- The plugin interface pattern (brief — full docs in P16)

---

## SUCCESS CRITERIA
All of the following must be true before marking this workstream complete:

1. databricks --profile fe-vm workspace list / returns without error
2. GitHub repository nexus-energy-trading-app exists with main branch
3. Directory structure matches the specification exactly — verify with tree -L 4
4. cd app/frontend && npm ci completes without errors
5. cd app && uvicorn backend.app:app --reload starts without import errors (routes are empty, that is fine)
6. cd app && python -m pytest backend/tests/ passes (no tests yet = 0 collected, that is a pass)
7. All files written in steps 5-14 exist with non-empty content
8. .gitignore correctly excludes .env and app/backend/static/

---

## COMPLETION ARTIFACT
When ALL success criteria pass, create the file: completions/P00-foundation.md

It must contain:
- Date and time completed
- Workspace URL confirmed reachable
- GitHub repository URL
- Git commit SHA of the completion commit
- Output of: tree -L 4 nexus-energy-trading-app/
- Output of: cd app/frontend && npm ci (last 5 lines)
- Output of: cd app && uvicorn backend.app:app (startup log, first 10 lines)
- List of any deviations from this specification and the reason

Commit this file and push to main. The commit message must be: "chore: P00 complete — project foundation"

Do not proceed to any other workstream until this file is committed to GitHub.
`
  },
  {
    id: "P01",
    title: "Design System",
    subtitle: "Typography, colour tokens, spacing, component primitives — zero functionality",
    prereqs: ["P00-foundation.md"],
    content: `# P01 — Design System
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Before starting, verify the file completions/P00-foundation.md exists in the repository. If it does not exist, stop immediately and report that P00 must be completed first.

---

## OBJECTIVE
Define and implement the complete NEXUS design system as a TypeScript token file, a global CSS file, and a library of primitive UI components. No page-level functionality is built here. Everything in P10 through P21 imports from this system. Breaking the design system here breaks every subsequent workstream.

---

## DESIGN PHILOSOPHY
NEXUS is modelled on the aesthetic language of professional institutional energy trading platforms — specifically the visual vocabulary of Trading Technologies TT platform, Trayport Joule, and LSEG Workspace. The principles are:

High information density without visual noise. Every pixel serves data. The user is a power trader or quant who spends 8+ hours per day in this interface. The design must be legible, not decorative. Fatigue reduction is a core design requirement, not an afterthought.

The colour palette is cold and precise. Dark navy backgrounds, not warm dark. Blue-grey borders, not grey. Teal-green for positive movements, not emerald. These choices are deliberate — they match the chromatic vocabulary institutional traders associate with professional tooling.

Numbers are always monospace. Without exception. A proportional-width digit in a price column is a design error.

---

## TOKEN SPECIFICATION

### Colour Tokens — write these as CSS custom properties in a :root block

Background layers (darkest to lightest):
- --color-bg-void: #060912 (page background — the deepest layer)
- --color-bg-base: #0a0d14 (primary panel background)
- --color-bg-elevated: #0f1520 (slightly elevated panels — headers, toolbars)
- --color-bg-raised: #141c2b (hover states, active rows)
- --color-bg-overlay: #1a2438 (modals, dropdowns, tooltips)

Border:
- --color-border-subtle: #1a2540 (standard panel borders)
- --color-border-default: #243050 (active element borders)
- --color-border-strong: #2e3f6a (focused element borders)

Text:
- --color-text-primary: #e4eaf4 (primary labels, values)
- --color-text-secondary: #7d92b0 (secondary labels, column headers)
- --color-text-tertiary: #4a607d (disabled, placeholder)
- --color-text-inverse: #060912 (text on bright backgrounds)

Data semantics:
- --color-positive: #00c99a (positive price move, profit — NOT green, teal)
- --color-positive-dim: #00c99a1a (positive background tint)
- --color-negative: #e05252 (negative price move, loss)
- --color-negative-dim: #e052521a (negative background tint)
- --color-neutral: #3b7dd8 (neutral data highlight, Databricks blue)
- --color-neutral-dim: #3b7dd81a
- --color-warning: #d4921e (warning, attention required)
- --color-warning-dim: #d4921e1a

Interactive:
- --color-accent: #3b7dd8 (primary interactive — buttons, links, active states)
- --color-accent-hover: #4d8de8
- --color-accent-active: #2d6fc4

Region identifiers (used subtly in region-specific panels):
- --color-region-anz: #00b4b4 (teal — NEM energy)
- --color-region-europe: #6b7dd8 (indigo — EPEX)
- --color-region-americas: #d87d3b (amber — ERCOT/PJM)

### Typography Tokens

Font stacks:
- --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif
- --font-data: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace

Font sizes (rem scale):
- --text-xs: 0.6875rem (11px — dense table data, secondary labels)
- --text-sm: 0.75rem (12px — standard table data, most UI)
- --text-base: 0.8125rem (13px — primary body text)
- --text-md: 0.875rem (14px — section headers)
- --text-lg: 1rem (16px — panel titles)
- --text-xl: 1.125rem (18px — page headings)
- --text-2xl: 1.375rem (22px — KPI numbers)
- --text-3xl: 1.75rem (28px — hero metrics)

Font weights:
- --weight-normal: 400
- --weight-medium: 500
- --weight-semibold: 600
- --weight-bold: 700

Letter spacing:
- --tracking-tight: -0.01em
- --tracking-normal: 0
- --tracking-wide: 0.04em
- --tracking-wider: 0.08em (column headers)
- --tracking-widest: 0.12em (labels, badges)

Line heights:
- --leading-none: 1
- --leading-tight: 1.25
- --leading-snug: 1.375
- --leading-normal: 1.5

### Spacing Tokens (4px base grid):
- --space-1: 4px
- --space-2: 8px
- --space-3: 12px
- --space-4: 16px
- --space-5: 20px
- --space-6: 24px
- --space-8: 32px
- --space-10: 40px
- --space-12: 48px
- --space-16: 64px

### Border Radius:
- --radius-sm: 2px (inputs, badges — very tight)
- --radius-md: 4px (buttons, cards)
- --radius-lg: 6px (panels — sparingly)
- --radius-none: 0px (data tables — always sharp)

### Shadows:
- --shadow-panel: 0 1px 3px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.3)
- --shadow-elevated: 0 4px 16px rgba(0,0,0,0.5), 0 1px 4px rgba(0,0,0,0.4)
- --shadow-overlay: 0 8px 32px rgba(0,0,0,0.6)

### Transitions:
- --transition-fast: 100ms ease
- --transition-base: 200ms ease
- --transition-slow: 300ms ease
- --transition-data-flash: background-color 300ms ease (for number updates)

---

## FILES TO CREATE

### File 1: app/frontend/src/styles/tokens.css
Write all CSS custom properties as specified above in a :root block. Add a class [data-theme="dark"] block that duplicates them — this is the only theme that will ever exist, but the pattern must be established for correctness.

### File 2: app/frontend/src/styles/global.css
Write global styles:
- Import tokens.css
- Import Inter from Google Fonts (weights 400, 500, 600, 700)
- Import JetBrains Mono from Google Fonts (weights 400, 500, 600)
- Set html and body to: background var(--color-bg-void), color var(--color-text-primary), font-family var(--font-ui), font-size 13px, line-height var(--leading-normal), -webkit-font-smoothing antialiased
- Set * { box-sizing: border-box }
- Remove all default margins from headings
- Set all table styles: border-collapse collapse, width 100%
- Set td and th: padding var(--space-2) var(--space-3), font-size var(--text-sm), text-align left
- Set th: font-weight var(--weight-semibold), color var(--color-text-secondary), text-transform uppercase, letter-spacing var(--tracking-wider), border-bottom 1px solid var(--color-border-subtle)
- Set input, select: background var(--color-bg-elevated), border 1px solid var(--color-border-default), color var(--color-text-primary), font-family var(--font-ui), border-radius var(--radius-sm), padding var(--space-2) var(--space-3)
- Set ::selection: background var(--color-neutral-dim)
- Set ::-webkit-scrollbar width 6px, track var(--color-bg-base), thumb var(--color-border-default)
- Set a: color var(--color-accent), text-decoration none

### File 3: app/frontend/src/styles/typography.css
Write utility classes:
- .font-data { font-family: var(--font-data) } — apply to ANY numerical value without exception
- .font-ui { font-family: var(--font-ui) }
- .text-xs through .text-3xl matching the tokens
- .text-positive { color: var(--color-positive) }
- .text-negative { color: var(--color-negative) }
- .text-secondary { color: var(--color-text-secondary) }
- .text-tertiary { color: var(--color-text-tertiary) }
- .text-right { text-align: right }
- .text-tabular { font-variant-numeric: tabular-nums; letter-spacing: 0 } — used on all data numbers
- .label-caps { text-transform: uppercase; letter-spacing: var(--tracking-wider); font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--color-text-secondary) }

### File 4: app/frontend/src/components/primitives/Panel.tsx
A Panel is the fundamental layout container. Props:
- title: string (optional) — rendered as UPPERCASE label in header
- actions: ReactNode (optional) — rendered right-aligned in header
- region: 'anz' | 'europe' | 'americas' | 'neutral' (optional, default neutral) — sets a 2px left border in the region colour
- className: string (optional)
- children: ReactNode

The Panel renders a div with:
- Background var(--color-bg-base)
- Border 1px solid var(--color-border-subtle)
- Border-left 2px solid [region colour or transparent]
- No border-radius on data panels (radius-none)
- A header div if title or actions are provided: background var(--color-bg-elevated), padding var(--space-3) var(--space-4), border-bottom 1px solid var(--color-border-subtle)
- Title uses .label-caps class
- Content area with padding var(--space-4)

### File 5: app/frontend/src/components/primitives/DataTable.tsx
A typed generic table component. It takes TanStack Table as its core, with props:
- data: T[] 
- columns: ColumnDef<T>[]
- onRowClick: (row: T) => void (optional)
- loading: boolean (optional)
- emptyMessage: string (optional, default "No data")

Styling requirements:
- Border-radius: 0 on all table elements
- Header row: background var(--color-bg-elevated)
- Body rows: alternating background: var(--color-bg-base) and var(--color-bg-raised) with 0.3 opacity on the raised variant
- Hover state: background var(--color-bg-overlay)
- Numeric columns (detected by value type): class .text-right .font-data .text-tabular
- Positive numbers: class .text-positive
- Negative numbers: class .text-negative
- Loading state: render skeleton rows (3 rows of grey shimmer — CSS animation, no library)
- Empty state: centred message in var(--color-text-tertiary)

### File 6: app/frontend/src/components/primitives/Metric.tsx
A KPI metric display. Props:
- label: string
- value: string | number
- unit: string (optional — e.g. "$/MWh", "GW", "%")
- change: number (optional — if positive shows text-positive, negative shows text-negative)
- changeLabel: string (optional)
- size: 'sm' | 'md' | 'lg' (default md)

The value must always use .font-data .text-tabular. The label must use .label-caps.

### File 7: app/frontend/src/components/primitives/StatusBadge.tsx
Props:
- status: 'active' | 'warning' | 'critical' | 'inactive' | 'neutral'
- label: string

Maps status to colour:
- active: var(--color-positive) with var(--color-positive-dim) background
- warning: var(--color-warning) with var(--color-warning-dim) background
- critical: var(--color-negative) with var(--color-negative-dim) background
- inactive: var(--color-text-tertiary) with var(--color-bg-elevated) background
- neutral: var(--color-text-secondary) with var(--color-bg-elevated) background

No icon. Colour-only status indication. Text is .label-caps uppercase.

### File 8: app/frontend/src/components/primitives/Sparkline.tsx
A minimal SVG sparkline for time-series data in table cells. Props:
- data: number[]
- width: number (default 80)
- height: number (default 24)
- positive: boolean (if last value > first value)
- strokeWidth: number (default 1.5)

Uses positive colour if positive, negative if not. No axes, no labels, no tooltips. Pure data visualisation primitive.

### File 9: app/frontend/src/components/primitives/index.ts
Barrel export for all primitives.

### File 10: app/frontend/src/styles/index.css
Import all style files: tokens.css, global.css, typography.css

---

## SUCCESS CRITERIA

1. cd app/frontend && npm run build completes with zero errors and zero TypeScript errors
2. cd app/frontend && npm run test — Vitest snapshot tests for all 6 components pass
3. Import any component from @/components/primitives in a test file — resolves correctly
4. Open storybook (if configured) or a dev server — all 6 components render without console errors
5. Verify visually: Panel with title shows uppercase label with correct spacing
6. Verify visually: DataTable with numeric column has monospace right-aligned numbers
7. Verify visually: Metric component KPI number uses JetBrains Mono
8. Verify visually: StatusBadge shows no icon — colour only
9. No component file contains the word "emoji", no component contains any Unicode symbol outside ASCII range
10. No component uses any colour value not defined in tokens.css — hardcoded hex colours in component files are a build error (use CSS custom properties only)

Write a Vitest test for each component before marking complete. Each test must render the component, take a snapshot, and assert at minimum one prop variation.

---

## COMPLETION ARTIFACT
When ALL success criteria pass, create: completions/P01-design-system.md

Must contain:
- Date and time completed
- npm run build output (last 10 lines)
- npm run test output (all lines)
- Screenshot description of each primitive component (text description of what was verified visually)
- List of all CSS custom properties defined (count must match this specification)
- Any deviations and justifications

Commit message: "feat: P01 complete — design system and primitive components"
`
  },
  {
    id: "P02",
    title: "Data Infrastructure",
    subtitle: "Unity Catalog schema, Lakebase database, DDL — no seed data",
    prereqs: ["P00-foundation.md"],
    content: `# P02 — Data Infrastructure
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P00-foundation.md exists. If not, stop.

---

## OBJECTIVE
Create the complete Unity Catalog schema, Lakebase database, and all table DDL for NEXUS. No seed data is inserted here. This workstream creates the structures that P03, P04, and P05 populate. Every table must be re-creatable from these SQL files alone — this is the guarantee that the app can be moved to another workspace.

---

## WORKSPACE CONTEXT
- Profile: fe-vm
- Target workspace: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/
- All SQL executed via Databricks CLI MCP using the fe-vm profile

---

## STEPS

### Step 1: Create Unity Catalog resources
Using Databricks CLI MCP with fe-vm profile, execute the following in order:

CREATE CATALOG IF NOT EXISTS nexus
  COMMENT 'NEXUS Energy Trading Intelligence Platform — all schemas and tables';

CREATE SCHEMA IF NOT EXISTS nexus.anz
  COMMENT 'Australian National Electricity Market data';

CREATE SCHEMA IF NOT EXISTS nexus.europe
  COMMENT 'European power markets — EPEX, Nord Pool, ENTSO-E';

CREATE SCHEMA IF NOT EXISTS nexus.americas
  COMMENT 'North American ISO/RTO markets — ERCOT, PJM, CAISO, MISO, IESO, AESO';

CREATE SCHEMA IF NOT EXISTS nexus.common
  COMMENT 'Shared reference data and application state';

Verify each was created successfully before proceeding.

### Step 2: Write SQL DDL files
Write all DDL to files under data/schema/. Each file is a standalone SQL script that can be re-run from scratch (uses CREATE TABLE IF NOT EXISTS). Files are also saved to the Databricks workspace via CLI MCP.

---

## DDL FILE SPECIFICATIONS

### data/schema/01_common.sql

Table: nexus.common.regions
Columns: region_code VARCHAR(10) NOT NULL, region_name VARCHAR(100), description VARCHAR(500), primary_market_operator VARCHAR(100), timezone VARCHAR(50), currency_code VARCHAR(3), currency_symbol VARCHAR(5), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
Primary key: region_code
Seed rows (insert directly in this file): ('ANZ','Australia NEM','Australian National Electricity Market','AEMO','Australia/Sydney','AUD','$'), ('EUR','Europe','European Power Exchange and Nord Pool markets','EPEX/Nord Pool','Europe/Berlin','EUR','€'), ('AMER','Americas','North American ISO/RTO markets','Various','America/Chicago','USD','$')

Table: nexus.common.etrm_vendors
Columns: vendor_id VARCHAR(50), vendor_name VARCHAR(100), vendor_category VARCHAR(50), primary_market VARCHAR(100), displacement_angle TEXT, gap_summary TEXT
Insert reference data for: OpenLink/Endur, Allegro, Brady Technologies, ZEMA, Lacima, Molecule, cQuant, Trayport, FIS Kiodex, SAP Trading

Table: nexus.common.app_metadata
Columns: meta_key VARCHAR(100), meta_value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
This table stores runtime metadata: last_data_refresh per region, app_version, schema_version.

### data/schema/02_anz_market.sql

All tables in nexus.anz schema.

Table: nexus.anz.nem_dispatch_intervals
Columns: dispatch_interval_id BIGINT GENERATED ALWAYS AS IDENTITY, interval_datetime TIMESTAMP NOT NULL, region_id VARCHAR(10) NOT NULL, rrp DECIMAL(12,4) COMMENT 'Regional Reference Price $/MWh', dispatch_price DECIMAL(12,4), totaldemand DECIMAL(12,2) COMMENT 'MW', availablegeneration DECIMAL(12,2) COMMENT 'MW', netinterchange DECIMAL(12,2), lower5min DECIMAL(12,4) COMMENT 'FCAS Lower 5min $/MW/hr', lower60sec DECIMAL(12,4), lower6sec DECIMAL(12,4), raise5min DECIMAL(12,4), raise60sec DECIMAL(12,4), raise6sec DECIMAL(12,4), lowerreg DECIMAL(12,4), raisereg DECIMAL(12,4), data_source VARCHAR(20) DEFAULT 'SIMULATED'
Partition by: interval_datetime (daily)
Index on: region_id, interval_datetime

Table: nexus.anz.bess_assets
Columns: duid VARCHAR(20) NOT NULL COMMENT 'Dispatchable Unit Identifier', asset_name VARCHAR(100), operator VARCHAR(100), region_id VARCHAR(10), capacity_mw DECIMAL(10,2), duration_hours DECIMAL(5,2), technology VARCHAR(50), commissioned_date DATE, status VARCHAR(20), scada_source VARCHAR(100)
Primary key: duid

Table: nexus.anz.bess_telemetry
Columns: telemetry_id BIGINT GENERATED ALWAYS AS IDENTITY, duid VARCHAR(20) NOT NULL, recorded_at TIMESTAMP NOT NULL, state_of_charge_pct DECIMAL(5,2) COMMENT '0-100', output_mw DECIMAL(10,2) COMMENT 'positive=discharge, negative=charge', fcas_raise_mw DECIMAL(10,2), fcas_lower_mw DECIMAL(10,2), available_mw DECIMAL(10,2), temperature_c DECIMAL(6,2), cycle_count_today DECIMAL(6,1), data_source VARCHAR(20) DEFAULT 'SIMULATED'
Partition by: recorded_at (daily)

Table: nexus.anz.settlement_revenues
Columns: revenue_id BIGINT GENERATED ALWAYS AS IDENTITY, duid VARCHAR(20) NOT NULL, settlement_date DATE NOT NULL, trading_interval_end TIMESTAMP, energy_revenue DECIMAL(14,4), fcas_raise5min_revenue DECIMAL(14,4), fcas_lower5min_revenue DECIMAL(14,4), fcas_raise60sec_revenue DECIMAL(14,4), fcas_lower60sec_revenue DECIMAL(14,4), fcas_raise6sec_revenue DECIMAL(14,4), fcas_lower6sec_revenue DECIMAL(14,4), total_revenue DECIMAL(14,4), mlf_applied DECIMAL(8,6), data_source VARCHAR(20) DEFAULT 'SIMULATED'

Table: nexus.anz.generation_portfolio
Columns: duid VARCHAR(20) NOT NULL, asset_name VARCHAR(100), fuel_type VARCHAR(50), region_id VARCHAR(10), registered_capacity_mw DECIMAL(10,2), annual_generation_gwh DECIMAL(12,2), market_participant VARCHAR(100), connection_point VARCHAR(50)

### data/schema/03_europe_market.sql

All tables in nexus.europe schema.

Table: nexus.europe.epex_day_ahead_prices
Columns: price_id BIGINT GENERATED ALWAYS AS IDENTITY, delivery_datetime TIMESTAMP NOT NULL, bidding_zone VARCHAR(20) NOT NULL COMMENT 'e.g. DE-LU, FR, BE, NL', price_eur_mwh DECIMAL(12,4), volume_mwh DECIMAL(14,4), market_time_unit_minutes INTEGER DEFAULT 60 COMMENT '60 or 15 from Sept 2025', auction_date DATE, data_source VARCHAR(20) DEFAULT 'SIMULATED'
Partition by: delivery_datetime (daily)

Table: nexus.europe.entso_generation_mix
Columns: mix_id BIGINT GENERATED ALWAYS AS IDENTITY, interval_datetime TIMESTAMP NOT NULL, bidding_zone VARCHAR(20) NOT NULL, fuel_type VARCHAR(50) COMMENT 'Solar,Wind Onshore,Wind Offshore,Nuclear,Hydro,Gas,Coal,Lignite,Other', generation_mw DECIMAL(12,2), data_source VARCHAR(20) DEFAULT 'SIMULATED'

Table: nexus.europe.cross_border_flows
Columns: flow_id BIGINT GENERATED ALWAYS AS IDENTITY, interval_datetime TIMESTAMP NOT NULL, from_zone VARCHAR(20) NOT NULL, to_zone VARCHAR(20) NOT NULL, flow_mw DECIMAL(12,2), atc_mw DECIMAL(12,2) COMMENT 'Available Transfer Capacity', ntc_mw DECIMAL(12,2), data_source VARCHAR(20) DEFAULT 'SIMULATED'

Table: nexus.europe.generation_portfolio
Columns: asset_id VARCHAR(50) NOT NULL, asset_name VARCHAR(100), operator VARCHAR(100), country VARCHAR(10), fuel_type VARCHAR(50), capacity_mw DECIMAL(10,2), commission_year INTEGER, openlink_incumbent BOOLEAN DEFAULT FALSE COMMENT 'True if OpenLink/Endur is ETRM incumbent'
Primary key: asset_id

Table: nexus.europe.ets_carbon_prices
Columns: price_date DATE NOT NULL, eua_price_eur DECIMAL(10,4) COMMENT 'EU Allowance price EUR/tonne CO2', volume DECIMAL(16,2), exchange VARCHAR(50), data_source VARCHAR(20) DEFAULT 'SIMULATED'

Table: nexus.europe.spark_spreads
Columns: spread_id BIGINT GENERATED ALWAYS AS IDENTITY, calculation_datetime TIMESTAMP NOT NULL, bidding_zone VARCHAR(20), power_price DECIMAL(12,4), gas_price_mmbtu DECIMAL(12,4), heat_rate DECIMAL(8,4), ets_price DECIMAL(10,4), spark_spread DECIMAL(12,4), clean_spark_spread DECIMAL(12,4), data_source VARCHAR(20) DEFAULT 'SIMULATED'

### data/schema/04_americas_market.sql

All tables in nexus.americas schema.

Table: nexus.americas.iso_nodes
Columns: node_id VARCHAR(50) NOT NULL, node_name VARCHAR(200), iso_id VARCHAR(20) NOT NULL COMMENT 'ERCOT,PJM,CAISO,MISO,SPP,NYISO,ISONE,IESO,AESO', zone VARCHAR(50), latitude DECIMAL(9,6), longitude DECIMAL(9,6), is_hub BOOLEAN DEFAULT FALSE, hub_name VARCHAR(100)
Primary key: node_id

Table: nexus.americas.lmp_realtime
Columns: lmp_id BIGINT GENERATED ALWAYS AS IDENTITY, node_id VARCHAR(50) NOT NULL, iso_id VARCHAR(20) NOT NULL, interval_datetime TIMESTAMP NOT NULL, lmp DECIMAL(12,4) COMMENT '$/MWh', energy_component DECIMAL(12,4), congestion_component DECIMAL(12,4), loss_component DECIMAL(12,4), data_source VARCHAR(20) DEFAULT 'SIMULATED'
Partition by: interval_datetime (daily)

Table: nexus.americas.ercot_bess_assets
Columns: resource_id VARCHAR(50) NOT NULL, resource_name VARCHAR(200), qse VARCHAR(100) COMMENT 'Qualified Scheduling Entity', county VARCHAR(100), capacity_mw DECIMAL(10,2), duration_hours DECIMAL(5,2), commissioned_date DATE, rtcb_eligible BOOLEAN DEFAULT TRUE COMMENT 'Eligible for RTC+B post Dec 2025'
Primary key: resource_id

Table: nexus.americas.ercot_bess_telemetry
Columns: telemetry_id BIGINT GENERATED ALWAYS AS IDENTITY, resource_id VARCHAR(50) NOT NULL, recorded_at TIMESTAMP NOT NULL, state_of_charge_pct DECIMAL(5,2), output_mw DECIMAL(10,2), drrs_mw DECIMAL(10,2) COMMENT 'Dispatchable Reliability Reserve Service MW', reg_up_mw DECIMAL(10,2), reg_down_mw DECIMAL(10,2), tb1_spread DECIMAL(10,4) COMMENT 'Top/Bottom 1hr spread signal', tb4_spread DECIMAL(10,4), rtcb_signal DECIMAL(10,4) COMMENT 'RTC+B co-optimisation signal post Dec 2025', data_source VARCHAR(20) DEFAULT 'SIMULATED'

Table: nexus.americas.pjm_capacity_auctions
Columns: auction_id VARCHAR(50) NOT NULL, delivery_year VARCHAR(20) COMMENT 'e.g. 2026/2027', auction_date DATE, clearing_price_mw_day DECIMAL(12,4), total_cost_billions DECIMAL(10,4), data_center_cost_pct DECIMAL(5,2), cleared_capacity_mw DECIMAL(12,2), reliability_shortfall_mw DECIMAL(12,2), price_cap_hit BOOLEAN DEFAULT FALSE, data_source VARCHAR(20) DEFAULT 'REFERENCE'

Table: nexus.americas.ieso_nodal_prices
Columns: price_id BIGINT GENERATED ALWAYS AS IDENTITY, node_id VARCHAR(50), interval_datetime TIMESTAMP NOT NULL, lmp_cad DECIMAL(12,4), ontario_zonal_price DECIMAL(12,4), basis_spread DECIMAL(12,4) COMMENT 'Node LMP vs Ontario Zonal Price', market_type VARCHAR(20) COMMENT 'DAM or RTM', data_source VARCHAR(20) DEFAULT 'SIMULATED'
Note: IESO went nodal May 1 2025 — data before this date does not exist in real markets. Simulated data must only start from 2025-05-01.

### Step 3: Execute all DDL against the workspace
Using Databricks CLI MCP with fe-vm profile, execute each SQL file against the nexus catalog. Verify each table was created by running SELECT COUNT(*) FROM [table] after creation — all should return 0.

### Step 4: Create data/README.md
Write comprehensive documentation:
- How to re-run all DDL from scratch (in order: 01_common.sql, 02_anz_market.sql, 03_europe_market.sql, 04_americas_market.sql)
- Warning: running DDL does not insert data — see P03, P04, P05 for seed data
- How to re-seed data after DDL
- How to reset the entire database (DROP SCHEMA CASCADE — only for fresh workspace setup)
- Table descriptions matching the column COMMENT values above

---

## SUCCESS CRITERIA

1. All four schemas exist: nexus.anz, nexus.europe, nexus.americas, nexus.common — verified via CLI
2. All SQL files exist in data/schema/ and are valid, re-runnable scripts
3. Every table created has at least one indexed column (not just primary key where specified)
4. SELECT COUNT(*) FROM nexus.common.regions returns 3 (the seed rows from Step 2)
5. SELECT COUNT(*) FROM nexus.common.etrm_vendors returns 10 (the reference data)
6. All other tables return 0 rows — confirming structure exists, data pending
7. data/README.md is complete and accurate
8. No hardcoded credentials in any SQL file
9. IESO nodal price table has a CHECK constraint or comment verifying data starts 2025-05-01

---

## COMPLETION ARTIFACT
Create: completions/P02-data-infrastructure.md

Must contain:
- Date and time completed
- List of all tables created with row counts
- Output of SHOW SCHEMAS IN nexus
- Output of SHOW TABLES IN nexus.anz, nexus.europe, nexus.americas, nexus.common
- Confirmation that DDL files are re-runnable (re-run them once and confirm no errors)

Commit message: "feat: P02 complete — Unity Catalog schema and Lakebase DDL"
`
  },
  {
    id: "P03",
    title: "Seed Data — ANZ",
    subtitle: "Simulated NEM market data: RRP, BESS, FCAS — realistic distributions",
    prereqs: ["P02-data-infrastructure.md"],
    content: `# P03 — Seed Data: ANZ
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P02-data-infrastructure.md exists. If not, stop.

---

## OBJECTIVE
Populate the nexus.anz schema with simulated but statistically realistic NEM market data. The data must be domain-authentic — a power trader reviewing it must find it credible. All generation is done by SQL files that can be re-run in any workspace. No Python scripts, no notebooks — SQL only.

---

## DOMAIN CONTEXT FOR DATA GENERATION

The NEM operates on 5-minute dispatch intervals with a 30-minute trading interval. The Regional Reference Price (RRP) is the spot price in $/MWh. FCAS markets run simultaneously. Key statistical properties your simulated data must match:

RRP characteristics by region:
- QLD: typical range $40-200/MWh, occasional spikes to $15,000 (market cap), frequent negative prices during high solar periods (10am-2pm), average ~$80/MWh
- NSW: similar to QLD, slightly higher average ~$90/MWh
- VIC: more volatile, influenced by wind and interconnector flows, average ~$95/MWh
- SA: most volatile NEM region, high renewable penetration, negative prices common in midday, spikes more frequent, average ~$110/MWh

FCAS prices: RAISE6SEC and LOWER6SEC typically $1-20/MW/hr with spikes to $1000+ during contingency events. RAISEREG and LOWERREG typically $1-10/MW/hr.

BESS operational patterns: SOC typically peaks around 16:00-17:00 (charged during solar hours), discharges 18:00-22:00 (evening peak). Average cycles: 1.5-2 per day.

Revenue concentration: approximately 50% of annual BESS revenue comes from 30 high-volatility days. Data must reflect this skew.

---

## DATA PARAMETERS

Time range: 2025-01-01 00:00:00 to 2026-03-01 00:00:00 (14 months at 5-min intervals)
Regions: QLD, NSW, VIC, SA (4 NEM regions — exclude TAS for simplicity)
BESS assets: 8 simulated assets across regions (see asset list below)
Total dispatch interval rows: approximately 4 × 14 months × 30 days × 288 intervals = ~480,000 rows

BESS Asset list (write to nexus.anz.bess_assets first):
- HORNSDALE_1, Hornsdale Power Reserve Stage 1, Neoen, SA, 150MW, 2hr
- WARATAH_1, Waratah Super Battery, Akaysha Energy, NSW, 500MW, 2hr
- BLYTH_1, Blyth BESS, Neoen, SA, 238.5MW, 2hr
- LATROBE_1, LaTrobe Valley BESS, Equis, VIC, 200MW, 2hr
- BOULDERCOMBE_1, Bouldercombe BESS, AGL, QLD, 100MW, 2hr
- TORRENS_B_BESS, Torrens Island B BESS, AGL, SA, 100MW, 2hr
- DARLINGTON_PT, Darlington Point BESS, Origin Energy, NSW, 100MW, 2hr
- ERARING_BESS_1, Eraring BESS Stage 1, Origin Energy, NSW, 460MW, 4hr

---

## SQL FILES TO CREATE

### data/seeds/anz/01_bess_assets.sql
INSERT statements for all 8 BESS assets defined above. Include all columns from the bess_assets table schema.

### data/seeds/anz/02_generation_portfolio.sql
INSERT statements for approximately 20 generation assets representing:
- 4 coal units (NSW, VIC — retiring)
- 6 gas units (QLD, SA, VIC)
- 5 large solar farms (QLD, NSW, SA)
- 3 wind farms (SA, VIC)
- 2 hydro units (NSW — Snowy Hydro reference)

Use realistic capacities and operator names matching actual NEM participants.

### data/seeds/anz/03_dispatch_intervals.sql
Write a SQL script using Databricks SQL syntax (not standard SQL) to generate simulated dispatch interval data. Use the following approach:

Use a recursive CTE or a numbers table to generate timestamps. For each 5-minute interval from 2025-01-01 to 2026-03-01, for each of 4 regions, generate a row with:

RRP calculation logic (implement as CASE/WHEN and mathematical expressions):
- Base price: 75 + (RAND() * 50) $/MWh
- Time-of-day effect: subtract 30 during solar hours (hour between 10 and 14) — this creates the duck curve effect
- Evening peak: add 40 during peak hours (hour between 17 and 20)
- Overnight: subtract 15 during overnight (hour between 23 and 5)
- SA multiplier: multiply by 1.3 for SA region
- Spike probability: approximately 0.3% of intervals have RAND() > 0.997, in which case price is between $3000 and $15000
- Negative price probability: approximately 8% of intervals between 10:00-14:00 in summer months (Oct-Feb), price between -$80 and $0
- Weekend adjustment: prices on Saturday/Sunday approximately 20% lower

FCAS prices: generate as proportional to RRP with appropriate volatility. RAISE6SEC = 2 + RAND() * 5 + (CASE WHEN rrp > 500 THEN 50 ELSE 0 END). Similar logic for other FCAS markets.

Demand: 5000 + 3000 * SIN(2*PI()*(hour-8)/24) + RAND() * 500 — realistic daily demand curve.

### data/seeds/anz/04_bess_telemetry.sql
Generate telemetry for all 8 BESS assets, every 5 minutes, from 2025-01-01 to 2026-03-01.

SOC pattern (realistic daily cycle):
- Start of day: 40-60% (previous day's end state)
- Charging phase (9:00-16:00): SOC increases towards 90-100% as solar energy is absorbed
- Discharge phase (17:00-22:00): SOC decreases to 10-30% as evening peak is served
- Overnight: minor fluctuation from FCAS participation
- Add stochastic noise: SOC can vary ±5% from the pattern at each interval

Output MW: derived from SOC change direction. Positive (discharging) during 17:00-22:00, negative (charging) during 9:00-16:00, near-zero overnight.

FCAS: assets with 2hr duration provide RAISE6SEC and LOWER6SEC continuously. The 4hr Eraring asset provides additional RAISE5MIN and LOWER5MIN.

Temperature: realistic diurnal variation. Higher in summer months (SA assets reach 35-40°C ambient).

### data/seeds/anz/05_settlement_revenues.sql
Generate daily settlement revenue for each BESS asset, 2025-01-01 to 2026-03-01.

Revenue structure (based on real NEM BESS revenue patterns from the strategy research):
- Base energy revenue: derived from price × volume during high-price periods
- FCAS revenue: consistent base with occasional spike days (matching the "50% revenue from 30 days" statistic)
- Total annual revenue per MW: range $50,000-$144,000/MW/year (matching the Modo Energy benchmarks referenced in the strategy documents)
- High-volatility day flag: approximately 30 days per year where revenue is 5-10× average

### data/seeds/anz/00_run_all.sql
A master script that calls all other files in order:
01_bess_assets.sql, 02_generation_portfolio.sql, 03_dispatch_intervals.sql, 04_bess_telemetry.sql, 05_settlement_revenues.sql

Include TRUNCATE TABLE statements before each INSERT to make the script idempotent (re-runnable).

---

## EXECUTION
Using Databricks CLI MCP with fe-vm profile, execute data/seeds/anz/00_run_all.sql. Verify row counts after execution.

---

## SUCCESS CRITERIA

1. nexus.anz.bess_assets: exactly 8 rows
2. nexus.anz.generation_portfolio: 20 rows
3. nexus.anz.nem_dispatch_intervals: between 400,000 and 600,000 rows
4. nexus.anz.bess_telemetry: between 3,000,000 and 4,000,000 rows (8 assets × 14 months × 30 days × 288)
5. nexus.anz.settlement_revenues: approximately 8 assets × 425 days = ~3,400 rows
6. RRP data verification: SELECT AVG(rrp), MAX(rrp), MIN(rrp), COUNT(CASE WHEN rrp < 0 THEN 1 END) FROM nexus.anz.nem_dispatch_intervals WHERE region_id = 'SA' — average must be 80-130, max must be > 5000, negative count must be > 0
7. BESS SOC verification: SELECT AVG(state_of_charge_pct), MIN(state_of_charge_pct), MAX(state_of_charge_pct) FROM nexus.anz.bess_telemetry — must be 20-80 average, min must be < 15, max must be > 90
8. All SQL files in data/seeds/anz/ are re-runnable (run 00_run_all.sql twice — second run must complete cleanly due to TRUNCATE statements)
9. data_source column in all rows = 'SIMULATED' — verified

---

## COMPLETION ARTIFACT
Create: completions/P03-seed-data-anz.md

Must contain:
- Date and time completed
- Row counts for all tables
- Output of the RRP verification query (criteria 6)
- Output of the BESS SOC verification query (criteria 7)
- Confirmation that re-run is clean

Commit message: "feat: P03 complete — ANZ seed data (NEM simulation)"
`
  },
  {
    id: "P04",
    title: "Seed Data — Europe",
    subtitle: "Simulated EPEX, ENTSO-E, generation portfolio, carbon prices",
    prereqs: ["P02-data-infrastructure.md"],
    content: `# P04 — Seed Data: Europe
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P02-data-infrastructure.md exists. If not, stop.

---

## OBJECTIVE
Populate the nexus.europe schema with simulated but domain-authentic European power market data. The data must reflect actual European market characteristics post-September 2025 (15-min MTU introduction on EPEX).

---

## DOMAIN CONTEXT

EPEX SPOT day-ahead prices by bidding zone (realistic 2025 ranges):
- DE-LU (Germany-Luxembourg): €60-120/MWh average, negative prices common in summer midday (high solar), winter spikes to €400+
- FR (France): similar to DE-LU, nuclear baseload creates lower average ~€70/MWh
- BE (Belgium): similar to FR, some nuclear exposure
- NL (Netherlands): highly gas-correlated, average €80/MWh
- ES (Spain): slightly lower averages due to high renewables, average €65/MWh
- NO1-NO5 (Norway zones): very low when hydro reservoirs full (~€20/MWh), spikes during drought

Critical data requirement: From 2025-09-01 onwards, market_time_unit_minutes must be 15 (not 60) for EPEX data. Before 2025-09-01, use 60. This reflects the real-world EPEX MTU change and is a testable fact a domain expert will verify.

EU ETS carbon prices: realistic 2025 range €50-80/EUA (EU Allowance). Volatile with policy announcements.

Spark spread calculation: power price minus (gas price × heat rate) minus (ETS price × emission factor). Clean spark spread accounts for carbon cost.

---

## SQL FILES TO CREATE

### data/seeds/europe/01_generation_portfolio.sql
INSERT approximately 25 European generation assets including:
- 6 gas CCGT units (DE, FR, NL, BE) with openlink_incumbent = TRUE for 4 of them
- 4 nuclear units (FR, BE — referencing EDF and Engie)
- 5 wind farms (offshore DE, onshore ES, UK)
- 5 solar farms (ES, DE, IT)
- 3 hydro units (NO — referencing Statkraft)
- 2 coal units (DE — being retired)

### data/seeds/europe/02_ets_carbon_prices.sql
Generate daily ETS price data from 2024-01-01 to 2026-03-01. Use a random walk with mean reversion around €65/EUA, volatility approximately €3/day, bounded €40-€100.

### data/seeds/europe/03_epex_prices.sql
Generate EPEX day-ahead prices from 2024-01-01 to 2026-03-01.

Before 2025-09-01: hourly granularity (24 intervals per day per zone)
From 2025-09-01: 15-minute granularity (96 intervals per day per zone)

Bidding zones: DE-LU, FR, BE, NL, ES, NO1, NO2, CH (8 zones)

Price generation logic:
- Base: 75 + RAND() * 40
- Time-of-day curve: duck curve effect for solar zones (DE, ES, FR reduced 10:00-14:00)
- Season: winter prices 20% higher
- Renewable effect: high wind days (simulate 3-4x per week) reduce prices 15-30%
- Negative price probability: 12% of summer midday hours in DE and ES post-2025
- Peak hours (18:00-20:00): add €30-50
- Weekend: 15% lower

Include the MTU change: the query must generate 24 rows/day/zone before 2025-09-01 and 96 rows/day/zone from 2025-09-01.

### data/seeds/europe/04_entso_generation_mix.sql
Generate hourly generation mix data for DE-LU and FR zones from 2025-01-01 to 2026-03-01.

Fuel types and approximate MW shares (DE-LU peak demand ~80GW):
- Solar: 0 at night, peaks 25,000-35,000MW at midday in summer, 5,000-10,000 in winter
- Wind Onshore: 0-30,000MW, variable with weather simulation (random daily pattern that persists 3-4 days)
- Wind Offshore: 0-8,000MW, similar weather pattern but different phase
- Nuclear: flat 7,000-8,000MW (FR has 40,000-45,000MW nuclear)
- Gas: residual load filler, 5,000-25,000MW
- Coal: declining through the period, 2,000-8,000MW early 2025, near zero by early 2026
- Hydro: 1,000-3,000MW, seasonal (higher spring/autumn)

### data/seeds/europe/05_cross_border_flows.sql
Generate cross-border flow data for key corridors from 2025-01-01 to 2026-03-01 (hourly):
- DE-FR, DE-NL, DE-BE, FR-BE, FR-ES, NO-DE

Flow direction follows price differentials: net flow moves from lower price zone to higher price zone, constrained by ATC. ATC values must be plausible (DE-FR: ~3,500MW typical ATC).

### data/seeds/europe/06_spark_spreads.sql
Calculate and insert clean spark spread values using the previously inserted data. Join epex_prices, ets_carbon_prices, and use assumed gas prices (generate a gas_price column using random walk, mean €30/MWh, volatility €2/day).

Formula: spark_spread = power_price - (gas_price * 0.45) where 0.45 is heat rate in MWh/MWh equivalent
clean_spark_spread = spark_spread - (ets_price * 0.35) where 0.35 tonne CO2 per MWh

### data/seeds/europe/00_run_all.sql
Master script with TRUNCATE + sequential execution.

---

## SUCCESS CRITERIA

1. nexus.europe.generation_portfolio: 25 rows, at least 4 with openlink_incumbent = TRUE
2. nexus.europe.ets_carbon_prices: approximately 790 days of data
3. nexus.europe.epex_day_ahead_prices: verify MTU change — SELECT COUNT(*) WHERE delivery_datetime >= '2025-09-01' AND DATE(delivery_datetime) = '2025-09-15' AND bidding_zone = 'DE-LU' must return 96 (not 24)
4. nexus.europe.epex_day_ahead_prices: verify pre-MTU — same query for a date before 2025-09-01 must return 24
5. nexus.europe.entso_generation_mix: nuclear rows for FR zone must show ~40,000MW average
6. nexus.europe.cross_border_flows: all 6 corridors have data
7. nexus.europe.spark_spreads: clean_spark_spread range is approximately -€20 to +€60
8. Re-run idempotency confirmed

---

## COMPLETION ARTIFACT
Create: completions/P04-seed-data-europe.md

Must contain row counts, MTU verification query outputs, and spark spread range verification.

Commit message: "feat: P04 complete — Europe seed data (EPEX/ENTSO-E simulation)"
`
  },
  {
    id: "P05",
    title: "Seed Data — Americas",
    subtitle: "Simulated ERCOT LMP, PJM nodal, CAISO, IESO nodal — with RTC+B post Dec 2025",
    prereqs: ["P02-data-infrastructure.md"],
    content: `# P05 — Seed Data: Americas
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P02-data-infrastructure.md exists. If not, stop.

---

## OBJECTIVE
Populate the nexus.americas schema. Critical domain requirement: ERCOT data must reflect the RTC+B market design change from December 5, 2025. IESO Ontario nodal data must start no earlier than 2025-05-01. These are testable facts.

---

## DOMAIN CONTEXT

ERCOT LMP characteristics (energy-only market, no capacity market):
- Hub prices: West Hub typically $30-60/MWh average, Houston Hub slightly higher
- Nodal basis: nodes near wind generation in Panhandle often have large negative basis
- Data center alley (Permian Basin, North Texas): nodes near large loads often trade at premium
- Volatility: extreme — ERCOT prices hit $5,000/MWh (cap) during tight supply. Summer evenings post-solar are highest risk.
- RTC+B post Dec 5 2025: new rtcb_signal column becomes non-null. DRRS market activates. The signal structure changes — pre-RTC+B rows have rtcb_signal = NULL, post-RTC+B rows have a value.

PJM nodal prices:
- Realtime hub (AEP, AECO, BGE, ComEd) prices typically $40-100/MWh
- Dominion Zone: persistently elevated LMP since mid-2024 due to data center load. Basis premium vs. RTO hub: +$5-20/MWh persistent.
- Capacity market: not in LMP data but PJM auction reference table has 4 rows (2024/25, 2025/26, 2026/27, 2027/28)

IESO Ontario (critical):
- Data starts 2025-05-01. Zero data before this date. This is non-negotiable.
- Post-MRP: ~1,000 nodes, but simulate 50 representative nodes
- Ontario Zonal Price: province-wide average. Node LMPs vary ±$20-30/MWh around this
- Basis spread: some nodes consistently premium (Toronto load pocket), some discount (Bruce Nuclear area)

---

## SQL FILES TO CREATE

### data/seeds/americas/01_iso_nodes.sql
Insert representative nodes for each ISO:
- ERCOT: 15 nodes (West Hub, Houston Hub, North Hub, South Hub, 5 generation nodes in Panhandle wind area, 3 load nodes near Dallas/Houston, 2 data center nodes in Permian Basin/North Texas)
- PJM: 12 nodes (AEP Hub, AECO, BGE, ComEd, Dominion Zone × 3 nodes near Northern Virginia, PPL, PECO, PSEG)
- CAISO: 8 nodes (SP15, NP15, ZP26, 5 representative nodes)
- IESO: 50 nodes (Ontario — post-MRP, 2025-05-01 onwards only)
Mark 3 IESO nodes as is_hub = FALSE with persistent positive basis (data center load pockets in Toronto-area)

### data/seeds/americas/02_ercot_bess_assets.sql
Insert 10 ERCOT BESS assets with rtcb_eligible = TRUE for all (all are post-Dec 2025 eligible):
- Mix of existing and new: 2 in West Texas (near Permian), 3 in North Texas, 2 near Houston, 3 in South Texas
- Capacities: 50MW to 500MW, durations: 1-4 hours
- QSEs: reference real QSEs (Equilibrium Energy, Enel, Tesla Energy, AES Clean Energy)

### data/seeds/americas/03_lmp_realtime.sql
Generate real-time LMP data from 2025-01-01 to 2026-03-01 at 5-minute intervals for all nodes.

ERCOT-specific logic:
- West Hub base: $35 + RAND() * 30
- Panhandle wind nodes: West Hub minus basis of $5-40 (high negative during strong wind)
- Data center load nodes: West Hub plus $3-12 premium
- Summer afternoon (June-Sept, 15:00-19:00): add $20-40
- Spike probability: RAND() > 0.998 → price between $2000 and $4999

PJM-specific logic:
- RTO Hub base: $45 + RAND() * 35
- Dominion Zone: RTO Hub plus $8-15 persistent basis
- Winter morning peaks (Dec-Feb, 7:00-9:00): add $30-50
- Congestion events: RAND() > 0.99 → congestion_component spikes to $50-200

IESO-specific logic:
- Start date: 2025-05-01. Do not generate any rows before this date.
- Ontario Zonal Price as base: C$70 + RAND() * 40
- Node basis: each node has a fixed basis ±$0 to ±$25 with daily noise
- Toronto load pocket nodes: consistently +$15-25 basis

### data/seeds/americas/04_ercot_bess_telemetry.sql
Generate 5-minute telemetry for all 10 ERCOT BESS assets from 2025-01-01 to 2026-03-01.

Critical RTC+B requirement:
- Before 2025-12-05: rtcb_signal = NULL, drrs_mw = NULL
- From 2025-12-05: rtcb_signal is populated with a co-optimisation value (range $0-150/MWh, reflecting the combined energy + ancillary signal), drrs_mw shows DRRS participation (0-50% of asset capacity)

TB spread signal: calculate as (max hourly price in day - min hourly price in day) at each 5-min interval. This reflects the daily energy arbitrage opportunity.

SOC pattern: similar to ANZ but with ERCOT timing — charge during midday solar hours (CAISO-influenced market), discharge 18:00-21:00 Texas time.

### data/seeds/americas/05_pjm_capacity_auctions.sql
Insert 4 rows for PJM capacity auction history (reference data, not simulated):
- 2024/2025: $28.92/MW-day, ~$3.5B total, 0% data center (pre-surge)
- 2025/2026: $269.92/MW-day, $16.1B total, 63% data center cost attribution, price_cap_hit = FALSE
- 2026/2027: $329.17/MW-day, $16.1B total, 40% data center, price_cap_hit = FALSE
- 2027/2028: $333.44/MW-day, $16.4B total, 40% data center, price_cap_hit = TRUE, reliability_shortfall_mw = 6625

These figures are from the strategy research documents and match published PJM data.

### data/seeds/americas/06_ieso_nodal_prices.sql
Generate IESO nodal price data from 2025-05-01 to 2026-03-01 for all 50 IESO nodes.
- Granularity: 5-minute real-time + hourly day-ahead
- Ontario Zonal Price: C$75 + RAND() * 50, seasonal adjustment (winter +20%, summer +15% for peak hours)
- Basis spreads: each node's basis is a fixed value + daily noise. Toronto load pocket: +$20 persistent. Bruce area: -$8 persistent. Note these in comments.

### data/seeds/americas/00_run_all.sql
Master script. TRUNCATE + sequential execution.

---

## SUCCESS CRITERIA

1. nexus.americas.iso_nodes: 85 rows (15+12+8+50)
2. nexus.americas.lmp_realtime: IESO rows have zero entries before 2025-05-01 — verify: SELECT COUNT(*) FROM nexus.americas.lmp_realtime WHERE iso_id = 'IESO' AND interval_datetime < '2025-05-01' must return 0
3. nexus.americas.ercot_bess_telemetry: rows before 2025-12-05 have rtcb_signal IS NULL — verify
4. nexus.americas.ercot_bess_telemetry: rows from 2025-12-05 have rtcb_signal IS NOT NULL — verify
5. nexus.americas.pjm_capacity_auctions: exactly 4 rows, 2027/2028 row has price_cap_hit = TRUE
6. Dominion Zone LMP average > RTO Hub LMP average — verify with AVG query per zone
7. Re-run idempotency confirmed

---

## COMPLETION ARTIFACT
Create: completions/P05-seed-data-americas.md

Must contain row counts, IESO date boundary verification, RTC+B boundary verification, PJM capacity data spot-check.

Commit message: "feat: P05 complete — Americas seed data (ERCOT/PJM/IESO simulation)"
`
  },
  {
    id: "P06",
    title: "Backend Core",
    subtitle: "FastAPI app, Lakebase connection, auth middleware, health endpoints",
    prereqs: ["P00-foundation.md", "P02-data-infrastructure.md"],
    content: `# P06 — Backend Core
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P00-foundation.md AND completions/P02-data-infrastructure.md exist. If either is missing, stop.

---

## OBJECTIVE
Build the complete FastAPI backend core: Lakebase connection pooling, authentication middleware (email domain check), route structure, health endpoints, and the configuration system. This is the foundation every subsequent backend workstream (P07, P08, P09) builds on.

---

## ARCHITECTURE NOTES

Databricks Apps handles authentication externally. The app receives the authenticated user's email via the X-Forwarded-Email header (or equivalent Databricks Apps header). The backend never manages authentication credentials directly.

Lakebase connection: use psycopg3 (not psycopg2). The LAKEBASE_HOST and LAKEBASE_DATABASE environment variables are auto-injected by Databricks Apps. Locally, they come from .env.

All routes must have the prefix /api/v1/. Databricks Apps requires this for token passthrough to work correctly.

Python type hints are mandatory on every function. Use Pydantic v2 models for all request/response schemas. No dict returns from route handlers — always Pydantic models.

---

## FILES TO CREATE OR UPDATE

### app/backend/config.py
Write a configuration class using pydantic-settings (BaseSettings). Fields:
- databricks_host: str — from environment
- lakebase_host: str — from environment (auto-injected in production)
- lakebase_database: str — from environment
- lakebase_port: int = 5432
- nexus_environment: Literal['dev', 'prod'] = 'dev'
- app_version: str = '1.0.0'
- cors_origins: list[str] — from environment, default ['http://localhost:5173']

Add a cached_property or lru_cache so config is only instantiated once.

### app/backend/database.py
Write Lakebase connection management:
- A connection pool using psycopg3's AsyncConnectionPool
- Pool size: min_size=2, max_size=10
- Connection string built from config: postgresql://[user]@[host]:[port]/[database]
- In production (Databricks Apps), the user is the service principal — use OBO token from the Databricks SDK
- In development, use the current user from databricks-sdk WorkspaceClient().current_user.me()
- A context manager get_db() that yields a connection from the pool
- A startup function init_db() called from FastAPI lifespan that creates the pool and verifies connectivity with SELECT 1
- A shutdown function close_db() called from FastAPI lifespan that closes the pool

### app/backend/auth.py
Write the email domain authentication:

Function: get_current_user_email(request: Request) -> str
- Reads X-Forwarded-Email header (Databricks Apps standard)
- Falls back to NEXUS_DEV_USER_EMAIL env var in dev mode (for local testing without Databricks Apps header)
- Raises HTTPException 401 if neither is available

Function: is_databricks_employee(email: str) -> bool
- Returns True if email.lower().endswith('@databricks.com')
- This is the ONLY place this logic lives

Dependency: require_databricks_employee(email: str = Depends(get_current_user_email)) -> str
- Calls is_databricks_employee(email)
- Raises HTTPException 403 with message "This feature requires Databricks employee access" if False
- This dependency is applied to the GTM Signal Board routes only — not to any market data routes

### app/backend/models/__init__.py
Create Pydantic v2 models for all API responses. Write these as a starting point — specific route models are added in P07-P09.

Base models:
- APIResponse[T]: Generic wrapper with data: T, timestamp: datetime, region: Optional[str]
- ErrorResponse: detail: str, code: str, timestamp: datetime
- HealthResponse: status: Literal['ok', 'degraded', 'error'], version: str, environment: str, lakebase_connected: bool, timestamp: datetime
- UserContextResponse: email: str, is_databricks_employee: bool, has_gtm_access: bool

### app/backend/routes/__init__.py
Write the route aggregator that imports and includes:
- from .health import router as health_router (prefix /api/v1/health)
- from .anz import router as anz_router (prefix /api/v1/anz) — empty in P06, populated in P07
- from .europe import router as europe_router (prefix /api/v1/europe) — populated in P08
- from .americas import router as americas_router (prefix /api/v1/americas) — populated in P09
- from .user import router as user_router (prefix /api/v1/user)

### app/backend/routes/health.py
Write health check endpoints:
- GET /api/v1/health/ — returns HealthResponse, checks Lakebase with SELECT 1, reports status
- GET /api/v1/health/lakebase — returns lakebase status, query time in ms, row count from nexus.common.regions
- GET /api/v1/health/ready — Kubernetes-style readiness probe, returns 200 if ready, 503 if not

### app/backend/routes/user.py
Write user context endpoints:
- GET /api/v1/user/me — returns UserContextResponse using get_current_user_email dependency
- No authentication required on this endpoint — everyone can see their own context
- The response tells the frontend whether to show the GTM Signal Board

### app/backend/app.py (update from P00)
Update to:
- Use lifespan context manager (not deprecated on_event)
- Call init_db() on startup, close_db() on shutdown
- Include the routes router
- Mount static files AFTER API routes (order matters)
- Log startup: workspace URL, environment, Lakebase host

### app/backend/tests/test_health.py
Write pytest tests using httpx AsyncClient:
- test_health_endpoint_returns_200
- test_health_lakebase_connected — requires actual Lakebase connection (mark as integration test)
- test_ready_endpoint
- test_user_me_without_auth_header_returns_401 (when dev email env var is also not set)
- test_user_me_returns_employee_true_for_databricks_email
- test_user_me_returns_employee_false_for_other_email

---

## SUCCESS CRITERIA

1. uvicorn app.backend.app:app starts without errors
2. GET http://localhost:8000/api/v1/health/ returns {"status": "ok", "lakebase_connected": true}
3. GET http://localhost:8000/api/v1/health/lakebase returns response time < 500ms
4. GET http://localhost:8000/api/v1/user/me with header X-Forwarded-Email: test@databricks.com returns {"is_databricks_employee": true, "has_gtm_access": true}
5. GET http://localhost:8000/api/v1/user/me with header X-Forwarded-Email: test@customer.com returns {"is_databricks_employee": false, "has_gtm_access": false}
6. pytest app/backend/tests/test_health.py — all non-integration tests pass
7. No route handler returns a raw dict — all return Pydantic models
8. Type checking: mypy app/backend/ --strict must pass with zero errors
9. Lakebase connection pool initialises and can execute SELECT COUNT(*) FROM nexus.common.regions returning 3

---

## COMPLETION ARTIFACT
Create: completions/P06-backend-core.md

Must contain:
- Health endpoint response (curl output)
- User context endpoint response for Databricks email (curl output)
- User context endpoint response for non-Databricks email (curl output)
- pytest output
- mypy output

Commit message: "feat: P06 complete — FastAPI backend core with Lakebase and auth"
`
  },
  {
    id: "P07",
    title: "Backend — ANZ Routes",
    subtitle: "NEM market data, BESS telemetry, FCAS, dispatch API endpoints",
    prereqs: ["P06-backend-core.md", "P03-seed-data-anz.md"],
    content: `# P07 — Backend: ANZ Routes
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P06-backend-core.md AND completions/P03-seed-data-anz.md exist. Both required.

---

## OBJECTIVE
Implement all FastAPI routes that serve ANZ market data to the frontend. Every query runs against the nexus.anz schema in Lakebase. All SQL is in separate .sql files — no inline SQL strings in Python.

---

## SQL QUERY FILES
Create data/queries/anz/ directory. All queries live here.

### data/queries/anz/rrp_by_region.sql
Returns the last N dispatch intervals (default 288 = 24 hours) for all 4 NEM regions, ordered by interval_datetime DESC. Parameterised: :hours (default 24), :region_id (optional filter). Returns: interval_datetime, region_id, rrp, totaldemand, lower5min, raise5min, raisereg, lowerreg.

### data/queries/anz/rrp_current.sql
Returns the single most recent RRP value per region (4 rows). Used for the live price header strip.

### data/queries/anz/bess_fleet_summary.sql
Returns one row per BESS asset with: duid, asset_name, operator, region_id, capacity_mw, duration_hours, latest SOC%, latest output_mw, today's total revenue, cumulative annual revenue. JOINs bess_assets, latest bess_telemetry row (subquery), and SUM of settlement_revenues for current year.

### data/queries/anz/bess_telemetry_timeseries.sql
Returns telemetry for a specific DUID over last N hours. Parameterised: :duid, :hours (default 24). Returns: recorded_at, state_of_charge_pct, output_mw, fcas_raise_mw, fcas_lower_mw.

### data/queries/anz/revenue_attribution.sql
Returns daily revenue breakdown for a specific DUID over last 30 days. Columns: settlement_date, energy_revenue, fcas_raise5min_revenue, fcas_lower5min_revenue, fcas_raise6sec_revenue, fcas_lower6sec_revenue, total_revenue. Parameterised: :duid.

### data/queries/anz/fcas_market_summary.sql
Returns current FCAS market state across all regions: average LOWER6SEC, RAISE6SEC, LOWERREG, RAISEREG prices per region from last 6 dispatch intervals. Shows the FCAS market depth.

### data/queries/anz/spike_events.sql
Returns historical RRP spike events (RRP > 1000) from last 90 days. Columns: interval_datetime, region_id, rrp, duration_minutes (consecutive intervals above threshold). Used for the spike intelligence panel.

---

## BACKEND ROUTE FILE: app/backend/routes/anz.py

Write all Pydantic response models first, then routes.

Pydantic models needed:
- DispatchInterval: interval_datetime, region_id, rrp, totaldemand, raise5min, lower5min, raisereg, lowerreg
- RegionCurrentPrice: region_id, rrp, change_vs_prev, pct_change, is_spike (bool: rrp > 1000)
- BESSAsset: duid, asset_name, operator, region_id, capacity_mw, duration_hours, current_soc_pct, current_output_mw, today_revenue, annual_revenue_ytd
- BESSFleetSummary: assets: list[BESSAsset], total_fleet_mw, total_fleet_charging_mw, total_fleet_discharging_mw, fleet_fcas_mw
- TelemetryPoint: recorded_at, state_of_charge_pct, output_mw, fcas_raise_mw, fcas_lower_mw
- RevenueDay: settlement_date, energy_revenue, fcas_total_revenue, total_revenue
- FCASMarketState: region_id, lower6sec_avg, raise6sec_avg, lowerreg_avg, raisereg_avg
- SpikeEvent: start_datetime, end_datetime, region_id, peak_rrp, duration_minutes

Routes (all return APIResponse[T] wrapper):
- GET /api/v1/anz/prices/current — returns APIResponse[list[RegionCurrentPrice]]
- GET /api/v1/anz/prices/history — query params: hours: int = 24, region_id: Optional[str]. Returns APIResponse[list[DispatchInterval]]
- GET /api/v1/anz/bess/fleet — returns APIResponse[BESSFleetSummary]
- GET /api/v1/anz/bess/{duid}/telemetry — path param duid, query param hours: int = 24. Returns APIResponse[list[TelemetryPoint]]
- GET /api/v1/anz/bess/{duid}/revenue — query param days: int = 30. Returns APIResponse[list[RevenueDay]]
- GET /api/v1/anz/fcas/summary — returns APIResponse[list[FCASMarketState]]
- GET /api/v1/anz/spikes — query param days: int = 90. Returns APIResponse[list[SpikeEvent]]

Each route must:
- Load SQL from the corresponding .sql file (not inline)
- Execute against Lakebase using the get_db() dependency
- Handle empty results gracefully (return empty list, not 404)
- Include response_model in the route decorator
- Be fully type-annotated

---

## TEST FILE: app/backend/tests/test_anz_routes.py

Write tests for all 7 routes. Tests must use httpx AsyncClient against the actual Lakebase data (integration tests). Each test verifies:
- Response status is 200
- Response matches the Pydantic model schema
- Data is non-empty (since seed data exists from P03)
- Key business logic: /anz/prices/current returns exactly 4 regions (QLD, NSW, VIC, SA)
- Key business logic: /anz/bess/fleet returns 8 assets
- Key business logic: spike events have rrp > 1000

---

## SUCCESS CRITERIA

1. All 7 routes return HTTP 200 with valid JSON matching Pydantic schemas
2. /api/v1/anz/prices/current returns 4 regions
3. /api/v1/anz/bess/fleet returns 8 assets, none with null current_soc_pct
4. /api/v1/anz/bess/HORNSDALE_1/telemetry returns data
5. /api/v1/anz/spikes returns at least 10 events (confirming spike simulation worked in P03)
6. All SQL lives in data/queries/anz/ — grep -r "SELECT" app/backend/routes/anz.py must return zero lines
7. mypy app/backend/routes/anz.py --strict passes
8. All tests pass

---

## COMPLETION ARTIFACT
Create: completions/P07-backend-anz.md

Must contain: curl output for each endpoint, test output, mypy output.

Commit message: "feat: P07 complete — ANZ backend routes"
`
  },
  {
    id: "P08",
    title: "Backend — Europe Routes",
    subtitle: "EPEX prices, generation portfolio, spark spreads, REMIT audit endpoints",
    prereqs: ["P06-backend-core.md", "P04-seed-data-europe.md"],
    content: `# P08 — Backend: Europe Routes
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P06-backend-core.md AND completions/P04-seed-data-europe.md exist.

---

## OBJECTIVE
Implement all FastAPI routes for European market data. Key differentiator endpoints to implement: the REMIT audit trail endpoint (shows audit capability), the spark spread endpoint (shows ETS integration), and the MTU change handling (15-min vs 60-min data).

---

## SQL QUERY FILES: data/queries/europe/

### data/queries/europe/epex_current_prices.sql
Latest day-ahead price per bidding zone (8 zones). Returns: bidding_zone, delivery_datetime, price_eur_mwh, volume_mwh, market_time_unit_minutes (to show whether data is 15-min or 60-min).

### data/queries/europe/epex_price_history.sql
Parameterised: :bidding_zone (optional), :hours (default 24). Handles the MTU duality — returns data at whatever granularity was in use at that time.

### data/queries/europe/generation_mix.sql
Current generation mix for a given bidding zone (last 6 hours aggregated). Parameterised: :bidding_zone. Returns fuel_type and generation_mw ordered by generation_mw DESC.

### data/queries/europe/spark_spread_history.sql
Spark spread time series for last 30 days. Parameterised: :bidding_zone. Returns: calculation_datetime, power_price, gas_price_mmbtu, ets_price, spark_spread, clean_spark_spread.

### data/queries/europe/openlink_displacement_summary.sql
Returns generation assets where openlink_incumbent = TRUE, with their bidding zone, capacity, and a hypothetical "intelligence gap score" (computed as 1 for every column in the asset table that is null or empty — representing data that OpenLink doesn't provide but Databricks could). This is the ETRM displacement intelligence query.

### data/queries/europe/remit_audit_example.sql
Simulates a REMIT audit query: returns all EPEX price entries for a specific bidding zone on a specific date, with their insertion timestamps and data source. Parameterised: :bidding_zone, :audit_date. This demonstrates the audit trail capability.

### data/queries/europe/cross_border_utilisation.sql
Returns cross-border corridor utilisation (flow / ATC percentage) for current period, ordered by congestion (highest utilisation first). This demonstrates the FTR/cross-border intelligence capability.

---

## ROUTES: app/backend/routes/europe.py

Pydantic models:
- EPEXPrice: bidding_zone, delivery_datetime, price_eur_mwh, volume_mwh, mtu_minutes, is_negative (bool)
- GenerationMixItem: fuel_type, generation_mw, pct_of_total
- SparkSpreadPoint: calculation_datetime, power_price, gas_price_mmbtu, ets_price, spark_spread, clean_spark_spread
- GenerationAsset: asset_id, asset_name, operator, country, fuel_type, capacity_mw, openlink_incumbent
- CrossBorderFlow: from_zone, to_zone, flow_mw, atc_mw, utilisation_pct, is_constrained (bool: > 90%)
- AuditRecord: delivery_datetime, bidding_zone, price_eur_mwh, data_source, recorded_at

Routes:
- GET /api/v1/europe/prices/current — APIResponse[list[EPEXPrice]]
- GET /api/v1/europe/prices/history — query params: bidding_zone, hours: int = 24
- GET /api/v1/europe/generation/mix — query param: bidding_zone (default 'DE-LU')
- GET /api/v1/europe/spreads/spark — query param: bidding_zone (default 'DE-LU')
- GET /api/v1/europe/assets/openlink-incumbent — APIResponse[list[GenerationAsset]]
- GET /api/v1/europe/flows/cross-border — APIResponse[list[CrossBorderFlow]]
- GET /api/v1/europe/audit/remit — query params: bidding_zone, audit_date (ISO format). APIResponse[list[AuditRecord]]

---

## TEST FILE: app/backend/tests/test_europe_routes.py

Key test: test_epex_prices_include_15min_data — verify that prices after 2025-09-01 have mtu_minutes = 15.
Key test: test_spark_spread_clean_lt_regular — verify clean_spark_spread < spark_spread (carbon cost reduces it).
Key test: test_openlink_incumbent_assets_exist — verify at least 4 assets returned.
Key test: test_remit_audit_returns_ordered_data.

---

## SUCCESS CRITERIA

1. All 7 routes return HTTP 200
2. EPEX current prices returns 8 bidding zones
3. Post-2025-09-01 price data has mtu_minutes = 15
4. OpenLink incumbent endpoint returns >= 4 assets
5. Clean spark spread is lower than spark spread (positive carbon cost verified)
6. REMIT audit endpoint demonstrates complete data lineage
7. SQL in separate files — no inline SQL in route file
8. mypy strict passes
9. All tests pass

---

## COMPLETION ARTIFACT
Create: completions/P08-backend-europe.md

Commit message: "feat: P08 complete — Europe backend routes"
`
  },
  {
    id: "P09",
    title: "Backend — Americas Routes",
    subtitle: "Multi-ISO LMP normalisation, ERCOT RTC+B, PJM capacity, IESO nodal endpoints",
    prereqs: ["P06-backend-core.md", "P05-seed-data-americas.md"],
    content: `# P09 — Backend: Americas Routes
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P06-backend-core.md AND completions/P05-seed-data-americas.md exist.

---

## OBJECTIVE
Implement Americas backend routes. The differentiator here is the multi-ISO normalisation endpoint — returning LMP data across all ISOs with the same schema despite different underlying market structures. Also implement the RTC+B urgency endpoint that explicitly surfaces the December 2025 market design change.

---

## SQL QUERY FILES: data/queries/americas/

### data/queries/americas/multi_iso_lmp_current.sql
Returns latest LMP per ISO hub node across all ISOs in a single result set. This is the "unified multi-ISO view" that demonstrates the core Databricks value proposition. Parameterised: optional :iso_id filter. Returns: iso_id, node_id, node_name, zone, lmp, energy_component, congestion_component, loss_component, interval_datetime. ISOs with only energy (no decomposition — like some ERCOT simplified views) should have congestion_component = 0, loss_component = 0.

### data/queries/americas/ercot_rtcb_comparison.sql
Returns ERCOT BESS telemetry comparing pre and post RTC+B periods for a given resource. Parameterised: :resource_id. Returns two aggregated rows: one for pre-2025-12-05 (rtcb_signal IS NULL), one for post. Columns: period (pre/post), avg_tb4_spread, avg_drrs_mw, avg_output_mw, avg_soc_pct, total_count. This directly demonstrates the December 2025 market change impact.

### data/queries/americas/pjm_capacity_auction_history.sql
Returns all 4 PJM auction rows ordered by delivery year. Includes derived column: capacity_cost_per_mw_per_year as clearing_price_mw_day * 365.

### data/queries/americas/ieso_nodal_basis_leaders.sql
Returns the 10 IESO nodes with highest persistent basis spread (average LMP - Ontario Zonal Price), post-2025-05-01 only. Columns: node_id, node_name, avg_basis_spread, max_basis_spread, pct_hours_positive_basis. This is the "greenfield nodal market" intelligence query.

### data/queries/americas/data_center_lmp_correlation.sql
Returns LMP history for nodes tagged as being near data center load (is_hub = FALSE and near-DC nodes defined in P05). Shows correlation between node load growth and basis premium. Returns: node_id, month_start, avg_lmp, avg_congestion, avg_basis_vs_hub. Parameterised: :iso_id.

### data/queries/americas/cross_iso_spread.sql
Computes the price differential between PJM AEP Hub and ERCOT Houston Hub for the last 30 days (daily average). This is a cross-ISO arbitrage intelligence query — the kind of query that only works with a unified multi-ISO data platform.

---

## ROUTES: app/backend/routes/americas.py

Pydantic models:
- ISOPrice: iso_id, node_id, node_name, zone, lmp, energy_component, congestion_component, loss_component, interval_datetime
- RTCBComparison: period: Literal['pre_rtcb', 'post_rtcb'], avg_tb4_spread, avg_drrs_mw, avg_output_mw, avg_soc_pct, record_count
- CapacityAuction: delivery_year, clearing_price_mw_day, total_cost_billions, data_center_cost_pct, price_cap_hit, reliability_shortfall_mw, capacity_cost_per_mw_per_year
- NodalBasisNode: node_id, node_name, avg_basis_spread, max_basis_spread, pct_hours_positive
- CrossISOSpread: date, pjm_aep_hub_price, ercot_houston_price, spread, spread_direction: Literal['PJM_PREMIUM','ERCOT_PREMIUM','FLAT']

Routes:
- GET /api/v1/americas/prices/current — multi-ISO unified LMP view. APIResponse[list[ISOPrice]]
- GET /api/v1/americas/prices/current — query param: iso_id (optional filter)
- GET /api/v1/americas/ercot/rtcb-comparison/{resource_id} — APIResponse[list[RTCBComparison]]. This is the flagship urgency endpoint.
- GET /api/v1/americas/pjm/capacity-auctions — APIResponse[list[CapacityAuction]]
- GET /api/v1/americas/ieso/nodal-basis — APIResponse[list[NodalBasisNode]]
- GET /api/v1/americas/intelligence/data-center-lmp — query param: iso_id (default 'PJM'). APIResponse showing data center load correlation
- GET /api/v1/americas/intelligence/cross-iso-spread — APIResponse[list[CrossISOSpread]]

---

## TEST FILE: app/backend/tests/test_americas_routes.py

Key test: test_multi_iso_prices_covers_all_isos — verify all 9 ISO codes appear in the response.
Key test: test_rtcb_comparison_shows_two_periods — verify both 'pre_rtcb' and 'post_rtcb' are returned.
Key test: test_rtcb_post_period_has_drrs_signal — verify avg_drrs_mw > 0 in post_rtcb period.
Key test: test_ieso_nodal_data_no_pre_may_2025 — calls the underlying SQL through the endpoint, verifies data integrity.
Key test: test_pjm_auctions_price_cap_hit_in_2027_28.

---

## SUCCESS CRITERIA

1. Multi-ISO unified endpoint returns nodes from all 9 ISOs in a single response
2. RTC+B comparison endpoint returns 2 rows (pre/post) when queried for any ERCOT resource
3. Post-RTC+B period shows non-zero drrs values
4. PJM capacity auctions endpoint returns 4 rows, 2027/28 has price_cap_hit = true
5. IESO nodal basis endpoint only returns post-2025-05-01 data
6. Cross-ISO spread endpoint returns valid daily spreads
7. SQL in separate files confirmed
8. mypy strict passes
9. All tests pass

---

## COMPLETION ARTIFACT
Create: completions/P09-backend-americas.md

Commit message: "feat: P09 complete — Americas backend routes"
`
  },
  {
    id: "P10",
    title: "Frontend Shell",
    subtitle: "Vite/React skeleton, region selector, routing, layout — no regional content",
    prereqs: ["P01-design-system.md", "P06-backend-core.md"],
    content: `# P10 — Frontend Shell
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P01-design-system.md AND completions/P06-backend-core.md exist.

---

## OBJECTIVE
Build the complete application shell: region selector landing screen, navigation layout, TanStack Router route structure, TanStack Query provider, API client configuration, and the empty regional module placeholders. When this workstream is complete, the app must be navigable with proper URL routing, but regional content panels are empty placeholders filled in by P12, P13, P14.

---

## FILES TO CREATE

### app/frontend/src/main.tsx
React 18 root entry point. Wraps the app in: TanStack Router provider, TanStack Query client (staleTime: 30s, refetchInterval: 30s for market data), React strict mode. Import global styles here.

### app/frontend/src/router.ts
Define the TanStack Router route tree:
- / — RegionSelector (landing page)
- /anz — ANZLayout (shell for ANZ region)
- /anz/market — ANZMarketDashboard (placeholder)
- /anz/bess — ANZBESSIntelligence (placeholder)
- /anz/etrm — ANZETRMPositioning (placeholder)
- /europe — EuropeLayout (shell)
- /europe/market — EuropeMarketDashboard (placeholder)
- /europe/portfolio — EuropePortfolioIntelligence (placeholder)
- /europe/etrm — EuropeETRMPositioning (placeholder)
- /americas — AmericasLayout (shell)
- /americas/market — AmericasMarketDashboard (placeholder)
- /americas/bess — AmericasBESSIntelligence (placeholder)
- /americas/etrm — AmericasETRMPositioning (placeholder)

### app/frontend/src/api/client.ts
Axios client configuration:
- baseURL: '/api/v1'
- 30s timeout
- Response interceptor that unwraps the APIResponse wrapper (returns data.data directly)
- Error interceptor that maps HTTP errors to typed error objects
- Request interceptor that adds X-Region header based on current route

### app/frontend/src/api/hooks/useHealth.ts
TanStack Query hook for health data. refetchInterval: 60s.

### app/frontend/src/api/hooks/useUserContext.ts
TanStack Query hook for user context (/api/v1/user/me). staleTime: 5min. This hook drives the GTM Signal Board visibility decision.

### app/frontend/src/pages/RegionSelector.tsx
The landing page. Must reflect the design vocabulary of professional trading platform landing screens.

Layout: full viewport, dark background, three side-by-side region cards, centred vertically and horizontally.

Header: wordmark "NEXUS" in --font-data, font-weight 300, letter-spacing 0.3em, colour --color-text-secondary. Below it in --font-ui size --text-xs: "ENERGY TRADING INTELLIGENCE PLATFORM" in --color-text-tertiary. No logo graphic. No tagline. No decorative elements.

Region cards: three equal-width cards with 1px border --color-border-default. No rounded corners on hover border — stays sharp. On hover: border colour changes to region colour (--color-region-anz / --color-region-europe / --color-region-americas). Background subtle shift to --color-bg-raised. Transition: var(--transition-base).

Card content (for each region):
- Region code in --font-data font-size --text-3xl, colour matching region colour, positioned top-left
- Region name below in --font-ui --text-md --color-text-primary
- Market operator(s) in --text-sm --color-text-secondary
- A three-item list of "live context" items in --text-xs --color-text-tertiary (e.g. for ANZ: "5-min dispatch intervals", "BESS fleet: 8 assets", "FCAS markets active")
- At bottom: a thin 1px separator and a status line showing: "MARKET DATA: SIMULATED" in --label-caps with a 4px circular status dot in --color-warning (amber — because it is simulated data, not live)

Clicking a card navigates to /anz, /europe, or /americas respectively using TanStack Router.

The RegionSelector must NOT have a "back" concept in the browser sense — it IS the home. Each regional app header has a "NEXUS" wordmark that navigates back here.

### app/frontend/src/layouts/RegionalLayout.tsx
Shared layout component for all three regional modules. Props: region, children.

Structure:
- Topbar: fixed height 44px, background --color-bg-elevated, border-bottom 1px solid --color-border-subtle
  - Left: "NEXUS" wordmark (link back to /), a separator, region badge (e.g. "ANZ / NEM" in region colour --label-caps)
  - Right: connection status dot (green if health OK), timestamp "LAST UPDATE: HH:MM:SS" in --font-data --text-xs
  - Far right: if isEmployee (from useUserContext), show a small "INTERNAL" badge — this is the only indication the Signal Board exists
- Left sidebar: 200px fixed width, background --color-bg-base, border-right 1px solid --color-border-subtle
  - Navigation items for the 3 panels in the region (MARKET / BESS or PORTFOLIO / ETRM)
  - Active item: 2px left border in region colour, --color-bg-raised background
  - Labels in --label-caps --text-xs
- Main content area: remainder, overflow-y auto, padding --space-6

### app/frontend/src/layouts/ANZLayout.tsx, EuropeLayout.tsx, AmericasLayout.tsx
Each extends RegionalLayout with the correct region prop and navigation items. These are thin wrappers.

### app/frontend/src/pages/anz/*, europe/*, americas/*
Create placeholder page components for all 9 content pages. Each placeholder renders a Panel component (from P01) with title "WORKSTREAM [P12/P13/P14] — PENDING" and a text body "This panel will be implemented in [P12/P13/P14]." These placeholders are replaced by those workstreams.

---

## SUCCESS CRITERIA

1. npm run build completes with zero errors
2. npm run dev serves the app — localhost:5173 opens to RegionSelector
3. Region cards display correctly: three cards, correct region colours on hover
4. Clicking ANZ navigates to /anz, Europe to /europe, Americas to /americas
5. Navigating to /anz/market shows the placeholder panel
6. NEXUS wordmark in regional layout navigates back to / (RegionSelector)
7. useUserContext hook makes one API call to /api/v1/user/me on mount
8. "INTERNAL" badge appears ONLY when user is a Databricks employee
9. No console errors or warnings
10. All 13 routes are navigable (may show placeholders — that is correct)
11. TypeScript strict: zero errors
12. Vitest tests for RegionSelector and RegionalLayout components pass (snapshot + render tests)

---

## COMPLETION ARTIFACT
Create: completions/P10-frontend-shell.md

Must contain: npm run build output, screenshot descriptions of RegionSelector and each regional layout, TypeScript check output.

Commit message: "feat: P10 complete — frontend shell and region routing"
`
  },
  {
    id: "P11",
    title: "Frontend — ANZ Module",
    subtitle: "NEM market dashboard, BESS dispatch intelligence, ETRM positioning panels",
    prereqs: ["P10-frontend-shell.md", "P07-backend-anz.md"],
    content: `# P11 — Frontend: ANZ Module
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P10-frontend-shell.md AND completions/P07-backend-anz.md exist.

---

## OBJECTIVE
Build the complete ANZ regional module — three fully functional panels. Replace all ANZ placeholder pages from P10 with production-quality components. Every number displayed uses JetBrains Mono. No emoji. No illustrations.

---

## PANEL 1: ANZ Market Dashboard (/anz/market)

### Component: ANZMarketDashboard.tsx

Layout: 3-column grid at large viewport, 2-column at medium, 1-column at small.

**Component: RegionPriceStrip**
A horizontal bar at the top of the panel showing current RRP for all 4 NEM regions (QLD, NSW, VIC, SA) simultaneously.
- Each region: label in --label-caps, price in --font-data --text-2xl
- Colour: price > 1000 → --color-negative. Price < 0 → --color-neutral (blue). Price 0-200 → --color-text-primary. Price 200-1000 → --color-warning.
- When data refreshes and a price changes, apply a 300ms background flash using --transition-data-flash
- Uses useANZCurrentPrices hook (calls /api/v1/anz/prices/current, refetchInterval: 15s)

**Component: RRPTimeSeriesChart**
A time-series chart using Recharts (LineChart) showing RRP for all 4 regions over last 24 hours.
- Background: --color-bg-base
- Grid lines: 1px dashed --color-border-subtle (horizontal only)
- Each region line: use distinct colours derived from region data (not hardcoded region colours — derive from hue rotation)
- Y-axis: right-aligned, --font-data --text-xs, $/MWh label
- X-axis: --font-data --text-xs, time format HH:mm
- Tooltip: dark background --color-bg-overlay, white border, shows all 4 regions at hovered time in --font-data
- No legend graphic — use a text legend above the chart in --label-caps
- Loading state: skeleton shimmer (CSS animation, no library)
- Uses useANZPriceHistory hook

**Component: FCASMarketTable**
A DataTable component (from P01) showing FCAS market state across regions.
Columns: REGION, RAISE 6S $/MW, LOWER 6S $/MW, RAISE REG, LOWER REG
All numeric columns: --font-data, right-aligned, --text-tabular
Header in --label-caps --color-text-secondary
Uses useANZFCASSummary hook

**Component: SpikeEventFeed**
A scrollable list of recent RRP spike events (last 30 days).
Each row: timestamp in --font-data, region badge, peak price in --font-data --text-negative, duration.
Compact design — 36px row height. No pagination — virtual scroll if > 50 rows.

---

## PANEL 2: BESS Dispatch Intelligence (/anz/bess)

### Component: ANZBESSIntelligence.tsx

**Component: BESSFleetOverview**
Top-level metrics row using the Metric component (from P01):
- TOTAL FLEET CAPACITY: sum of all asset MW, unit "MW"
- CURRENTLY DISCHARGING: MW with --color-positive
- CURRENTLY CHARGING: MW (shown as negative, --color-negative)
- FLEET AVG SOC: percentage

**Component: BESSAssetTable**
Full-width DataTable showing all 8 BESS assets.
Columns: DUID, ASSET NAME, REGION, CAPACITY (MW), DURATION, SOC%, OUTPUT (MW), TODAY REVENUE ($), YTD REVENUE ($)
SOC%: uses a compact inline bar (6px height, 60px width SVG) in the cell alongside the number. Full bar = 100%. Colour: green if > 60%, warning if < 20%.
OUTPUT (MW): positive = --color-positive, negative = --color-negative
REVENUE columns: --font-data, --text-tabular, right-aligned
Clicking a row opens the BESSAssetDetail panel for that DUID.

**Component: BESSAssetDetail**
A side panel (not modal — slides in from right, 380px wide) showing detail for a selected BESS asset.
- Asset name, operator, region as header
- SOC time series (Recharts AreaChart, last 24 hours)
  - Area fill: gradient from --color-neutral to transparent
  - The "discharge band" (17:00-22:00) highlighted with a vertical band in --color-positive-dim
- Revenue attribution bar chart (Recharts BarChart, last 7 days)
  - Stacked bars: energy revenue, FCAS raise, FCAS lower — each a different shade
  - Bars are sharp (no border-radius)
- Key metrics: avg daily cycles, annual run rate revenue

---

## PANEL 3: ETRM Intelligence Positioning (/anz/etrm)

### Component: ANZETRMPositioning.tsx

This panel positions Databricks against ETRM incumbents (ZEMA, Lacima) in the ANZ context.

**Component: ETRMGapMatrix**
A structured comparison table with 3 columns: CAPABILITY, LEGACY ETRM (ZEMA/LACIMA), DATABRICKS NEXUS.
Rows (8 gaps from the strategy document):
1. Real-time 5-min dispatch data ingestion
2. ML price forecasting (MLflow)
3. BESS dispatch optimisation model
4. SCADA/PI historian integration
5. Self-serve NL analytics (Genie)
6. Operational state store (Lakebase)
7. Regulatory audit trail (Unity Catalog)
8. Multi-asset revenue stacking

For each row: LEGACY column shows a coloured StatusBadge (status: critical = not supported, warning = partial). DATABRICKS column shows StatusBadge (status: active = fully supported). StatusBadge is colour-only — no icons.

**Component: CostDisplacementPanel**
A Panel titled "COST DISPLACEMENT OPPORTUNITY" showing:
- A simple metric: "ZEMA TYPICAL ANNUAL LICENCE" in --font-data --text-3xl with unit "AUD / yr"
  Show range "A$200,000 – A$500,000" (estimated, not precise)
- Below: "EQUIVALENT DATABRICKS COMPUTE" with a lower range
- A note in --text-xs --color-text-tertiary: "Based on UCO intelligence: ZEMA cited as expensive for Monte Carlo simulations (AGL Energy, 2026)"
- This is a text-only panel — no charts, no decorative elements

**Component: ReferenceArchitectureDiagram**
An ASCII-art style architecture diagram rendered as fixed-width text (--font-data --text-xs --color-text-secondary):
Shows: PI HISTORIAN → UNIVERSAL OT CONNECTOR → DELTA LIVE TABLES → LAKEBASE (operational state) → MLFLOW (price forecast) → GENIE SPACE (trader queries)
Each arrow is "→" in --color-neutral. Layer names are uppercase. No SVG graphics.

---

## TANSTACK QUERY HOOKS: app/frontend/src/api/hooks/anz.ts

Write all hooks used by the ANZ module:
- useANZCurrentPrices: GET /api/v1/anz/prices/current, refetchInterval: 15000
- useANZPriceHistory(hours: number = 24, regionId?: string): GET /api/v1/anz/prices/history
- useANZBESSFleet: GET /api/v1/anz/bess/fleet, refetchInterval: 30000
- useANZBESSTelemetry(duid: string, hours: number = 24): GET /api/v1/anz/bess/{duid}/telemetry
- useANZBESSRevenue(duid: string, days: number = 30): GET /api/v1/anz/bess/{duid}/revenue
- useANZFCASSummary: GET /api/v1/anz/fcas/summary, refetchInterval: 30000
- useANZSpikes(days: number = 30): GET /api/v1/anz/spikes

---

## SUCCESS CRITERIA

1. npm run build passes with zero TypeScript errors
2. Navigate to /anz/market — RegionPriceStrip shows 4 NEM regions with real data from Lakebase
3. Navigate to /anz/market — RRPTimeSeriesChart renders with 24 hours of data, all 4 region lines visible
4. Navigate to /anz/bess — BESSAssetTable shows 8 rows with real SOC and revenue data
5. Click HORNSDALE_1 row — BESSAssetDetail slides in with SOC timeseries and revenue chart
6. Navigate to /anz/etrm — ETRMGapMatrix renders with correct StatusBadge colours
7. ALL numeric values in ALL components use JetBrains Mono font — verify by inspecting computed styles
8. No emoji characters anywhere in rendered output — grep -r "emoji\|🔴\|🟢\|✓\|✗" src/pages/anz/ returns zero
9. Vitest tests pass for all new components (snapshot + render with mock data)
10. Data refreshes: after 15s, current prices re-fetch (verify with network tab)

---

## COMPLETION ARTIFACT
Create: completions/P11-frontend-anz.md

Must contain: npm run build output, test output, description of each panel rendered with real data, confirmation that numeric fonts are monospace throughout.

Commit message: "feat: P11 complete — ANZ frontend module"
`
  },
  {
    id: "P12",
    title: "Frontend — Europe Module",
    subtitle: "EPEX market dashboard, generation portfolio, REMIT compliance demo panels",
    prereqs: ["P10-frontend-shell.md", "P08-backend-europe.md"],
    content: `# P12 — Frontend: Europe Module
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P10-frontend-shell.md AND completions/P08-backend-europe.md exist.

---

## OBJECTIVE
Build the complete Europe regional module. Three panels: market dashboard (EPEX + cross-border), generation portfolio intelligence (the E.ON pattern), and ETRM positioning (REMIT + OpenLink displacement).

---

## PANEL 1: Europe Market Dashboard (/europe/market)

**Component: EPEXPriceGrid**
An 8-cell grid showing current day-ahead price per EPEX bidding zone (DE-LU, FR, BE, NL, ES, NO1, NO2, CH).
Each cell: zone code in --label-caps, price in --font-data --text-2xl, a Sparkline (from P01 primitives) showing last 24 hours, and the MTU indicator (a small badge showing "15 MIN" in --color-positive or "60 MIN" in --color-text-tertiary). The MTU badge demonstrates the September 2025 market change.

**Component: CrossBorderFlowTable**
DataTable showing cross-border corridors ordered by utilisation percentage.
Columns: CORRIDOR, FLOW (MW), ATC (MW), UTILISATION %, STATUS
STATUS: StatusBadge (active if < 70%, warning if 70-90%, critical if > 90%). Colour only.
The congested corridors panel is a direct demonstration of the FTR intelligence value proposition.

**Component: EPEXPriceHistoryChart**
Recharts LineChart for selected bidding zone, last 7 days. Zone selector above the chart (tabs, not dropdown — max 8 tabs in --label-caps --text-xs). The chart must visually distinguish pre- and post-15min MTU data: add a vertical reference line at 2025-09-01 with label "15-MIN MTU".

---

## PANEL 2: Generation Portfolio Intelligence (/europe/portfolio)

**Component: GenerationPortfolioTable**
Full DataTable of all European generation assets (25 rows).
Columns: ASSET, OPERATOR, COUNTRY, FUEL TYPE, CAPACITY (MW), OPENLINK INCUMBENT
OPENLINK INCUMBENT column: StatusBadge (warning for TRUE — showing OpenLink is present, active for FALSE — showing Databricks can lead). Label: "OPENLINK" or "DATABRICKS READY".
This directly surfaces the E.ON pattern as a repeatable playbook.

**Component: SparkSpreadPanel**
Time-series chart showing spark spread and clean spark spread for selected zone over last 30 days.
Two lines: spark spread in --color-neutral, clean spark spread in --color-positive (lower — carbon cost removed).
Y-axis label: "€/MWh". A horizontal reference line at 0 in --color-border-default.
Annotation: where clean_spark_spread < 0, background fill in --color-negative-dim (uneconomic dispatch zone).

**Component: ETSCarbonPriceStrip**
A compact 1-row strip showing: CARBON PRICE (EUA) in --font-data --text-xl, 30-day change, and a Sparkline of last 30 days price. This is positioned above the SparkSpreadPanel to contextualise carbon's impact on generation economics.

---

## PANEL 3: ETRM Positioning (/europe/etrm)

**Component: REMITCapabilityDemo**
Positioned as the European entry-point conversation: compliance as infrastructure.

Two sub-sections side by side:

Left: "LEGACY ETRM REMIT" — shows the traditional approach as a bullet list in --text-sm:
- Compliance module bolt-on to ETRM database
- Manual extraction for ACER reporting
- T+2 audit reconstruction time
- Separate compliance database (data duplication)
- Version upgrade required for REMIT II changes

Right: "DATABRICKS UNITY CATALOG" — shows Databricks approach:
- Delta time-travel: point-in-time replay any date/time
- Unity Catalog: complete lineage from market feed to reported trade
- Real-time audit: any ACER query answered in < 1 second
- REMIT II compliance: automatic (schema extension, not rebuild)
- Side effect of normal data pipeline: zero additional infrastructure

Below: A live "REMIT Audit Simulation" section. A date picker (defaulting to last month) and a bidding zone selector. Clicking "RUN AUDIT QUERY" calls the /api/v1/europe/audit/remit endpoint and displays the results in a DataTable. Column headers include "RECORDED_AT" (the lineage column that proves the audit trail). This is a live demo of the architecture, not a mock.

**Component: OpenLinkDisplacementMap**
A visual representation (pure CSS/HTML — no SVG library) showing the E.ON pattern.
Rendered as a horizontal flow: OPENLINK ENDUR → DATABRICKS NEXUS INTELLIGENCE LAYER
Each box is a styled div: background --color-bg-elevated, border 1px solid --color-border-default, padding --space-4, text in --label-caps.
The OPENLINK box has a border in --color-warning (amber — existing system, not being replaced).
The NEXUS box has a border in --color-positive (teal — the new intelligence layer).
Between them: an arrow with label "COMPLEMENTS" in --text-xs --color-text-tertiary.
Below the OPENLINK box: 3 bullet points of what OpenLink provides (trade capture, settlement, scheduling).
Below the NEXUS box: 3 bullet points of what NEXUS adds (ML forecasting, self-serve analytics, real-time risk).
This is a text + box diagram — no emoji, no icons.

---

## TANSTACK QUERY HOOKS: app/frontend/src/api/hooks/europe.ts

- useEuropePricesCurrent: refetchInterval: 60s (day-ahead prices are less volatile than real-time)
- useEuropePriceHistory(biddingZone: string, hours: number = 168): 7 days default
- useEuropeGenerationMix(biddingZone: string): refetchInterval: 300s
- useEuropeSparkSpreads(biddingZone: string): refetchInterval: 300s
- useEuropeOpenLinkAssets: staleTime: 10min (reference data)
- useEuropeCrossBorderFlows: refetchInterval: 60s
- useEuropeREMITAudit(biddingZone: string, date: string): enabled when both params present

---

## SUCCESS CRITERIA

1. npm run build with zero TypeScript errors
2. EPEX price grid shows 8 zones with correct MTU badge (post-Sept-2025 data shows "15 MIN")
3. Cross-border flow table shows at least 1 CRITICAL status row (> 90% utilisation — should exist given simulation)
4. EPEX history chart shows a vertical reference line at the MTU change date
5. Generation portfolio table shows OpenLink incumbent assets with warning badges
6. Spark spread chart shows two lines with clean spread below regular spread
7. REMIT audit simulation returns actual data from Lakebase when "RUN AUDIT QUERY" is clicked
8. OpenLink displacement diagram renders as a professional flow — text and boxes only, no emoji
9. All numeric values use --font-data (JetBrains Mono) — verified
10. Vitest tests pass

---

## COMPLETION ARTIFACT
Create: completions/P12-frontend-europe.md

Commit message: "feat: P12 complete — Europe frontend module"
`
  },
  {
    id: "P13",
    title: "Frontend — Americas Module",
    subtitle: "Multi-ISO LMP dashboard, ERCOT RTC+B intelligence, PJM capacity panels",
    prereqs: ["P10-frontend-shell.md", "P09-backend-americas.md"],
    content: `# P13 — Frontend: Americas Module
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P10-frontend-shell.md AND completions/P09-backend-americas.md exist.

---

## OBJECTIVE
Build the complete Americas regional module. The narrative thread is: multi-ISO normalisation is the entry point (the hardest data engineering problem in North American energy), ERCOT RTC+B is the urgency hook, and the IESO greenfield story is the strategic opportunity.

---

## PANEL 1: Americas Market Dashboard (/americas/market)

**Component: MultiISOPriceTable**
The flagship Americas component. A DataTable showing current LMP for all 9 ISOs simultaneously — PJM, ERCOT, CAISO, MISO, SPP, NYISO, ISO-NE, IESO, AESO.
Columns: ISO, HUB / ZONE, LMP ($/MWh), ENERGY, CONGESTION, LOSS, TIMESTAMP
ISO column: coloured badge (each ISO has a distinct hue within the --color-bg-elevated palette — no bright colours, subtle differentiation).
All price columns: --font-data right-aligned, positive/negative coloured by sign.
Note: ERCOT CONGESTION column is 0 (ERCOT does not publish congestion component — show as "N/A" in --color-text-tertiary). This shows domain knowledge.
IESO rows: timestamp must be >= 2025-05-01 (assert this in the component).
This table refreshes every 30s. When a price changes on refresh, the row background flashes --color-bg-overlay for 300ms.

**Component: ISOSelector**
A compact row of 9 ISO code buttons above the price table. Clicking an ISO filters the table and the history chart below to that ISO. Active state: border in --color-accent, background --color-bg-raised.

**Component: LMPHistoryChart**
Recharts LineChart for selected ISO(s), last 24 hours. When ERCOT is selected, add a vertical reference line at 2025-12-05 with label "RTC+B LIVE" in --color-warning. This immediately surfaced the urgency story for any ERCOT customer.

---

## PANEL 2: ERCOT RTC+B Intelligence (/americas/bess)

This panel is the urgency argument for ERCOT BESS operators. The title of the panel is "ERCOT BESS DISPATCH INTELLIGENCE — RTC+B ERA".

**Component: RTCBUrgencyBanner**
A full-width Panel with region border in --color-region-americas (amber). Content:
A single line of text in --font-data --text-md --color-text-primary: "ERCOT Real-Time Co-optimization + Batteries (RTC+B) launched December 5, 2025"
Below in --text-sm --color-text-secondary: "All BESS dispatch models trained on pre-December 2025 data require retraining. The new co-optimisation signal structure changes optimal dispatch strategy."
Below: two StatusBadge components side by side: "PRE-RTC+B MODELS: STALE" (status: critical), "NEXUS SIGNAL CAPTURE: ACTIVE" (status: active). Colour-only badges.

**Component: RTCBComparisonTable**
A DataTable showing the RTC+B comparison for each ERCOT BESS asset. For each asset, shows two rows: PRE-RTC+B and POST-RTC+B.
Columns: RESOURCE, PERIOD, AVG TB4 SPREAD, AVG DRRS (MW), AVG OUTPUT (MW), AVG SOC (%)
PRE row: DRRS column shows "--" (null — DRRS didn't exist)
POST row: DRRS column shows actual MW in --color-positive
The visual contrast between the two rows for each asset makes the RTC+B impact immediately legible to a domain expert.

**Component: ERCOTBESS AssetSelector**
A dropdown (styled as a dark select element) to choose which ERCOT BESS asset to view in detail. Options are the 10 ERCOT assets from P05.

**Component: TBSpreadTimeSeries**
Recharts AreaChart showing TB1 and TB4 spread for selected ERCOT asset over last 30 days.
The area fill uses gradient from --color-warning to transparent.
A vertical reference line at 2025-12-05 (RTC+B launch). The area after this line has a slightly different fill colour (--color-region-americas at 10% opacity) to visually indicate the new market regime.

---

## PANEL 3: ETRM Positioning (/americas/etrm)

**Component: PJMCapacityAuctionTable**
A DataTable showing all 4 PJM capacity auction results.
Columns: DELIVERY YEAR, CLEARING PRICE ($/MW-DAY), TOTAL COST ($B), DATA CENTER COST (%), PRICE CAP HIT, RELIABILITY SHORTFALL (MW)
The 2027/28 row has PRICE CAP HIT = TRUE — show this with a StatusBadge (critical).
RELIABILITY SHORTFALL column: 6,625 MW for 2027/28 in --color-negative.
Below the table: a text annotation in --text-xs --color-text-secondary: "Data center load has driven $21.3B in costs across the last 3 PJM auctions. Source: PJM Monitoring Analytics, Jan 2026."

**Component: IESOGreenfieldPanel**
A Panel titled "IESO ONTARIO — GREENFIELD NODAL MARKET".
A Metric showing: "NODAL MARKET AGE" with value "< 12 MONTHS" (since May 2025). Unit: "SINCE MRP LAUNCH".
Below: "DATA AVAILABLE FROM" in --label-caps, then "2025-05-01" in --font-data --text-xl. A subtitle: "First market to go nodal in North America since SPP in 2014."
Below: a compact DataTable showing top 5 IESO nodes by basis premium (from useIESONodalBasis hook). Columns: NODE, AVG BASIS (C$/MWh), MAX BASIS, STATUS.
Below: a single line in --text-sm: "No incumbent analytics vendor exists for IESO nodal pricing. NEXUS is the founding data infrastructure for this market."

**Component: MultiISONormalisationDemo**
A Panel showing the architecture value proposition:

Shows 3 data source boxes on the left: "PJM DataMiner2", "ERCOT MIS", "CAISO OASIS" — each a styled div in --color-bg-elevated with border --color-border-subtle, label in --label-caps.
An arrow converging them to a single box: "NEXUS UNIFIED LMP TABLE — delta.nexus.americas.lmp_realtime"
From that single box, two outputs: "GENIE SPACE" and "TRADING SYSTEM API"
All rendered as text + boxes (no SVG, no icons). Arrows are "→" in --color-neutral.
Below the diagram: "Total rows: [live count from Lakebase]" in --font-data --text-xs. This pulls a COUNT(*) from the americas.lmp_realtime table and displays it. A real number from a real database, demonstrating the platform at work.

---

## TANSTACK QUERY HOOKS: app/frontend/src/api/hooks/americas.ts

- useAmericasCurrentPrices(isoId?: string): refetchInterval: 30s
- useAmericasLMPHistory(isoId: string, hours: number = 24): refetchInterval: 60s
- useERCOTRTCBComparison(resourceId: string): staleTime: 5min (reference comparison)
- usePJMCapacityAuctions: staleTime: 1 day (historical reference)
- useIESONodalBasis: staleTime: 5min
- useMultiISORowCount: staleTime: 5min (the live count demo)

---

## SUCCESS CRITERIA

1. npm run build with zero TypeScript errors
2. MultiISOPriceTable shows all 9 ISOs, ERCOT congestion column shows "N/A"
3. IESO rows in price table have timestamps >= 2025-05-01
4. RTCBComparisonTable shows PRE and POST rows with DRRS null/populated correctly
5. PJM capacity auction table shows 2027/28 with PRICE CAP HIT badge in critical (red)
6. IESO greenfield panel shows data starting 2025-05-01
7. Live row count in MultiISONormalisationDemo shows an actual number from Lakebase
8. Vertical reference line at 2025-12-05 appears in ERCOT LMP history chart
9. All monospace font requirements met
10. Vitest tests pass

---

## COMPLETION ARTIFACT
Create: completions/P13-frontend-americas.md

Commit message: "feat: P13 complete — Americas frontend module"
`
  },
  {
    id: "P14",
    title: "GTM Signal Board",
    subtitle: "Plugin interface (public), SFDC integration (private submodule), employee-only gate",
    prereqs: ["P10-frontend-shell.md", "P06-backend-core.md"],
    content: `# P14 — GTM Signal Board
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/P10-frontend-shell.md AND completions/P06-backend-core.md exist.

---

## OBJECTIVE
Implement the GTM Signal Board as a plugin architecture. The PUBLIC repository contains ONLY the plugin interface and the no-op default. The PRIVATE repository (a git submodule) contains the Salesforce API integration. This workstream has two phases: Phase A installs in the public repo, Phase B installs in the private repo.

---

## PHASE A — PUBLIC REPO (plugin interface and no-op)

### app/backend/gtm/__init__.py
Write the Python plugin interface:

\`\`\`
class GTMSignalBoardPlugin:
    """
    Extension interface for the NEXUS GTM Signal Board.
    Default implementation is a no-op — the Signal Board
    is not rendered for non-authenticated deployments.

    Override this class in a private plugin to implement
    Salesforce CRM integration. The private plugin is
    maintained in a separate repository and installed
    as a git submodule at app/plugins/gtm_signal_board/.
    See CONTRIBUTING.md for the plugin interface contract.
    """

    def is_available(self) -> bool:
        return False

    async def get_signals(self, region: str) -> list[dict]:
        return []

    async def get_account_detail(self, account_id: str) -> dict | None:
        return None
\`\`\`

A module-level registry:

\`\`\`
_plugin: GTMSignalBoardPlugin = GTMSignalBoardPlugin()

def get_plugin() -> GTMSignalBoardPlugin:
    return _plugin

def register_plugin(plugin: GTMSignalBoardPlugin) -> None:
    global _plugin
    _plugin = plugin
\`\`\`

A startup function that attempts to import the private plugin:

\`\`\`
def load_plugin_if_available() -> None:
    try:
        from app.plugins.gtm_signal_board import GTMSignalBoardPluginImpl
        register_plugin(GTMSignalBoardPluginImpl())
    except ImportError:
        pass  # Private plugin not installed — no-op is correct
\`\`\`

Call load_plugin_if_available() from app.py startup (lifespan).

### app/backend/routes/gtm.py
Write backend GTM routes. These routes require the require_databricks_employee dependency — they return 403 for non-employees.

- GET /api/v1/gtm/signals/{region} — returns list of account signals for the region. If plugin.is_available() is False, returns empty list (not 403 — the frontend handles this gracefully).
- GET /api/v1/gtm/account/{account_id} — returns detail for a specific account. Same availability logic.
- GET /api/v1/gtm/status — returns: {"available": bool, "plugin_loaded": bool}. This is the endpoint the frontend calls to decide whether to show the Signal Board UI. No auth required on this endpoint.

### app/frontend/src/components/GTMSignalBoard/
Write the frontend Signal Board components. These are inside the RegionalLayout but only rendered when isEmployee is true AND the GTM status endpoint returns available: true.

**GTMSignalBoard.tsx**
The outer container. Receives region prop. On mount, calls useGTMStatus hook. If available is false, renders nothing (not even a placeholder).

If available is true:
- A Panel titled "GTM SIGNAL BOARD — [REGION]" with a note "INTERNAL — NOT VISIBLE TO CUSTOMERS" in --color-warning --label-caps
- A DataTable of account signals with columns: ACCOUNT, ARR/MO, SIGNAL TYPE, RECOMMENDED PLAY, URGENCY, ACCOUNT OWNER
- URGENCY column: StatusBadge (critical=HIGH, warning=MED, inactive=LOW)
- Clicking a row opens an account detail side panel

If the user's email is NOT @databricks.com, the entire component tree is null — not hidden, not empty div, null.

**hooks/useGTMSignals.ts**
TanStack Query hook for /api/v1/gtm/signals/{region}. Enabled only when isEmployee is true. staleTime: 5min (refreshes on demand).

---

## PHASE B — PRIVATE REPO (Salesforce integration)

Create a SEPARATE GitHub repository: nexus-energy-trading-app-internal
Set it as a git submodule in the main repo at: app/plugins/gtm_signal_board/

### app/plugins/gtm_signal_board/__init__.py
Implement GTMSignalBoardPluginImpl extending GTMSignalBoardPlugin.

### app/plugins/gtm_signal_board/sfdc_client.py
Implement Salesforce API client using OAuth 2.0 Connected App credentials stored in Databricks Secrets (scope: nexus, key: sfdc_client_id / sfdc_client_secret / sfdc_instance_url).

The client must:
- Use OAuth 2.0 client_credentials flow
- Cache the access token and refresh when expired
- Implement get_energy_accounts(region: str) → runs the multi-step SFDC query defined in the SFDC agent prompt (accounts + opportunities + UCOs + product gaps)
- Implement get_account_detail(account_id: str) → returns full account data with contacts and opportunities
- Apply the region scoping: ANZ → filter by region fields including APAC/ANZ. Europe → EMEA. Americas → AMER/CAN GEO. Scoped at query level, not post-filter.
- All results are in-memory only — no SFDC data is persisted to Lakebase or any database

The scoring logic (signal type, urgency, recommended play) is computed in Python from the raw SFDC data using the exact rules defined in the SFDC agent prompt. This ensures the app scoring matches what the agent would produce.

### app/plugins/gtm_signal_board/scoring.py
Implement the full scoring logic as pure Python functions:
- classify_signal_type(account: dict, uccos: list) → SignalType
- compute_urgency(account: dict, signals: list) → Urgency
- recommend_play(signal_type: SignalType, account: dict) → str

Rules must match the SFDC agent prompt urgency rules exactly (ERCOT = HIGH, IESO = HIGH, OpenLink named = HIGH, etc.)

---

## GIT SUBMODULE SETUP

In the public repo:
git submodule add git@github.com:[your-org]/nexus-energy-trading-app-internal.git app/plugins/gtm_signal_board

Commit the .gitmodules file to the public repo. The submodule points to the private repo. When someone clones the public repo without credentials, app/plugins/gtm_signal_board/ is empty — the load_plugin_if_available() function catches the ImportError and silently continues with the no-op default.

Update .github/workflows/deploy-public.yml to NOT include a submodule checkout step.

Create .github/workflows/deploy-internal.yml in the PRIVATE repo that: checks out both repos, assembles them, and deploys to Databricks. This workflow is never in the public repo.

---

## SUCCESS CRITERIA

### Public repo (can verify without private plugin):
1. App starts with load_plugin_if_available() executing silently (no ImportError visible in logs)
2. GET /api/v1/gtm/status returns {"available": false, "plugin_loaded": false}
3. GET /api/v1/gtm/signals/anz with Databricks employee header returns 200 with empty list
4. GET /api/v1/gtm/signals/anz with non-employee header returns 403
5. GTMSignalBoard React component renders null for non-employee users
6. GTMSignalBoard React component renders null when available is false
7. grep -r "salesforce\|SFDC\|sfdc_client" app/ (excluding app/plugins/) returns zero matches in public repo

### With private plugin installed (verify separately):
8. GET /api/v1/gtm/status returns {"available": true, "plugin_loaded": true}
9. GET /api/v1/gtm/signals/anz returns SFDC account data scoped to ANZ region
10. Signal scoring matches urgency rules from agent prompt
11. SFDC credentials are read from Databricks Secrets only — not from env vars or files

---

## COMPLETION ARTIFACT
Create: completions/P14-gtm-signal-board.md (in public repo)

Must contain:
- Confirmation of plugin interface structure (public repo)
- GTM status endpoint response (no plugin installed = available: false)
- Employee auth gate test results
- Submodule .gitmodules entry
- Confirmation that private repo is a separate GitHub repository
- Do NOT include any Salesforce configuration or credentials in this file

Commit message: "feat: P14 complete — GTM Signal Board plugin interface"
`
  },
  {
    id: "P15",
    title: "Deployment & Integration",
    subtitle: "Databricks Apps DAB deployment, end-to-end testing, final integration",
    prereqs: ["P11-frontend-anz.md", "P12-frontend-europe.md", "P13-frontend-americas.md", "P14-gtm-signal-board.md"],
    content: `# P15 — Deployment & Integration
## NEXUS: Energy Trading Intelligence Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify ALL of the following completion files exist:
- completions/P11-frontend-anz.md
- completions/P12-frontend-europe.md
- completions/P13-frontend-americas.md
- completions/P14-gtm-signal-board.md

If any are missing, stop and report which are absent.

---

## OBJECTIVE
Deploy NEXUS to the target Databricks Apps workspace, run full end-to-end integration tests, verify all success criteria across the entire application, and produce the final project completion documentation.

---

## STEPS

### Step 1: Build frontend for production
cd app/frontend && npm ci && npm run build
The output goes to app/backend/static/ (configured in vite.config.ts from P00).
Verify: app/backend/static/index.html exists after build.

### Step 2: Validate app.yaml completeness
Verify app/app.yaml includes:
- Command pointing to uvicorn
- All required environment variable references (no hardcoded values)
- Lakebase database resource reference
- Secrets scope reference for SFDC credentials (nexus scope)

### Step 3: Deploy using Databricks CLI MCP
Using the fe-vm profile, execute:
databricks --profile fe-vm bundle deploy --target dev

This deploys the Databricks Asset Bundle to the fe-sandbox workspace. Monitor the output for errors.

### Step 4: Deploy the app
databricks --profile fe-vm apps deploy nexus

Monitor deployment logs until status is RUNNING.

### Step 5: Retrieve the app URL
databricks --profile fe-vm apps get nexus
Note the app URL from the response.

### Step 6: Smoke test the deployed app
Using curl or httpx against the deployed app URL (not localhost):
- GET [app-url]/api/v1/health/ → {"status": "ok", "lakebase_connected": true}
- GET [app-url]/api/v1/anz/prices/current → 4 regions with data
- GET [app-url]/api/v1/europe/prices/current → 8 bidding zones
- GET [app-url]/api/v1/americas/prices/current → multi-ISO data
- GET [app-url]/ → returns index.html (React app)

### Step 7: Full integration test suite
Run the integration test suite against the deployed app URL (not localhost). Write a test file: app/backend/tests/test_integration_deployed.py

This file runs all the same tests as the individual route test files but against the deployed URL. Pass the deployed URL as an environment variable: NEXUS_DEPLOYED_URL.

Integration tests must cover:
- All health endpoints
- All ANZ routes with real data assertions
- All Europe routes including MTU verification
- All Americas routes including IESO date boundary and RTC+B comparison
- GTM status endpoint (available: false for public deployment)
- Employee gate: authenticated as Databricks employee → Signal Board accessible
- Non-employee gate: authenticated as non-employee → Signal Board 403

### Step 8: Frontend E2E verification
Manually navigate the deployed app and verify:
- RegionSelector renders with all 3 region cards
- ANZ module: all 3 panels accessible and showing real data
- Europe module: all 3 panels accessible, REMIT audit simulation works against real Lakebase
- Americas module: all 3 panels accessible, multi-ISO price table shows 9 ISOs
- Navigation: NEXUS wordmark returns to RegionSelector from any panel
- Fonts: JetBrains Mono visible on all numeric values (use browser dev tools to verify computed font)
- No emoji visible anywhere in the rendered app
- No console errors in browser dev tools

### Step 9: Performance verification
Using browser dev tools Network tab:
- Initial page load (index.html + JS bundle): < 3 seconds on standard connection
- /api/v1/anz/prices/current: < 500ms response time
- /api/v1/europe/prices/current: < 500ms
- /api/v1/americas/prices/current: < 1000ms (multi-ISO join is more complex)

If any API response exceeds 1000ms, investigate and optimise (add index, add LIMIT, or add caching).

### Step 10: Data re-seed verification
Verify the data portability guarantee: run data/seeds/anz/00_run_all.sql against the deployed workspace using the CLI MCP. Confirm it completes cleanly and row counts match P03 completion documentation. This proves the app can be moved to another workspace by re-running the SQL files.

---

## FINAL SUCCESS CRITERIA

All of the following must be true for P15 to be complete:

**Infrastructure:**
1. App is RUNNING in the fe-sandbox workspace
2. App URL is accessible from the public internet (standard Databricks Apps behaviour)
3. Health endpoint returns lakebase_connected: true

**Data:**
4. All seed data is present: ANZ (480K+ dispatch intervals), Europe (MTU boundary verified), Americas (IESO date boundary verified, RTC+B boundary verified)
5. Data re-seed is verified: SQL files can reproduce all data in a new workspace

**Backend:**
6. All 7 ANZ routes return correct data
7. All 7 Europe routes return correct data including REMIT audit
8. All 7 Americas routes return correct data including multi-ISO unified LMP
9. GTM status returns {"available": false} on public deployment
10. Employee auth gate working: 403 for non-employees on GTM routes

**Frontend:**
11. RegionSelector renders correctly with 3 region cards
12. All 9 content panels accessible and showing real Lakebase data
13. All numeric values use JetBrains Mono (verified in browser)
14. No emoji in rendered output (verified by DOM inspection)
15. No console errors
16. Performance: all API calls < 1000ms

**Code quality:**
17. mypy --strict passes on all backend Python files
18. TypeScript strict: zero errors
19. All pytest tests pass
20. No TODO comments in any committed file
21. No inline SQL in any Python route file

**Repository:**
22. All completion .md files exist (P00 through P15)
23. GitHub repository is clean (no uncommitted changes)
24. .gitignore correctly excludes .env, static/, node_modules/
25. Public repo contains zero references to Salesforce, SFDC, or internal credentials

---

## FINAL COMPLETION ARTIFACT
Create: completions/P15-deployment-complete.md

This is the project completion document. It must contain:
- Deployed app URL
- Date and time of deployment
- Output of databricks apps get nexus (status section)
- Complete integration test output (pytest -v)
- Performance measurements for all 3 region API endpoints
- Data row count summary for all tables across all 3 regions
- Browser verification confirmation (fonts, no emoji, no console errors)
- Links to all 16 completion .md files (P00-P15)
- Any known limitations or deviations from the original specification

Final commit message: "chore: P15 complete — NEXUS deployed to fe-sandbox Databricks Apps"

---

## AFTER DEPLOYMENT
The project is complete when P15-deployment-complete.md is committed to GitHub and the app is confirmed running at the deployed URL.

To move the app to a different workspace:
1. Clone the public repository
2. Run the SQL files in order: data/schema/01-04, then data/seeds/[region]/00_run_all.sql for each region
3. Configure Databricks Secrets for the target workspace
4. Update databricks.yml workspace host
5. Run: databricks bundle deploy && databricks apps deploy nexus

The app will be running in the new workspace within 15 minutes.
`
  }
];

const regionColours = {
  "P00": "#6366f1", "P01": "#8b5cf6", "P02": "#0ea5e9", "P03": "#14b8a6",
  "P04": "#6b7dd8", "P05": "#d87d3b", "P06": "#ec4899", "P07": "#14b8a6",
  "P08": "#6b7dd8", "P09": "#d87d3b", "P10": "#6366f1", "P11": "#14b8a6",
  "P12": "#6b7dd8", "P13": "#d87d3b", "P14": "#f59e0b", "P15": "#10b981"
};

export default function App() {
  const [selected, setSelected] = useState(null);
  const [copied, setCopied] = useState(null);

  const download = (p) => {
    const blob = new Blob([p.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${p.id}-${p.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadAll = () => {
    prompts.forEach((p, i) => setTimeout(() => download(p), i * 150));
  };

  const copy = (p) => {
    navigator.clipboard.writeText(p.content);
    setCopied(p.id);
    setTimeout(() => setCopied(null), 2000);
  };

  const sel = selected ? prompts.find(p => p.id === selected) : null;
  const col = (id) => regionColours[id] || "#6366f1";

  return (
    <div style={{ background: "#0a0d14", minHeight: "100vh", fontFamily: "'Inter', system-ui, sans-serif", color: "#e4eaf4" }}>

      {/* Header */}
      <div style={{ background: "#0f1520", borderBottom: "1px solid #1a2540", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 22, fontWeight: 300, letterSpacing: "0.25em", color: "#e4eaf4" }}>NEXUS</div>
          <div style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "#4a607d", marginTop: 2 }}>Energy Trading Intelligence Platform — Cursor Prompt Files</div>
        </div>
        <button onClick={downloadAll} style={{ background: "#3b7dd8", border: "none", color: "#fff", padding: "8px 16px", borderRadius: 3, fontFamily: "Inter", fontSize: 12, fontWeight: 600, cursor: "pointer", letterSpacing: "0.05em" }}>
          DOWNLOAD ALL ({prompts.length} FILES)
        </button>
      </div>

      {/* Notes */}
      <div style={{ background: "#0f1a2a", border: "1px solid #1e3a5a", borderLeft: "3px solid #d4921e", margin: "16px 24px", padding: "12px 16px", borderRadius: "0 3px 3px 0" }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "#d4921e", marginBottom: 6 }}>BEFORE YOU START</div>
        <div style={{ fontSize: 12, color: "#7d92b0", lineHeight: 1.6 }}>
          Rust cannot be the Databricks Apps runtime. The confirmed stack is <span style={{ color: "#e4eaf4", fontFamily: "JetBrains Mono, monospace" }}>FastAPI + Python 3.11 + React 18 TypeScript + Vite</span>. Place these .md files in your Cursor project's <span style={{ color: "#e4eaf4", fontFamily: "JetBrains Mono, monospace" }}>.cursorrules/</span> or prompts directory. Each prompt is self-contained — provide them one at a time. Do not start P07 until P06-backend-core.md exists in your completions/ folder. Workspace: <span style={{ color: "#3b7dd8", fontFamily: "JetBrains Mono, monospace" }}>fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com</span>. CLI profile: <span style={{ color: "#3b7dd8", fontFamily: "JetBrains Mono, monospace" }}>fe-vm</span>.
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 160px)" }}>

        {/* File list */}
        <div style={{ width: 300, borderRight: "1px solid #1a2540", overflow: "auto", flexShrink: 0 }}>
          {prompts.map(p => (
            <div key={p.id} onClick={() => setSelected(selected === p.id ? null : p.id)}
              style={{ padding: "12px 16px", borderBottom: "1px solid #0f1520", cursor: "pointer", background: selected === p.id ? "#141c2b" : "transparent",
                borderLeft: selected === p.id ? `3px solid ${col(p.id)}` : "3px solid transparent", transition: "all 0.15s" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 600, color: col(p.id), background: col(p.id) + "20", padding: "2px 7px", borderRadius: 2 }}>{p.id}</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: "#e4eaf4" }}>{p.title}</span>
              </div>
              <div style={{ fontSize: 11, color: "#4a607d", lineHeight: 1.4 }}>{p.subtitle}</div>
              {p.prereqs.length > 0 && (
                <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {p.prereqs.map(r => <span key={r} style={{ fontSize: 9, background: "#1a2540", color: "#7d92b0", padding: "1px 5px", borderRadius: 2, fontFamily: "JetBrains Mono, monospace" }}>{r.replace(".md", "")}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Detail view */}
        <div style={{ flex: 1, overflow: "auto", padding: 24 }}>
          {sel ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 14, fontWeight: 700, color: col(sel.id) }}>{sel.id}</span>
                    <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#e4eaf4" }}>{sel.title}</h2>
                  </div>
                  <p style={{ margin: "4px 0 0", fontSize: 13, color: "#7d92b0" }}>{sel.subtitle}</p>
                  {sel.prereqs.length > 0 && (
                    <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
                      <span style={{ fontSize: 10, color: "#4a607d", letterSpacing: "0.06em", textTransform: "uppercase" }}>REQUIRES:</span>
                      {sel.prereqs.map(r => <span key={r} style={{ fontSize: 10, background: "#1a2540", color: "#d4921e", padding: "2px 6px", borderRadius: 2, fontFamily: "JetBrains Mono, monospace" }}>{r}</span>)}
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => copy(sel)} style={{ background: copied === sel.id ? "#00c99a20" : "#1a2540", border: `1px solid ${copied === sel.id ? "#00c99a" : "#243050"}`, color: copied === sel.id ? "#00c99a" : "#7d92b0", padding: "6px 14px", borderRadius: 3, fontFamily: "Inter", fontSize: 11, fontWeight: 600, cursor: "pointer", letterSpacing: "0.05em" }}>
                    {copied === sel.id ? "COPIED" : "COPY"}
                  </button>
                  <button onClick={() => download(sel)} style={{ background: col(sel.id), border: "none", color: "#fff", padding: "6px 14px", borderRadius: 3, fontFamily: "Inter", fontSize: 11, fontWeight: 600, cursor: "pointer", letterSpacing: "0.05em" }}>
                    DOWNLOAD
                  </button>
                </div>
              </div>
              <div style={{ background: "#0f1520", border: "1px solid #1a2540", borderRadius: 3, padding: 20 }}>
                <pre style={{ margin: 0, fontFamily: "JetBrains Mono, monospace", fontSize: 11.5, lineHeight: 1.7, color: "#c8d3e0", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {sel.content}
                </pre>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 12 }}>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, letterSpacing: "0.15em", color: "#4a607d", textTransform: "uppercase" }}>Select a prompt file to preview</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 20 }}>
                {prompts.map(p => (
                  <div key={p.id} onClick={() => setSelected(p.id)}
                    style={{ background: "#0f1520", border: `1px solid ${col(p.id)}30`, padding: "10px 14px", borderRadius: 3, cursor: "pointer", borderLeft: `3px solid ${col(p.id)}` }}>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 700, color: col(p.id) }}>{p.id}</div>
                    <div style={{ fontSize: 11, color: "#7d92b0", marginTop: 3 }}>{p.title}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
