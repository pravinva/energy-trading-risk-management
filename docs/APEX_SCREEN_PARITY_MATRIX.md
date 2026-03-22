# APEX Screen Parity Matrix

This matrix tracks current APEX workspace labeling against the original `apex-screens (2).html` vocabulary.

## Persona Header Parity

| Persona route | Target header | Current header | Status |
|---|---|---|---|
| `/workspace/dispatch` | Dispatch Operator | Dispatch Operator | Aligned |
| `/workspace/trading` | Power Trader | Power Trader | Aligned |
| `/workspace/risk` | Risk Manager | Risk Manager | Aligned |
| `/workspace/quant` | Quant Developer | Quant Developer | Aligned |
| `/workspace/portfolio` | Portfolio Manager | Portfolio Manager | Aligned |

## Panel Name Parity

| Persona | Target panel names (baseline) | Current panel names | Status |
|---|---|---|---|
| Dispatch | Fleet Monitor, Pre-Dispatch Strip, Offer Stack Builder, ML Recommendations, Stack History | Fleet Monitor, Pre-Dispatch Strip, Offer Stack Builder, ML Recommendations, Stack History | Aligned |
| Trading | Flow Summary, Market Snapshot, Position Book, Net Exposure, Trade Blotter | Flow Summary, Market Snapshot, Position Book, Net Exposure, Trade Blotter | Aligned |
| Risk | VaR Dashboard, Stress Scenarios, Limit Monitor, Credit Exposure, Stress Testing | VaR Dashboard, Stress Scenarios, Limit Monitor, Credit Exposure, Stress Testing | Aligned |
| Quant | Model Performance, Model Lineage, Strategy Backtest, Forecast vs Actual | Model Performance, Model Lineage, Strategy Backtest, Forecast vs Actual | Aligned |
| Portfolio | Revenue Stacking Simulator, PPA Book, Asset Benchmarking, Total Annual Revenue, PPA MTM | Revenue Stacking Simulator, PPA Book, Asset Benchmarking, Total Annual Revenue, PPA MTM | Aligned |

## Interaction Semantics Check

- Trading workspace: read-only analytics (no buy/sell or submit controls).
- Dispatch workspace: read-only analytics/insights (no submit/accept actions).
- Risk/Stress/Quant/Portfolio workspaces: analysis refresh controls only, no execution semantics.
