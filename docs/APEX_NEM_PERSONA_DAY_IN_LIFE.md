# APEX NEM - Day in the Life by Persona

## Purpose

This guide shows how each core persona uses APEX through a full trading day in the NEM market:
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

---

## 06:00-08:00 Market Open Preparation

### Dispatch Operator
- Opens `/workspace/dispatch`.
- Reviews **Fleet Monitor** and validates available NEM assets/service types.
- Confirms **Pre-Dispatch Strip** for next 12 intervals and checks model metadata/lineage health.
- Reviews latest offer stack from prior shift and resets scenarios for the day.

### Power Trader
- Opens `/workspace/trading`.
- Reviews **Market Snapshot** and quote spread for selected NEM instrument.
- Checks **Position Book** for overnight net MW and early imbalance.
- Uses **Net Exposure** heatmap to identify quarter-hour concentration.

### Risk Manager
- Opens `/workspace/risk`.
- Confirms opening **spot price**, baseline **VaR 95/99**, and **limit utilization**.
- Verifies no overnight breaches in Gross MW and Intraday Drawdown.

### Quant Developer
- Opens `/workspace/quant`.
- Confirms freshest model run in **Model Lineage** and expected feature hash.
- Validates predispatch availability for first 24-hour horizon.

### Portfolio Manager
- Opens `/workspace/portfolio`.
- Reviews starting **Total Annual Revenue** and component mix.
- Verifies simulation defaults for NEM (duration, FCAS %, PPA MW).

---

## 09:00-12:00 Active Trading and Dispatch

### Dispatch Operator
- Refines bid bands in **Offer Stack Builder** based on forecast strip steepness.
- Uses **ML Recommendations** to compare charge vs discharge intent.
- Accepts recommendation if confidence and target MW align with desk constraints.
- Audits changes in **Stack History** for operator handoff traceability.

### Power Trader
- Watches **Trade Blotter** for fills and MTM drift.
- Uses instrument selector to rotate NSW/VIC/QLD books.
- Tracks quote changes and confirms spread tightness before adding trades.

### Risk Manager
- Triggers VaR refresh after major directional changes.
- Uses stress cards to test downside and peak-price scenarios.
- Escalates if drawdown utilization trend approaches limit threshold.

### Quant Developer
- Compares expected vs implied move from strip behavior.
- Cross-checks strategy availability for NEM and current model confidence context.

### Portfolio Manager
- Simulates higher FCAS participation vs baseline.
- Tests sensitivity to duration-hours for arbitrage uplift.
- Evaluates resulting contribution percentages before recommending positioning.

---

## 13:00-17:00 Re-Optimization and Governance

### Dispatch Operator
- Re-optimizes stacks as volatility shifts.
- Confirms weighted offer price remains aligned with target capture.

### Power Trader
- Rebalances inventory to reduce quarter concentration.
- Uses blotter and exposure to flatten adverse buckets.

### Risk Manager
- Performs midday formal risk check:
  - VaR refresh
  - limit status review
  - stress rerun at current spot
- Shares risk posture summary to trading/dispatch.

### Quant Developer
- Flags drift risk if realized behavior materially diverges from model profile.
- Prepares retraining recommendation inputs for next model cycle.

### Portfolio Manager
- Reviews PPA MTM impact and active contract concentration.
- Uses **Asset Benchmarking** to identify underperforming counterparties/assets.

---

## 17:00-20:00 End-of-Day Wrap

### Dispatch Operator
- Publishes final stack state and rationale.
- Ensures latest accepted recommendation is recorded.

### Power Trader
- Confirms end-of-day blotter completeness and net position carry.
- Highlights unusual MTM swings for risk and quant follow-up.

### Risk Manager
- Final VaR snapshot and breach status report.
- Confirms no unresolved credit/limit anomalies before handoff.

### Quant Developer
- Captures notable model exceptions and feature anomalies.
- Feeds observations into next training/monitoring cycle.

### Portfolio Manager
- Compares simulated plan vs realized intraday trajectory.
- Prepares next-day allocation suggestions.

---

## Operating Notes for NEM

- Key market data dependency: `apex_fresh.market_nem.prices`.
- Core transactional dependency: `apex_fresh.trading.trades`.
- Portfolio simulation dependencies:
  - `apex_fresh.portfolio.revenue_rates`
  - `apex_fresh.portfolio.simulation_defaults`
- Forecast/lineage dependencies:
  - `apex_fresh.analytics.price_forecasts`
  - `apex_fresh.analytics.model_lineage`
