# APEX EPEX - Day in the Life by Persona

## Purpose

This guide shows how each core persona uses APEX across a full EPEX operating day:
- Dispatch Operator
- Power Trader
- Risk Manager
- Quant Developer
- Portfolio Manager

Primary workspace screens:
- `/workspace/dispatch`
- `/workspace/trading`
- `/workspace/risk`
- `/workspace/quant`
- `/workspace/portfolio`

Supplemental Europe screens:
- `/europe/market`
- `/europe/portfolio`
- `/europe/etrm`

---

## 05:00-08:00 Auction Context and Portfolio Setup

### Dispatch Operator
- Opens `/workspace/dispatch` with market set to `EPEX`.
- Confirms asset and reserve service mappings for EPEX battery assets.
- Reviews predispatch strip and latest model lineage marker.

### Power Trader
- Opens `/workspace/trading`.
- Rotates through EPEX instruments (for example `DE-LU_BASE`, `FR_BASE`).
- Uses **Trade Blotter** + **Position Book** to evaluate overnight carry.

### Risk Manager
- Opens `/workspace/risk`.
- Initializes VaR at current EPEX spot and verifies limits.
- Runs initial stress set to baseline downside risk envelope.

### Quant Developer
- Opens `/workspace/quant`.
- Confirms EPEX model lineage freshness and run timestamp.
- Validates strategy availability for EPEX in strategy catalog.

### Portfolio Manager
- Opens `/workspace/portfolio`.
- Reviews annual revenue composition and PPA sensitivity baseline.
- Confirms EPEX simulation defaults are loaded.

---

## 08:00-12:00 Intraday Positioning and Cross-Border Awareness

### Dispatch Operator
- Tunes offer bands to reflect expected intraday profile.
- Uses recommendation confidence to guide charge/discharge scheduling.

### Power Trader
- Tracks quoted instrument movement and MTM shifts.
- Uses exposure heatmap to reduce concentration risk by quarter bucket.

### Risk Manager
- Recomputes VaR after material trade additions.
- Uses stress scenarios for volatility expansion and max-price conditions.

### Quant Developer
- Correlates strip behavior with expected model output trajectory.
- Flags unusual residual behavior for post-session diagnostics.

### Portfolio Manager
- Runs simulation what-if cases:
  - higher reserve participation
  - adjusted contracted MW
  - extended duration assumptions
- Shares contribution deltas with trader/risk.

### Europe Regional Screens (context augmentation)
- `/europe/market`: checks current EPEX prices and cross-border utilization.
- `/europe/portfolio`: checks spark spread trend and legacy incumbent asset set.
- `/europe/etrm`: runs REMIT audit simulation for compliance traceability.

---

## 12:00-17:00 Governance and Optimization Loop

### Dispatch Operator
- Maintains offer stack traceability in stack history.
- Ensures final stack for each key asset is coherent with forecast conditions.

### Power Trader
- Rebalances positions ahead of close.
- Confirms blotter and quote-consistency for key delivery zones.

### Risk Manager
- Performs formal midday and pre-close risk control checks.
- Ensures utilization remains within approved thresholds.

### Quant Developer
- Captures model behavior notes for retraining and drift monitoring.

### Portfolio Manager
- Reviews benchmark rankings and PPA MTM changes.
- Prepares next-day portfolio recommendations.

---

## 17:00-20:00 Close and Hand-off

### Dispatch Operator
- Locks final stack configuration and logs rationale.

### Power Trader
- Confirms end-of-day net position and unresolved execution items.

### Risk Manager
- Publishes final VaR/limits snapshot for controls handoff.

### Quant Developer
- Documents model exceptions and data quality concerns.

### Portfolio Manager
- Publishes realized-vs-simulated commentary for next-day planning.

---

## Operating Notes for EPEX

- Core market data dependency: `apex_fresh.market_epex.prices`.
- Core trading dependency: `apex_fresh.trading.trades` (market = `EPEX`).
- Forecast/lineage dependencies:
  - `apex_fresh.analytics.price_forecasts`
  - `apex_fresh.analytics.model_lineage`
- Portfolio dependencies:
  - `apex_fresh.portfolio.revenue_rates`
  - `apex_fresh.portfolio.simulation_defaults`
