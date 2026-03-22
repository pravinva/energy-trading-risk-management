/**
 * Data Dictionary - Comprehensive mapping of all metrics to their definitions,
 * data sources, and calculations
 */

export interface MetricInfo {
  title: string;
  description: string;
  table?: string;
  calculation?: string;
  unit?: string;
}

export const DATA_DICTIONARY: Record<string, MetricInfo> = {
  // Risk Metrics
  'var_95': {
    title: 'Value at Risk 95%',
    description: 'Maximum expected loss over a 1-day period at 95% confidence level using Monte Carlo simulation with 10,000 paths',
    table: 'apex_fresh.trading.trades (exposure) + apex_fresh.market_*.prices (volatility)',
    calculation: '95th percentile of simulated P&L distribution',
    unit: 'USD/AUD/EUR',
  },
  'var_99': {
    title: 'Value at Risk 99%',
    description: 'Maximum expected loss over a 1-day period at 99% confidence level using Monte Carlo simulation with 10,000 paths',
    table: 'apex_fresh.trading.trades (exposure) + apex_fresh.market_*.prices (volatility)',
    calculation: '99th percentile of simulated P&L distribution',
    unit: 'USD/AUD/EUR',
  },
  'expected_shortfall': {
    title: 'Expected Shortfall (CVaR)',
    description: 'Average loss in the worst 5% of scenarios, providing a measure of tail risk beyond VaR',
    table: 'apex_fresh.trading.trades + apex_fresh.market_*.prices',
    calculation: 'Mean of losses exceeding VaR 95%',
    unit: 'USD/AUD/EUR',
  },
  'exposure_mw': {
    title: 'Net Exposure (MW)',
    description: 'Total net position across all traded instruments, representing market risk',
    table: 'apex_fresh.trading.trades',
    calculation: 'SUM(CASE WHEN direction=BUY THEN volume_mw ELSE -volume_mw END)',
    unit: 'MW',
  },
  'position_value': {
    title: 'Position Value',
    description: 'Total value of current positions at current market prices',
    table: 'apex_fresh.trading.trades + apex_fresh.market_*.prices',
    calculation: 'ABS(session_pnl) + (exposure_mw * spot_price)',
    unit: 'USD/AUD/EUR',
  },

  // Trading Metrics
  'trade_id': {
    title: 'Trade ID',
    description: 'Unique identifier for each trade execution',
    table: 'apex_fresh.trading.trades',
    unit: 'text',
  },
  'market': {
    title: 'Market',
    description: 'Trading market/exchange (NEM=Australia, EPEX=Europe, ERCOT=Texas)',
    table: 'apex_fresh.trading.trades',
    unit: 'enum',
  },
  'instrument_id': {
    title: 'Instrument ID',
    description: 'Specific product or contract being traded (e.g., NSW_PEAK_Q2)',
    table: 'apex_fresh.trading.trades',
    unit: 'text',
  },
  'trader_id': {
    title: 'Trader ID',
    description: 'User who executed the trade',
    table: 'apex_fresh.trading.trades',
    unit: 'text',
  },
  'direction': {
    title: 'Direction',
    description: 'Trade side: BUY (long position) or SELL (short position)',
    table: 'apex_fresh.trading.trades',
    unit: 'enum',
  },
  'volume_mw': {
    title: 'Volume (MW)',
    description: 'Quantity of energy traded in megawatts',
    table: 'apex_fresh.trading.trades',
    unit: 'MW',
  },
  'price': {
    title: 'Trade Price',
    description: 'Execution price per MWh in local currency',
    table: 'apex_fresh.trading.trades',
    unit: 'USD/AUD/EUR per MWh',
  },

  // Dispatch Metrics
  'asset_id': {
    title: 'Asset ID',
    description: 'Unique identifier for BESS (Battery Energy Storage System) asset',
    table: 'apex_fresh.trading.dispatch_reference',
    unit: 'text',
  },
  'capacity_mw': {
    title: 'Capacity (MW)',
    description: 'Maximum power output/input capacity of the battery',
    table: 'apex_fresh.trading.dispatch_reference',
    unit: 'MW',
  },
  'capacity_mwh': {
    title: 'Capacity (MWh)',
    description: 'Total energy storage capacity of the battery',
    table: 'apex_fresh.trading.dispatch_reference',
    unit: 'MWh',
  },
  'service_type': {
    title: 'Service Type',
    description: 'Market service provided (FCAS_CONTINGENCY=frequency control, ENERGY_ARBITRAGE=price arbitrage)',
    table: 'apex_fresh.trading.dispatch_reference',
    unit: 'enum',
  },
  'offer_band': {
    title: 'Offer Band',
    description: 'Price-volume tier in offer stack (Band 1=lowest price, Band 5=highest price)',
    table: 'apex_fresh.trading.offer_bands',
    unit: 'integer',
  },
  'band_price': {
    title: 'Band Price',
    description: 'Offer price for this volume tier',
    table: 'apex_fresh.trading.offer_bands',
    calculation: 'Set via bidding strategy optimization',
    unit: 'USD/AUD per MW',
  },
  'band_volume': {
    title: 'Band Volume',
    description: 'Available capacity at this price tier',
    table: 'apex_fresh.trading.offer_bands',
    unit: 'MW',
  },

  // Analytics Metrics
  'model_name': {
    title: 'Model Name',
    description: 'ML model identifier (ARIMA, LSTM, XGBoost, Prophet) with version',
    table: 'apex_fresh.analytics.model_performance',
    unit: 'text',
  },
  'mape': {
    title: 'MAPE (Mean Absolute Percentage Error)',
    description: 'Average percentage error of price forecasts - lower is better (5-15% is good)',
    table: 'apex_fresh.analytics.model_performance',
    calculation: 'MEAN(ABS((actual - predicted) / actual)) * 100',
    unit: 'percentage',
  },
  'rmse': {
    title: 'RMSE (Root Mean Square Error)',
    description: 'Root mean square of price forecast errors in currency units',
    table: 'apex_fresh.analytics.model_performance',
    calculation: 'SQRT(MEAN((actual - predicted)^2))',
    unit: 'USD/AUD/EUR',
  },
  'r2': {
    title: 'R² (Coefficient of Determination)',
    description: 'Model fit quality: 1.0=perfect, 0.0=no better than average (75-95% is good)',
    table: 'apex_fresh.analytics.model_performance',
    calculation: '1 - (SS_residual / SS_total)',
    unit: 'ratio',
  },
  'strategy': {
    title: 'Strategy',
    description: 'Trading strategy algorithm (Mean_Reversion, Momentum, Arbitrage, Statistical_Arb)',
    table: 'apex_fresh.analytics.backtest_runs',
    unit: 'text',
  },
  'trades': {
    title: 'Trades',
    description: 'Number of trades executed in backtest simulation',
    table: 'apex_fresh.analytics.backtest_runs',
    unit: 'count',
  },
  'win_rate': {
    title: 'Win Rate',
    description: 'Percentage of profitable trades (52-68% is typical for successful strategies)',
    table: 'apex_fresh.analytics.backtest_runs',
    calculation: 'profitable_trades / total_trades',
    unit: 'percentage',
  },
  'total_pnl': {
    title: 'Total P&L',
    description: 'Cumulative profit/loss from all backtest trades',
    table: 'apex_fresh.analytics.backtest_runs',
    calculation: 'SUM(trade_pnl)',
    unit: 'USD/AUD/EUR',
  },
  'sharpe': {
    title: 'Sharpe Ratio',
    description: 'Risk-adjusted return metric: >1.0 is good, >2.0 is excellent',
    table: 'apex_fresh.analytics.backtest_runs',
    calculation: '(mean_return - risk_free_rate) / stddev_return',
    unit: 'ratio',
  },

  // Market Price Metrics
  'spot_price': {
    title: 'Spot Price',
    description: 'Current real-time market price for energy',
    table: 'apex_fresh.market_nem.prices (rrp) / apex_fresh.market_epex.prices (price_eur_mwh) / apex_fresh.market_ercot.lmp (lmp)',
    unit: 'USD/AUD/EUR per MWh',
  },
  'forecast_price': {
    title: 'Forecast Price',
    description: 'ML model prediction of future spot price',
    table: 'apex_fresh.analytics.price_forecasts',
    calculation: 'Model output (LSTM_v3, ARIMA_v2, XGBoost_v1, Prophet_v2)',
    unit: 'USD/AUD/EUR per MWh',
  },
  'volatility': {
    title: 'Price Volatility',
    description: 'Standard deviation of price returns, representing market uncertainty',
    table: 'apex_fresh.market_*.prices',
    calculation: 'STDDEV(price_returns)',
    unit: 'percentage',
  },

  // Model Lineage
  'run_timestamp': {
    title: 'Run Timestamp',
    description: 'When the model was last executed/trained',
    table: 'apex_fresh.analytics.model_lineage',
    unit: 'datetime',
  },
  'training_start': {
    title: 'Training Start',
    description: 'Beginning of historical data used for model training',
    table: 'apex_fresh.analytics.model_lineage',
    unit: 'datetime',
  },
  'training_end': {
    title: 'Training End',
    description: 'End of historical data used for model training',
    table: 'apex_fresh.analytics.model_lineage',
    unit: 'datetime',
  },
  'feature_set': {
    title: 'Feature Set',
    description: 'Input variables used by the model (price, demand, weather, etc.)',
    table: 'apex_fresh.analytics.model_lineage',
    unit: 'text',
  },
  'feature_hash': {
    title: 'Feature Hash',
    description: 'SHA-256 hash of feature configuration for reproducibility tracking',
    table: 'apex_fresh.analytics.model_lineage',
    calculation: 'SHA256(feature_set)',
    unit: 'hex',
  },
};

export function getMetricInfo(key: string): MetricInfo | null {
  return DATA_DICTIONARY[key] || null;
}
