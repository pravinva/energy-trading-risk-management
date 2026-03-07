# W13 — Dispatch Console
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W09-dispatch-api.md exist.

---

## OBJECTIVE
Build the Dispatch Operator workspace. This is a functioning BESS dispatch console where an operator can monitor their fleet, view ML dispatch recommendations, build and submit offer stacks, and execute compliant rebids. Every action writes to Lakebase.

---

## PAGE: /dispatch/console — DispatchConsole.tsx

This is the main dispatch workspace. Split into three columns:

### Column 1 (280px): Fleet Monitor

**FleetStatusPanel**
List of all BESS assets. Each row is a compact AssetStatusRow:
- Asset name (abbreviated — HORNSDALE, WARATAH, ERARING etc.) in --text-sm
- SOC%: inline bar (60px SVG, 6px height) + percentage in --font-data --text-sm --mono-mw
- Output MW: positive=dispatch colour, negative=charging colour, 0=flat in --font-data
- Available MW in --color-text-secondary
- Stack status badge: DRAFT/SUBMITTED/DISPATCHED/NONE

Clicking a row selects the asset and loads its detail in Column 2 and 3.
Selected row highlighted with persona colour left border.
Hook: useFleetStatus, refetchInterval: 15000.

**Pre-Dispatch Signal Strip**
Below the fleet list. Shows next 12 forecast RRP values (next 60 min) for the selected asset's region as a compact sparkline with the values displayed. Colour coded: green if > $150 (dispatch opportunity), amber $50-150, blue < $50 (charging opportunity).
Hook: useNEMPreDispatch(regionId), refetchInterval: 15000.

---

### Column 2 (middle, flex 1): Offer Stack Builder

**AssetHeader**
Selected asset name, capacity, duration, region. Current SOC prominently displayed: a circular gauge (SVG, no library needed — 4 arcs representing 0/25/50/75/100%) with the percentage in --font-data --text-2xl in the centre. Colour: green > 60%, amber 20-60%, red < 20%.

**ServiceTypeSelector**
Tabs: ENERGY / RAISE 6S / LOWER 6S / RAISE REG / LOWER REG / RAISE 5M / LOWER 5M
Select which offer stack to build. Each tab shows current stack status badge.

**OfferStackBuilder**
The core interactive component. 10 rows, one per band. Uses OfferBand primitive (from W01 design system).

Each band row:
- Band number in --label-caps (BAND 1 through BAND 10)
- Price input: --font-data, right-aligned, suffix "$/MWh". Validates as Decimal. Shows red border if price < previous band (ascending constraint).
- Volume input: --font-data, right-aligned, suffix "MW". Validates as Decimal > 0.
- Dispatched MW: read-only, shows actual dispatch from last interval in --color-bid dim
- Drag handle: allows reordering bands (react-beautiful-dnd or similar — no emoji for the handle, use "⠿" dotted grid character which is standard DnD convention)

Below the bands:
- Total MW: sum of all band volumes in --font-data. Shows "OVER CAPACITY" warning if > asset capacity in --color-offer.
- Volume bar: proportional visualisation of MW allocation across bands (simple CSS flex bar, no library)

**Action buttons (bottom of Column 2):**
- SUBMIT STACK — disabled if any validation error. On click: calls POST /api/v1/dispatch/{asset_id}/offer-stack. On success: show ConfirmationToast "Offer stack submitted for [INTERVAL]". Resets draft state.
- CLEAR DRAFT — resets all band inputs to the pre-seeded values
- LOAD FROM RECOMMENDATION — populates bands from the latest ML recommendation

---

### Column 3 (280px): Recommendations + History

**DispatchRecommendationPanel**
List of ML/deterministic dispatch recommendations for next 12 intervals.
Each recommendation:
- Interval time in --font-data --text-xs
- Recommended action: "DISCHARGE 185 MW @ $142/MWh" or "CHARGE 120 MW" in --text-sm
- Confidence score: small bar (30px) + percentage
- Expected revenue in --font-data pnl-positive
- ACCEPT button (small, --color-bid border, no fill) — calls accept endpoint, creates offer stack

At bottom: model version in --text-2xs --color-text-tertiary

**RebidPanel**
Shows current active stack for selected interval. 
If a stack is already submitted and the operator wants to change it:
- "REBID" toggle unlocks the band inputs
- Reason field (required): textarea in --color-bg-input
- PRE-VALIDATE button calls compliance check endpoint, shows result
- SUBMIT REBID enabled only if compliance check passes

**StackHistoryTable**
DataTable of last 7 days of offer stack submissions for selected asset.
Columns: INTERVAL / SERVICE / STATUS / BANDS SUBMITTED / ACCEPTED? / SUBMITTED BY
Compact — 28px row height. Click row to see the bands in a side panel.

---

## PAGE: /dispatch/fleet — FleetOverview.tsx

Full-width grid view of all 8 BESS assets. Each asset shown as a card:
- Asset name, operator, region, capacity
- SOC circular gauge (same as detail view but smaller)
- Output MW (real-time)
- Today's revenue in --font-data pnl-positive
- Spark line of SOC last 24 hours
- Current stack status badge

Uses useFleetStatus + useFleetRevenue hooks.

---

## HOOKS: app/frontend/src/api/hooks/dispatch.ts
- useFleetStatus: GET /api/v1/dispatch/fleet, refetchInterval: 15000
- useAssetStatus(assetId: string): GET /api/v1/dispatch/{assetId}/status, refetchInterval: 10000
- useOfferStack(assetId: string, serviceType: string): GET /api/v1/dispatch/{assetId}/offer-stack
- useDispatchRecommendations(assetId: string): GET /api/v1/dispatch/{assetId}/recommendations, refetchInterval: 30000
- useStackHistory(assetId: string, days: number): staleTime: 60000
- submitOfferStack(assetId, draft): POST mutation
- submitRebid(assetId, stackId, rebidRequest): POST mutation
- checkCompliance(assetId, stackId, request): POST mutation (called on demand)
- acceptRecommendation(assetId, recId): POST mutation

---

## SUCCESS CRITERIA
1. FleetMonitor shows all 8 BESS assets with real SOC data
2. Selecting an asset loads its detail in Columns 2 and 3
3. Offer stack builder validates ascending prices — red border on violation
4. Volume total shows over-capacity warning when exceeded
5. Submit stack writes to Lakebase (verify with GET after submit)
6. Accept recommendation creates a stack (verify with stack history update)
7. Rebid without reason string: PRE-VALIDATE shows compliance error
8. SOC circular gauge renders correctly for 0%, 50%, 100%
9. ConfirmationToast appears on successful submit
10. No emoji anywhere (⠿ drag handle is acceptable as it is a functional symbol)
11. Vitest tests pass for all Dispatch components

---

## COMPLETION ARTIFACT
completions/W13-dispatch-console.md
Commit message: "feat: W13 complete — Dispatch Operator console"

---
---

# W14 — Trading Blotter
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W08-trade-management-api.md exist.

---

## OBJECTIVE
Build the Power Trader workspace. A functioning trading blotter where traders can enter deals, monitor their position book with live P&L mark-to-market, manage open orders, and receive spike alerts requiring immediate action.

---

## PAGE: /trader/blotter — TradingBlotter.tsx

Four-panel layout using CSS grid.

### Panel A (top, full width): Price Strip
The PriceTicker component (from W01 design system) for each NEM region + EPEX DE-LU + ERCOT West Hub. Displayed as a horizontal strip of tickers. Each shows: region/zone, last price, change, bid/offer.
Price flash animation triggers on every update.
Hook: useNEMCurrentPrices + useEPEXCurrent + useERCOTCurrent. refetchInterval: 15000.

---

### Panel B (left 40%): Trade Entry Form

**InstrumentSelector**
Searchable dropdown (no emoji — styled select with search input overlay). Options grouped: NEM Spot (5 regions), ASX Futures (cal, quarterly), Bilateral, FCAS (7 services × 5 regions). On select: loads current price from market data, populates indicative price field.

**TradeEntryForm**
This is the core functional component. Fields:
- DIRECTION: Two buttons "BUY" and "SELL". BUY styled with --color-bid border when selected. SELL with --color-offer. Only one can be active.
- VOLUME: number input in --font-data. Suffix "MW". Validates > 0. Decimal.js.
- PRICE: number input in --font-data. Suffix "$/MWh". Shows live market price hint below: "MARKET: $87.42/MWh". Negative prices allowed. Decimal.js.
- COUNTERPARTY: searchable select from apex.reference.counterparties.
- DELIVERY START: datetime-local input.
- DELIVERY END: datetime-local input. Must be after delivery start.
- TRADE TYPE: select — SPOT, BILATERAL, FUTURES, SWAP, CAP.
- NOTES: optional textarea, 2 rows.

Below form:
- P&L ESTIMATE: calculated in real-time as user types. Shows expected MTM P&L if this trade were executed at current market price. "(current_price - trade_price) × volume × hours = +$X,XXX AUD" in --font-data pnl-positive or pnl-negative.
- SUBMIT TRADE button. On click: POST /api/v1/trades/. On success: ConfirmationToast ("BUY 150MW NSW1 @ $86.50/MWh | CONFIRMED"), reset form, update position book.
- CLEAR button: resets form.

Validation (all client-side before submit):
- Volume must be > 0
- Delivery end must be after delivery start
- Counterparty must be selected
- Instrument must be selected
- Price must be a valid number

---

### Panel C (top right, 60%): Position Book

**PositionBook**
DataTable showing all current positions. Columns:
- INSTRUMENT / REGION / PERIOD / NET POSITION MW / AVG PRICE / MARKET PRICE / MTM P&L

NET POSITION: positive = "--color-bid font-data mono-mw" with row-long class. Negative = "--color-offer" with row-short class.
AVG PRICE: --font-data mono-price.
MARKET PRICE: --font-data mono-price with price-up/price-down class if changed since last render.
MTM P&L: --font-data. pnl-positive if positive, pnl-negative if negative. No currency symbol just number with 2dp and comma separator.

Below table:
TOTAL MTM P&L: a prominent Metric component showing the sum of all position MTM P&Ls. Large --font-data --text-2xl in pnl-positive or pnl-negative. Labels: "TOTAL UNREALISED P&L" and "TODAY'S REALISED P&L" side by side.

Hook: usePositionBook, refetchInterval: 10000 (positions update frequently as market moves).

---

### Panel D (bottom right, 60%): Blotter

**TradeBlotter**
DataTable of all trades. Columns:
- TIME / INSTRUMENT / DIRECTION / VOLUME MW / PRICE / COUNTERPARTY / MTM P&L / STATUS

DIRECTION: "BUY" in --color-bid, "SELL" in --color-offer. Text only — no arrows.
Double-click a row: opens TradeDetail side panel.
Filter bar above table: Status dropdown (ALL/CONFIRMED/PENDING/CANCELLED), Days dropdown (7/30/90).
Hook: useTradeBlotter, staleTime: 5000.

**TradeDetail** (side panel, 320px, slides from right):
Shows all trade fields. If status = CONFIRMED: shows CANCEL button that calls PATCH /api/v1/trades/{id}/cancel.

---

## PAGE: /trader/positions — PositionBook.tsx (standalone)
Full-page position book with more detail than the blotter panel version.
Adds: position history chart (how net position changed over last 30 days), attribution by counterparty.

## PAGE: /trader/orders — OrderManagement.tsx
DataTable of open orders. Columns: INSTRUMENT / DIRECTION / TYPE / VOLUME / LIMIT PRICE / FILLED / STATUS / CREATED.
DELETE button per row calls DELETE /api/v1/orders/{id}.
ORDER ENTRY form (compact, above table) to place new limit/market orders.

---

## SPIKE ALERT SYSTEM

**SpikeAlertBar** (conditionally shown above Price Strip when spike detected)
When any NEM region RRP > $1,000:
- Full-width bar appears in --color-offer background (dark red, subtle)
- Text: "PRICE ALERT — SA1 $4,284/MWh — Review dispatch positions" in --font-data --text-sm
- DISMISS button (X)
- Persists until dismissed or price normalises

---

## HOOKS: app/frontend/src/api/hooks/trading.ts
- useTradeBlotter(traderId?, status?, days?): staleTime: 5000
- usePositionBook(traderId?, regionId?): refetchInterval: 10000
- usePnLSummary(traderId?, days?): staleTime: 30000
- useOpenOrders(traderId?): refetchInterval: 15000
- submitTrade(entry): POST mutation, returns Trade
- cancelTrade(tradeId): PATCH mutation
- placeOrder(entry): POST mutation
- cancelOrder(orderId): DELETE mutation

---

## SUCCESS CRITERIA
1. TradeEntryForm submits and creates a trade in Lakebase (verify POST response and GET blotter)
2. Position book updates within 10s of trade submit
3. MTM P&L shows correctly: BUY at $80, market at $100 shows positive P&L
4. MTM P&L shows correctly: BUY at $100, market at $80 shows negative P&L
5. Cancel trade updates status in blotter
6. Price flash animation visible when market data refreshes
7. Spike alert bar appears when any region > $1000 in test data
8. BUY button --color-bid, SELL button --color-offer when selected
9. P&L estimate updates in real-time as price field is typed
10. All numbers monospace (verify computed styles)
11. Vitest tests pass

---

## COMPLETION ARTIFACT
completions/W14-trading-blotter.md
Commit message: "feat: W14 complete — Power Trader blotter and position book"

---
---

# W15 — Risk Dashboard
## APEX ETRM Platform
### Cursor Agent Instructions

---

## PREREQUISITE CHECK
Verify completions/W12-frontend-shell.md AND completions/W10-risk-api.md exist.

---

## OBJECTIVE
Build the Risk Manager workspace. A live risk monitoring dashboard where the risk manager can view portfolio VaR, run stress tests against NEM historical scenarios, monitor credit exposure, and track trading limit utilisation. All calculations trigger real Lakebase writes.

---

## PAGE: /risk/var — VaRDashboard.tsx

### VaR Header Metrics Row
Four Metric components (from W01):
- PORTFOLIO VAR 95%: in --font-data --text-2xl. "A$[value]" — pnl-negative colour (VaR is always a potential loss)
- PORTFOLIO VAR 99%: same
- POSITION VALUE: total mark-to-market value of all positions
- VAR UTILISATION: VaR_99 / var_limit_aud as percentage — StatusBadge (active < 70%, warning 70-90%, critical > 90%)

### VaR Runner Panel
A Panel titled "RUN VAR CALCULATION".
Description: "Monte Carlo simulation — 10,000 paths, 1-day horizon, historical volatility"
Inputs:
- SCOPE selector: FULL PORTFOLIO / BY DESK / BY REGION (radio group)
- TRADER filter: dropdown (All Traders / Sarah Chen / James Wu / etc.)
- SIMULATIONS: read-only display "10,000" (not user-editable in demo)
RUN VAR button (prominent — --color-accent background, white text).
On click: calls POST /api/v1/risk/var/calculate with spinner.
On return: updates all metrics and the histogram below.
Estimated time label: "Estimated: < 2 seconds"

### P&L Distribution Histogram
Recharts BarChart showing the simulated P&L distribution from the VaR calculation.
- 100 bars representing P&L buckets from worst to best
- Bars left of VaR_95: --color-offer (tail risk)
- Bars between VaR_95 and VaR_99: --color-warning
- Bars right of 0: --color-bid dim
- Two vertical reference lines: VaR_95 and VaR_99 in their respective colours with labels
- X-axis: P&L in $AUD --font-data --text-xs
- Y-axis: frequency count

### VaR History Chart
Recharts LineChart showing VaR_99 trend over last 30 days.
Single line in --color-persona-risk (amber). Horizontal reference line at var_limit_aud.
If line crosses reference: area between line and reference fills with --color-offer-dim.

---

## PAGE: /risk/stress — StressTestPanel.tsx

### Scenario Selector
Cards for each of the 5 stress scenarios (from seed data). Each card:
- Scenario name in --text-md
- Description in --text-sm --color-text-secondary
- Price shock: "+400%" or "-80%" in appropriate colour (positive shock --color-offer, negative shock --color-bid)
- Region badge
- Reference event in --text-xs italic --color-text-tertiary
- RUN button per card

Clicking RUN: calls POST /api/v1/risk/stress-test with scenario_id. Shows loading spinner on that card. On return: updates the results section.

### Stress Test Results Panel
After running:
- Scenario name as panel title
- PORTFOLIO P&L IMPACT: large Metric in pnl-positive or pnl-negative depending on sign
- WORST CASE: Metric
- BEST CASE: Metric
- POSITIONS BREACHED: integer count with StatusBadge (active=0, warning=1-3, critical=>3)
- A bar chart showing P&L impact per trader/region (Recharts horizontal BarChart, bars in pnl colours)

### Historical Stress Test Table
DataTable of all past stress test runs.
Columns: RUN DATE / SCENARIO / P&L IMPACT / BREACHES / RUN BY

---

## PAGE: /risk/limits — LimitMonitor.tsx

### Limits Overview Table
DataTable showing all trading limits and their utilisation.
Columns: TRADER / LIMIT TYPE / LIMIT VALUE / CURRENT VALUE / UTILISATION % / STATUS

UTILISATION %: shown as percentage AND as a thin inline progress bar (100px wide CSS bar).
Bar fills: green < 70%, amber 70-90%, red > 90%.
STATUS: StatusBadge — active/warning/critical/breach.
Rows with is_breach=TRUE: background --color-offer-dim.

### Breach Alert Panel
If any breach exists: a full-width alert panel above the table.
Background --color-offer-dim, border --color-offer, text: "LIMIT BREACH DETECTED — [N] limits exceeded. Trader: [name]. Reviewed and acknowledged below."
ACKNOWLEDGE button per breach (simulated — clears the visual highlight but does not change backend data).

---

## PAGE: /risk/credit — CreditExposure.tsx

### Credit Exposure Table
DataTable showing counterparty credit exposure.
Columns: COUNTERPARTY / MTM (A$) / PFE (A$) / TOTAL EXPOSURE / CREDIT LIMIT / UTILISATION % / STATUS

MTM column: pnl-positive if positive (we are owed money), pnl-negative if negative.
TOTAL EXPOSURE: always pnl-negative (exposure is a risk).
Utilisation bar: same inline CSS bar as limits page.
is_breach rows: --color-offer-dim background.

---

## HOOKS: app/frontend/src/api/hooks/risk.ts
- useVaRLatest(traderId?): staleTime: 60000
- useVaRHistory(traderId?, days?): staleTime: 300000
- calculateVaR(request): POST mutation, invalidates useVaRLatest on success
- useStressScenarios: staleTime: 3600000 (rarely changes)
- runStressTest(request): POST mutation
- useStressHistory(traderId?, days?): staleTime: 60000
- useCreditExposure(counterpartyId?): refetchInterval: 120000
- useTradingLimits(traderId?): refetchInterval: 60000
- useLimitBreaches(traderId?): refetchInterval: 30000

---

## SUCCESS CRITERIA
1. RUN VAR button triggers calculation and updates metrics
2. VaR_99 > VaR_95 always displayed
3. P&L histogram renders with 100 bars and VaR reference lines
4. Running stress test updates results section with real data
5. Limit breach rows show --color-offer-dim background
6. Credit utilisation bars render at correct proportional width
7. VaR calculation completes visually in < 3s (spinner to result)
8. All $ amounts: Decimal precision, comma-formatted, no float
9. Vitest tests pass

---

## COMPLETION ARTIFACT
completions/W15-risk-dashboard.md
Commit message: "feat: W15 complete — Risk Manager dashboard with live VaR"
