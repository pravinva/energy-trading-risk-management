# APEX ERCOT - Day in the Life by Persona

## Purpose

This guide outlines how each core persona uses APEX through a full ERCOT day:
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

Supplemental Americas screens:
- `/americas/market`
- `/americas/bess`
- `/americas/etrm`

---

## 06:00-09:00 System Start and Volatility Read

### Dispatch Operator
- Opens `/workspace/dispatch` with market set to `ERCOT`.
- Validates available ERCOT assets/service types and prior stack state.
- Reviews 12-interval strip and recommendation confidence baseline.

### Power Trader
- Opens `/workspace/trading`.
- Focuses on `ERCOT_*` instruments and quote responsiveness.
- Checks blotter and exposure to identify early imbalance.

### Risk Manager
- Opens `/workspace/risk`.
- Captures opening VaR and limit utilization.
- Sets stress baseline with current spot sensitivity.

### Quant Developer
- Opens `/workspace/quant`.
- Confirms ERCOT lineage and forecast coverage are present.
- Reviews strategy availability for ERCOT convergence/arbitrage themes.

### Portfolio Manager
- Opens `/workspace/portfolio`.
- Reviews annualized revenue stack and contract intensity assumptions.

---

## 09:00-14:00 Intraday Execution Window

### Dispatch Operator
- Adjusts bid bands to reflect changing scarcity and expected spread.
- Uses recommendation engine to guide dispatch targeting.
- Validates weighted stack economics and volume caps.

### Power Trader
- Monitors trade flow and MTM rapidly as prices move.
- Uses quarter heatmap to avoid concentrated directional exposure.

### Risk Manager
- Refreshes VaR after significant order flow changes.
- Runs stress scenarios to evaluate tail expansion impact.

### Quant Developer
- Tracks divergence between expected and observed strip movement.
- Records anomalies tied to volatility spikes and market regime shift.

### Portfolio Manager
- Tests ancillary participation and PPA MW sensitivity in simulation.
- Aligns optimization recommendations with observed intraday behavior.

### Americas Regional Screens (context augmentation)
- `/americas/market`: compares ERCOT with other ISO pricing context.
- `/americas/bess`: evaluates RTC+B telemetry and spread behavior.
- `/americas/etrm`: reviews PJM/IESO context and normalization evidence.

---

## 14:00-18:00 Risk and Position Governance

### Dispatch Operator
- Consolidates stack updates and confirms approved action path.

### Power Trader
- Tightens carry exposure into close.
- Verifies execution completeness and residual risk posture.

### Risk Manager
- Performs structured pre-close checks:
  - VaR refresh
  - limit monitor review
  - stress rerun at updated spot

### Quant Developer
- Tags model behavior windows for retraining and drift analysis.

### Portfolio Manager
- Reconciles current allocation against benchmark and PPA MTM impact.

---

## 18:00-21:00 End-of-Day Close

### Dispatch Operator
- Confirms last accepted recommendation and final stack state.

### Power Trader
- Finalizes blotter and carry notes for overnight desk.

### Risk Manager
- Publishes end-of-day risk posture and unresolved exceptions.

### Quant Developer
- Compiles model and data quality observations for next cycle.

### Portfolio Manager
- Publishes next-day optimization recommendations by component.

---

## Operating Notes for ERCOT

- Core market data dependency: `apex_fresh.market_ercot.lmp`.
- Core trading dependency: `apex_fresh.trading.trades` (market = `ERCOT`).
- Dispatch dependencies:
  - `apex_fresh.trading.dispatch_reference`
  - `apex_fresh.trading.offer_bands`
- Forecast/lineage dependencies:
  - `apex_fresh.analytics.price_forecasts`
  - `apex_fresh.analytics.model_lineage`
