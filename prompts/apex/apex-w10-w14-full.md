# APEX W10–W14: Risk + Portfolio APIs + Frontend Shell + UI Workspaces

---

# W10 — Risk Engine API

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-seeds.md exist.

## Lakebase writes: VaR results, stress test results (+ async Delta sync for Genie).

## SQL QUERIES: data/queries/risk/

### var_latest.sql — most recent VaR per trader/market :trader_id :market
### var_history.sql — trend last 30 days :trader_id :market :days
### price_returns_history.sql
```sql
-- Log returns for each instrument over last 252 days
-- Used as Monte Carlo input
SELECT instrument_id, market,
       LN(rrp / LAG(rrp) OVER (PARTITION BY region_id ORDER BY interval_datetime)) AS log_return
FROM apex.market_nem.prices
WHERE interval_datetime >= CURRENT_TIMESTAMP - INTERVAL 252 DAYS
  AND rrp > 0
-- UNION ALL equivalent for EPEX and ERCOT
```
### stress_scenarios.sql — all scenarios :market (optional)
### stress_results_history.sql — :trader_id :market :days
### credit_exposure.sql — :counterparty_id (optional) :market
### trading_limits.sql — :trader_id :market
### limit_breaches.sql — current breaches :trader_id :market

## ROUTES: app/backend/routes/risk.py

```python
GET  /api/v1/risk/var                    # latest VaR ?market&trader_id
POST /api/v1/risk/var/calculate          # trigger Monte Carlo → Lakebase write
GET  /api/v1/risk/var/history            # trend ?market&trader_id&days=30
GET  /api/v1/risk/scenarios              # all stress scenarios ?market
POST /api/v1/risk/stress-test            # run scenario → Lakebase write
GET  /api/v1/risk/stress-test/history    # ?market&trader_id&days=30
GET  /api/v1/risk/credit                 # credit exposure ?market
GET  /api/v1/risk/limits                 # all limits ?market&trader_id
GET  /api/v1/risk/limits/breaches        # current breaches ?market&trader_id
```

### POST /api/v1/risk/var/calculate — full implementation
```python
@router.post("/var/calculate")
async def calculate_var(req: VaRRequest) -> VaRResult:
    # 1. Fetch current positions (SQL Warehouse → Delta gold_positions)
    positions = await query_warehouse(POSITION_BOOK_SQL, {"market": req.market})

    # 2. Fetch 252-day price returns per instrument
    returns = await query_warehouse(PRICE_RETURNS_SQL, {"market": req.market})
    returns_by_instrument = group_returns_by_instrument(returns)

    # 3. Run Monte Carlo (numpy — <1s for 10k simulations)
    var_input = VaRInput(
        positions=positions,
        price_returns=returns_by_instrument,
        simulation_count=req.simulation_count,
        currency=MARKET_CURRENCY[req.market]
    )
    result = run_monte_carlo_var(var_input)

    # 4. Bucket distribution into 100 bins
    pnl_dist = bucket_distribution(result.simulated_pnl, bins=100)

    # 5. Write to Lakebase
    var_record = {...}
    async with get_lakebase() as conn:
        await conn.execute(INSERT_VAR_SQL, var_record)

    # 6. Async sync to Delta for Genie
    asyncio.create_task(append_to_delta("apex.risk.var_results", var_record))

    # 7. Check and update limit utilisation
    await update_var_limit_utilisation(req.trader_id, req.market, result.var_99)

    return VaRResult(**var_record, pnl_distribution=pnl_dist)
```

### Currency-aware VaR
All VaR calculations use correct currency per market:
- NEM → AUD
- EPEX → EUR
- ERCOT → USD
VaRResult always includes `currency` field. No cross-currency aggregation unless explicitly requested.

## SUCCESS CRITERIA
1. POST /var/calculate returns in < 3s (measure with stopwatch)
2. VaR_99 > VaR_95 on every run — verified in tests
3. CVaR > VaR on every run
4. pnl_distribution: list of exactly 100 ints summing to simulation_count
5. Result written to Lakebase — verify with SELECT
6. Result queryable in Delta via Genie within 60s
7. Stress test applies correct shock to positions — verify manually
8. All currency fields match market (AUD/EUR/USD)

## COMPLETION ARTIFACT
completions/W10-risk-api.md

---

# W11 — Portfolio API

## PREREQUISITE CHECK
Verify completions/W06-backend-core.md AND completions/W05-seeds.md exist.

## SQL QUERIES: data/queries/portfolio/

### revenue_actuals.sql — :market :asset_id (optional) :days
### revenue_forecast.sql — :market :asset_id :scenario :months
### ppa_book.sql — :market, includes counterparty join
### asset_benchmarking.sql — :market, revenue per MW vs benchmark
### revenue_components.sql — monthly stacked breakdown :market :months

## ROUTES: app/backend/routes/portfolio.py

```python
GET  /api/v1/portfolio/revenue/actuals      # ?market&asset_id&days=365
GET  /api/v1/portfolio/revenue/forecast     # ?market&asset_id&scenario=BASE&months=24
GET  /api/v1/portfolio/revenue/components   # ?market&asset_id&months=12 — stacked bar data
GET  /api/v1/portfolio/ppa                  # all PPAs with MTM ?market
GET  /api/v1/portfolio/ppa/{ppa_id}         # single PPA
POST /api/v1/portfolio/ppa/{ppa_id}/mark    # recalculate MTM → Lakebase write
GET  /api/v1/portfolio/benchmarking         # all assets vs benchmark ?market
POST /api/v1/portfolio/revenue-stack/simulate  # interactive simulator — no DB write
```

### Revenue stacking simulator — market-aware
```python
def simulate_revenue_stack(inputs: RevenueStackingInput,
                            market: str, market_data: dict) -> RevenueStackingResult:
    currency = {"NEM": "AUD", "EPEX": "EUR", "ERCOT": "USD"}[market]

    # NEM: energy revenue based on TB4 spread (top 4 hours - bottom 4 hours)
    # EPEX: energy revenue based on day-ahead price range and arbitrage
    # ERCOT: energy revenue based on daily LMP spread + RTC+B premium (if live)

    if market == "ERCOT":
        rtcb_live = datetime.now().date() >= date(2025, 12, 5)
        rtcb_premium = market_data.get("avg_rtcb_premium", 0) if rtcb_live else 0
        energy_rev = base_energy_rev + (rtcb_premium * inputs.capacity_mw * 365)
    ...
    return RevenueStackingResult(
        energy_revenue=energy_rev, fcas_revenue=fcas_rev,
        cap_revenue=cap_rev, ppa_revenue=ppa_rev,
        total_annual_revenue=total, currency=currency,
        assumptions={...}
    )
```

## SUCCESS CRITERIA
1. Revenue actuals covers all 15 assets across 3 markets
2. ERCOT assets show rtcb_revenue=NULL before 2025-12-05, non-null after
3. PPA mark updates Lakebase and Delta
4. Revenue simulator returns in < 500ms
5. ERCOT simulator shows higher revenue post-RTC+B than pre (monotonic)
6. All currency amounts match market

## COMPLETION ARTIFACT
completions/W11-portfolio-api.md

---

# W12 — Frontend Shell (Market Selector + Persona + Workspace)

## PREREQUISITE CHECK
Verify completions/W01-design-system.md AND completions/W06-backend-core.md exist.

## TWO-STAGE NAVIGATION

### Stage 1 — MarketSelector.tsx (route: /)

Full viewport. Vertically and horizontally centred.

Header:
- "APEX" in font-data 28px weight 300 letter-spacing 0.3em, colour text-secondary
- "ENERGY ANALYTICS PLATFORM · POWERED BY DATABRICKS" in label-caps text-tertiary below

Three market cards in a row (or stacked on narrow):

```
┌─────────────────────────────────────────────────────────────────┐
│              ◈ NEM              ◈ EPEX              ◈ ERCOT    │
│         ┌──────────┐       ┌──────────┐       ┌──────────┐    │
│         │ [blue]   │       │ [purple] │       │ [amber]  │    │
│         │Australia │       │ Europe   │       │ Americas │    │
│         │          │       │          │       │          │    │
│         │5-min spot│       │DA auction│       │Nodal LMP │    │
│         │FCAS/ASX  │       │15-min MTU│       │RTC+B     │    │
│         │AUD       │       │EUR       │       │USD       │    │
│         │          │       │          │       │          │    │
│         │[ENTER →] │       │[ENTER →] │       │[ENTER →] │    │
│         └──────────┘       └──────────┘       └──────────┘    │
│                                                                  │
│  ● NEM A$94/MWh    ◉ EPEX €71/MWh    ◉ ERCOT $47/MWh          │
└─────────────────────────────────────────────────────────────────┘
```

Market card styling:
- Width ~280px, border 1px border-default, border-radius radius-md
- On hover: border-color → market accent colour, transform translateY(-2px)
- Top accent line 3px in market colour
- NEM: #60A5FA (blue), EPEX: #A78BFA (purple), ERCOT: #FBBF24 (amber)
- Market icon: simple geometric — NEM (wave), EPEX (EU stars), ERCOT (lightning bolt) — SVG inline

Market status strip below cards: real prices from useMarketSummary hook. 30s refetch.
Green dot = market open, grey = closed. Prices in font-data.

On card click: store market in Zustand marketStore, navigate to /nem | /epex | /ercot.

---

### Stage 2 — PersonaSelector.tsx (route: /nem | /epex | /ercot)

Header:
- ← back to market selector
- Market badge (e.g. "NEM" in blue pill)
- "SELECT YOUR WORKSPACE" in label-caps

Five persona cards. Descriptions market-specific per current market:

| Persona | NEM | EPEX | ERCOT |
|---|---|---|---|
| Dispatch | "FCAS offer stacks · AEMO dispatch · SOC monitoring" | "Balancing reserve · EPEX intraday · SOC monitoring" | "RTC+B dispatch · ERCOT real-time · SOC monitoring" |
| Trader | "Position analytics · Aligne ingestion · ASX futures" | "DA/intraday positions · Endur ingestion · EU ETS" | "Nodal exposure · Triple Point ingestion · basis analysis" |
| Risk | "VaR Monte Carlo · NEM stress scenarios · AUD" | "VaR Monte Carlo · EU cold snap scenarios · EUR" | "VaR Monte Carlo · ERCOT summer scenarios · USD" |
| Quant | "NEM price forecast · FCAS signal analysis" | "DA price model · renewable surplus patterns" | "LMP forecast · RTC+B signal analysis" |
| Portfolio | "BESS revenue stacking · PPA book · ASX benchmarking" | "Storage arbitrage · EU ETS hedging · revenue forecast" | "Battery revenue · wind basis · RTC+B premium" |

Card persona accent colours (unchanged from original design). On click: navigate to /{market}/{persona}/...

---

### WorkspaceLayout.tsx
Props: market, persona, children.

Topbar (48px fixed):
- Left: "APEX" wordmark (→ /), separator, MarketBadge component (shows market in accent colour), separator, persona name in persona accent colour (label-caps)
- Centre: live price ticker for current market. NEM: 5 regions. EPEX: top 4 zones. ERCOT: top 4 nodes. font-data text-xs, 30s refetch via useMarketSummary hook
- Right: clock in font-data text-xs (HH:MM:SS local, 1s tick), separator, trader name

Sidebar (192px):
- Navigation for current persona's pages
- Active item: 2px left border in persona accent colour, bg-raised
- Section headers in label-caps text-tertiary

Status bar (28px fixed bottom):
- Left: Lakebase status (green dot "CONNECTED" or amber "DEGRADED") + latency in ms
- Centre: "Source: [ETRM source] · Last sync [timestamp] · [N]s ago" — SourceProvenanceBar inline
- Right: Session P&L in font-data for trading/risk personas (pnl-positive/negative)

---

### Router: app/frontend/src/router.ts

```typescript
/                                  → MarketSelector
/nem                               → NEM PersonaSelector
/nem/dispatch/console              → DispatchConsole
/nem/dispatch/fleet                → FleetOverview
/nem/trader/analytics              → TradingAnalytics
/nem/trader/positions              → PositionBook
/nem/risk/var                      → VaRDashboard
/nem/risk/stress                   → StressTestPanel
/nem/risk/limits                   → LimitMonitor
/nem/risk/credit                   → CreditExposure
/nem/quant/models                  → ModelPerformance
/nem/quant/backtest                → BacktestConsole
/nem/quant/signals                 → SignalScanner
/nem/portfolio/revenue             → RevenueDashboard
/nem/portfolio/ppa                 → PPABook
/nem/portfolio/assets              → AssetBenchmarking

/epex/* → same structure as /nem/*
/ercot/* → same structure as /nem/*
```

All page components receive `market` prop from router params. All hooks receive market from Zustand marketStore.

---

### Zustand stores

#### marketStore.ts
```typescript
type Market = 'NEM' | 'EPEX' | 'ERCOT';
interface MarketStore {
  selectedMarket: Market | null;
  marketCurrency: string;          // AUD | EUR | USD
  marketTimezone: string;
  marketAccentColor: string;
  marketSourceSystem: string;      // ALIGNE_SIM | ENDUR_SIM | TRIPLE_POINT_SIM
  setMarket: (m: Market) => void;
}
const MARKET_CONFIG = {
  NEM:   {currency:'AUD', tz:'Australia/Brisbane', color:'var(--color-market-nem)',   source:'ALIGNE_SIM'},
  EPEX:  {currency:'EUR', tz:'Europe/Paris',       color:'var(--color-market-epex)',  source:'ENDUR_SIM'},
  ERCOT: {currency:'USD', tz:'America/Chicago',    color:'var(--color-market-ercot)', source:'TRIPLE_POINT_SIM'},
}
```

#### tradingStore.ts
```typescript
interface TradingStore {
  selectedInstrument: string | null;
  activePersona: 'dispatch'|'trader'|'quant'|'risk'|'portfolio' | null;
  sessionPnl: Decimal | null;
  sessionCurrency: string;
  setSelectedInstrument: (id: string) => void;
  setSessionPnl: (pnl: Decimal, currency: string) => void;
}
```

#### dispatchStore.ts
```typescript
interface DispatchStore {
  selectedAssetId: string | null;
  activeStackDraft: OfferStackDraft | null;
  activeServiceType: string;
  setSelectedAsset: (id: string) => void;
  updateBand: (bandNumber: number, field: 'price'|'volume', value: Decimal) => void;
  clearDraft: () => void;
}
```

---

### API client: app/frontend/src/api/client.ts
```typescript
const client = axios.create({ baseURL: '/api/v1', timeout: 30000 });

// Inject market header on every request
client.interceptors.request.use(config => {
  const market = useMarketStore.getState().selectedMarket;
  if (market) config.params = { ...config.params, market };
  return config;
});

// Unwrap APIResponse wrapper
client.interceptors.response.use(r => r.data.data ?? r.data);
```

## SUCCESS CRITERIA
1. / opens MarketSelector with live prices in status strip
2. Click NEM → /nem PersonaSelector with NEM-specific descriptions
3. Click TRADER on NEM → /nem/trader/analytics workspace
4. Topbar shows correct market badge and accent colour
5. Status bar SourceProvenanceBar shows correct ETRM source per market
6. Switching markets (back → select ERCOT) changes all ticker symbols
7. Clock ticks every second
8. TypeScript strict: zero errors

## COMPLETION ARTIFACT
completions/W12-frontend-shell.md

---

# W13 — Dispatch Console

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W09-dispatch-api.md exist.

## PAGE: /{market}/dispatch/console — DispatchConsole.tsx

Three-column layout.

### Column 1 (264px): Fleet Monitor

**FleetStatusPanel**
Title: "FLEET — [MARKET]" in label-caps with market accent colour dot.

Each asset row (AssetStatusRow):
- Asset name abbreviated, font-data text-sm text-primary
- SOC bar: CSS width proportional (60px × soc/100), colour:
  - > 60%: color-bid (green)
  - 20–60%: color-warning (amber)
  - < 20%: color-offer (red)
- SOC percentage: font-data mono-mw
- Output MW: positive = pnl-positive, negative = pnl-negative (charging), font-data
- For ERCOT assets: small "RTC+B" badge if rtcb_eligible AND rtcb_signal is live (post Dec 2025)
- Stack status badge (DRAFT / SUBMITTED / DISPATCHED / NONE)
- Selected row: 2px left border in persona colour (dispatch = #60A5FA)

Hook: useFleetStatus(?market), refetchInterval: 15000

**Market-specific pre-dispatch strip** below fleet list:
- NEM: pre-dispatch RRP next 12 intervals (60 min). Sparkline + colour-coded cells
- EPEX: next 8 hourly DA prices for selected asset's zone
- ERCOT: next 12 real-time LMP forecasts for asset's node. If RTC+B live: show rtcb_signal vs forecast comparison ("RTC+B vs DA spread: +$X")

---

### Column 2 (flex): Offer Stack Builder

**AssetHeader**
Asset name, capacity MW, duration hours, market, region/node.

SOC circular gauge (SVG, hand-coded):
- Outer ring: bg-raised
- SOC arc: colour coded (bid/warning/offer per threshold)
- Centre: percentage in font-data text-2xl
- Below: "Available: XXX MW" in font-data text-secondary

**ServiceTypeSelector** (tabs)
NEM: ENERGY / RAISE 6S / LOWER 6S / RAISE REG / LOWER REG / RAISE 5M / LOWER 5M
EPEX: ENERGY / BALANCING_RESERVE
ERCOT: ENERGY / REGUP / REGDOWN / ECRS

For ERCOT, if RTC+B is live and asset is rtcb_eligible: show a yellow banner:
"RTC+B ACTIVE — Recommendations incorporate real-time signal"

**OfferStackBuilder**
10 bands. Each band uses OfferBand primitive.
- Band number in label-caps
- Price input: font-data, right-aligned, currency suffix (A$/€/$) from market context
- Volume input: font-data, right-aligned, "MW" suffix
- Red border on price input if price ≤ previous band (ascending constraint)
- Dispatched MW (read-only from last interval)

Below bands:
- Total MW (sum of bands). "OVER CAPACITY" warning in offer colour if > asset capacity_mw
- Volume allocation bar: CSS flex proportional to each band's MW

Action buttons:
- SUBMIT STACK (primary, accent background): validates → POST offer stack → ConfirmationToast
- CLEAR DRAFT: resets to seeded values
- LOAD FROM RECOMMENDATION: populates from top recommendation

---

### Column 3 (264px): Recommendations + History

**DispatchRecommendationPanel**
Title: "DISPATCH RECOMMENDATIONS" label-caps

Each recommendation (12 intervals):
- Interval timestamp, font-data text-xs
- Action: "DISCHARGE 185MW @ A$142/MWh" — use correct currency
- For ERCOT post-Dec-2025: "DISCHARGE 220MW @ $85/MWh ⟵ RTC+B" (show RTC+B attribution)
- Confidence bar (30px) + percentage
- Expected revenue in pnl-positive font-data, correct currency
- ACCEPT button: small, bid-colour border

Model version in text-2xs text-tertiary at bottom.

**RebidPanel** (NEM only — NEL s.254):
Active stack bands (read-only). REBID toggle shows:
- Reason field (required textarea, bg-input)
- PRE-VALIDATE button → calls compliance check endpoint, shows ComplianceCheck result
- SUBMIT REBID (disabled until compliance check passes)

For EPEX/ERCOT: show "REPLACE STACK" instead — no rebid concept.

**StackHistoryTable**
DataTable compact (28px rows). Columns: INTERVAL / SERVICE / STATUS / MW / REBID / BY
Click row: side panel shows all 10 bands.

---

## PAGE: /{market}/dispatch/fleet — FleetOverview.tsx

Full-width grid. All assets in the current market.
Each card: asset name, operator, region/node, capacity, SOC gauge, today's revenue (currency-correct), SOC sparkline (24h), stack status badge.

For ERCOT: show RTC+B status badge on eligible assets.

---

## SUCCESS CRITERIA
1. FleetMonitor shows all assets for selected market only
2. ERCOT assets show "RTC+B" badge post-Dec-2025
3. SOC gauge circular SVG renders correctly at 0%, 50%, 100%
4. ServiceTypeSelector shows market-correct tabs (7 NEM, 2 EPEX, 4 ERCOT)
5. Ascending price validation works — red border on violation
6. Submit creates rows in Lakebase AND Delta (Genie queryable within 60s)
7. ERCOT recommendations show rtcb_adjusted=True when live
8. NEM rebid requires reason — PRE-VALIDATE fails without it
9. ConfirmationToast appears on submit — no emoji in text
10. Live SOC values update every 15s (verify by watching page for 30s)

## COMPLETION ARTIFACT
completions/W13-dispatch-console.md

---

# W14 — Trading Analytics Workspace

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W08-trade-analytics-api.md exist.

## CRITICAL: No deal entry form. This workspace shows analytics on positions ingested from the ETRM.

## PAGE: /{market}/trader/analytics — TradingAnalytics.tsx

Four-panel CSS grid layout.

---

### Panel A (top, full width, 52px): Live Price Strip

PriceTicker components for current market:
- NEM: QLD1, NSW1, VIC1, SA1, TAS1 — shows rrp, change, bid/offer
- EPEX: DE-LU, FR, BE, NL, ES — shows price_eur_mwh, change
- ERCOT: West, Houston, North, South, Panhandle W1 — shows lmp, rtcb_signal (if live)

For ERCOT post-Dec-2025: RTC+B values shown below main price in text-2xs text-secondary: "RTC+B: $47.32"

Spike alert: if NEM RRP > A$1,000 OR ERCOT LMP > $500: full-width amber bar above ticker:
"PRICE ALERT — [REGION] [PRICE] — Review positions"

Hook: useMarketPricesCurrent(market), refetchInterval: 15000. Price flash animation fires on every update.

---

### Panel B (left 36%): Exposure Analytics — REPLACES deal entry form

**NetExposureHeatmap**
Title: "NET EXPOSURE — [MARKET]"

Grid table:
- Rows: regions/nodes for current market
  - NEM: QLD1 / NSW1 / VIC1 / SA1 / TAS1
  - EPEX: DE-LU / FR / BE / NL / ES
  - ERCOT: West Hub / Houston Hub / North Hub / South Hub
- Columns: delivery periods (Q1-2026 / Q2-2026 / Q3-2026 / Q4-2026 / Cal-2027)
- Cell: net_volume_mw in font-data
- Cell background: interpolated between bid-dim (long) and offer-dim (short), intensity = position size vs limit
- Zero position: bg-surface, text-muted "—"
- Click cell: loads position detail for that region × period in Panel C

**P&L Attribution Summary** (below heatmap):
Four Metric components (compact, size='sm'):
- TODAY REALISED P&L (currency-correct)
- UNREALISED MTM P&L (currency-correct)
- LARGEST LONG: "NSW1 +320MW" with region badge
- LARGEST SHORT: "SA1 −180MW" with region badge

**Source Provenance Panel** (below attribution):
SourceProvenanceBar component. Shows:
"[ALIGNE_SIM | ENDUR_SIM | TRIPLE_POINT_SIM] → last sync [time] ([N]s ago) · [N] positions"

Colour: green <60s, amber 1–5min, red >5min.
"Data ingested via DLT pipeline · Bronze→Silver→Gold · View lineage" link to DLT pipeline UI.

Hook: useSourceLag(market), refetchInterval: 30000

---

### Panel C (top right, 64%): Position Book

DataTable. Title: "POSITION BOOK — [ETRM_SOURCE] via DLT"
Columns:
- INSTRUMENT | REGION | PERIOD | NET MW | AVG PRICE | MKT PRICE | MTM P&L | SOURCE

NET MW: positive = bid colour, negative = offer colour, font-data mono-mw
Apply row-long/row-short class per direction.
AVG PRICE / MKT PRICE: font-data mono-price with correct currency prefix (A$ / € / $)
MKT PRICE: price-up / price-down class if changed since last render (flash on update)
MTM P&L: font-data, pnl-positive or pnl-negative. Format: "+A$398,400" or "−€42,000"
SOURCE: source-tag CSS class, small ALIGNE/ENDUR/TRIPLE text

Double-click row: TradeDetail side panel (slides from right, 320px). Shows all fields.

Total row at bottom: "TOTAL UNREALISED P&L: +[CURRENCY][AMOUNT]" in font-data text-2xl pnl-positive/negative.

Hook: usePositionBook(market, traderId), refetchInterval: 10000

---

### Panel D (bottom right, 64%): Trade Blotter (read-only)

DataTable. Title: "TRADE BLOTTER — READ ONLY · Source: [ETRM]"
Columns:
- TIME | INSTRUMENT | DIR | VOL MW | PRICE | COUNTERPARTY | STATUS | SOURCE | INGESTED

DIRECTION: "BUY" in bid colour, "SELL" in offer colour
INGESTED: small timestamp showing when DLT wrote this record (text-2xs text-tertiary)
SOURCE: source-tag component

Filter bar: Market (locked to current), Status dropdown (ALL/CONFIRMED/PARTIAL/CANCELLED), Days (7/30/90).

No cancel/edit buttons — this is read-only analytics.
A note in the panel header: "Trades are booked in [ETRM_SOURCE]. Data arrives via DLT ingestion."

Hook: useTradeBlotter(market, traderId, status, days), staleTime: 5000

---

## PAGE: /{market}/trader/positions — PositionBook.tsx (full page)
Full-width position book with:
- Same DataTable as Panel C but with more columns and sorting
- Position history chart (net MW change last 30 days per region) — Recharts LineChart
- Attribution table: P&L by instrument type and counterparty

## SUCCESS CRITERIA
1. Exposure heatmap cells correctly colour long positions green, short red
2. Clicking a heatmap cell loads matching positions in Panel C
3. SourceProvenanceBar shows correct ETRM source (ALIGNE_SIM for NEM, etc.)
4. SourceProvenanceBar goes amber after 90s of no new data (verify by stopping simulator)
5. Position book MTM P&L updates when market prices change (10s refetch)
6. Price flash animation fires on Panel A ticker update
7. Trade blotter shows source and ingested_at columns
8. "Data arrives via DLT ingestion" note visible in Panel D header
9. ERCOT panel shows rtcb_signal in Panel A ticker after Dec 2025 boundary
10. No deal entry form anywhere in this workspace — verified by DOM inspection

## COMPLETION ARTIFACT
completions/W14-trading-analytics.md
