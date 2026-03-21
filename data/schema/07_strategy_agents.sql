-- Phase 2: Strategy Development with Agents Schema
-- Agent framework, trading strategies, backtesting, and multi-agent collaboration

USE CATALOG apex;

-- Strategy schema
CREATE SCHEMA IF NOT EXISTS strategy;

-- ============================================================================
-- AGENT DEFINITIONS
-- ============================================================================

-- Agent registry - defines available agents in the system
CREATE TABLE IF NOT EXISTS apex.strategy.agents (
  agent_id STRING,
  agent_type STRING, -- 'QUANT', 'RISK', 'EXECUTION', 'FORECAST'
  agent_name STRING,
  description STRING,
  model_provider STRING, -- 'DATABRICKS_FM_API'
  model_name STRING, -- 'claude-sonnet-4-5'
  model_config JSON, -- Temperature, max_tokens, etc.
  tools_enabled ARRAY<STRING>, -- Available tools for this agent
  system_prompt STRING, -- Agent's core instructions
  status STRING, -- 'ACTIVE', 'PAUSED', 'RETIRED'
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  created_by STRING
);

-- Agent memory - stores conversation history and context
CREATE TABLE IF NOT EXISTS apex.strategy.agent_memory (
  memory_id STRING,
  agent_id STRING,
  session_id STRING,
  timestamp TIMESTAMP,
  role STRING, -- 'USER', 'ASSISTANT', 'SYSTEM', 'TOOL'
  content STRING,
  metadata JSON -- Additional context, tool calls, etc.
);

-- Agent tools - defines tools available to agents
CREATE TABLE IF NOT EXISTS apex.strategy.agent_tools (
  tool_id STRING,
  tool_name STRING,
  tool_type STRING, -- 'FORECASTING', 'MARKET_DATA', 'RISK', 'EXECUTION'
  description STRING,
  input_schema JSON,
  python_function STRING, -- Function path or code
  enabled BOOLEAN,
  created_at TIMESTAMP
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS apex.strategy.agent_metrics (
  metric_id STRING,
  agent_id STRING,
  timestamp TIMESTAMP,
  total_invocations INT,
  avg_response_time_ms DOUBLE,
  success_rate DOUBLE,
  tokens_used INT,
  cost_usd DOUBLE,
  decisions_made INT,
  decisions_correct INT
);

-- ============================================================================
-- TRADING STRATEGIES
-- ============================================================================

-- Strategy definitions
CREATE TABLE IF NOT EXISTS apex.strategy.strategies (
  strategy_id STRING,
  strategy_name STRING,
  strategy_type STRING, -- 'WEATHER_DRIVEN', 'MEAN_REVERSION', 'ARBITRAGE', 'MAINTENANCE_AWARE'
  description STRING,
  agent_id STRING, -- Primary agent responsible for this strategy
  region_id STRING, -- NEM region (NSW1, VIC1, QLD1, SA1)
  parameters JSON, -- Strategy-specific parameters
  risk_limits JSON, -- Max position, VaR limits, etc.
  status STRING, -- 'BACKTEST', 'PAPER', 'LIVE', 'PAUSED', 'RETIRED'
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  created_by STRING
);

-- Strategy execution log - records all strategy decisions
CREATE TABLE IF NOT EXISTS apex.strategy.execution_log (
  execution_id STRING,
  strategy_id STRING,
  agent_id STRING,
  timestamp TIMESTAMP,
  market_conditions JSON, -- Snapshot of market at decision time
  action STRING, -- 'BUY', 'SELL', 'HOLD', 'CLOSE'
  instrument STRING,
  volume_mw DOUBLE,
  price DOUBLE,
  reasoning STRING, -- Agent's explanation for the decision
  confidence DOUBLE, -- 0.0 to 1.0
  tool_calls ARRAY<STRING>, -- Tools used to make decision
  execution_status STRING, -- 'PROPOSED', 'APPROVED', 'EXECUTED', 'REJECTED', 'FAILED'
  pnl DOUBLE, -- Profit/loss from this trade (if executed)
  metadata JSON
);

-- Strategy positions - current open positions per strategy
CREATE TABLE IF NOT EXISTS apex.strategy.positions (
  position_id STRING,
  strategy_id STRING,
  instrument STRING,
  region_id STRING,
  entry_timestamp TIMESTAMP,
  entry_price DOUBLE,
  volume_mw DOUBLE,
  current_price DOUBLE,
  unrealized_pnl DOUBLE,
  stop_loss DOUBLE,
  take_profit DOUBLE,
  status STRING, -- 'OPEN', 'CLOSED'
  closed_timestamp TIMESTAMP,
  closed_price DOUBLE,
  realized_pnl DOUBLE
);

-- Strategy performance summary
CREATE TABLE IF NOT EXISTS apex.strategy.performance_summary (
  summary_id STRING,
  strategy_id STRING,
  period_start TIMESTAMP,
  period_end TIMESTAMP,
  total_trades INT,
  winning_trades INT,
  losing_trades INT,
  win_rate DOUBLE,
  total_pnl DOUBLE,
  sharpe_ratio DOUBLE,
  max_drawdown DOUBLE,
  avg_trade_pnl DOUBLE,
  best_trade DOUBLE,
  worst_trade DOUBLE,
  total_volume_mwh DOUBLE,
  avg_holding_period_hours DOUBLE,
  created_at TIMESTAMP
);

-- ============================================================================
-- BACKTESTING
-- ============================================================================

-- Backtest runs
CREATE TABLE IF NOT EXISTS apex.strategy.backtest_runs (
  backtest_id STRING,
  strategy_id STRING,
  strategy_name STRING,
  start_date DATE,
  end_date DATE,
  initial_capital DOUBLE,
  final_capital DOUBLE,
  total_return_pct DOUBLE,
  total_trades INT,
  win_rate DOUBLE,
  sharpe_ratio DOUBLE,
  sortino_ratio DOUBLE,
  max_drawdown DOUBLE,
  max_drawdown_pct DOUBLE,
  calmar_ratio DOUBLE,
  avg_trade_pnl DOUBLE,
  best_trade DOUBLE,
  worst_trade DOUBLE,
  avg_holding_period_hours DOUBLE,
  total_volume_mwh DOUBLE,
  parameters JSON, -- Strategy parameters used
  market_conditions JSON, -- Summary of market during backtest
  run_timestamp TIMESTAMP,
  run_duration_seconds DOUBLE,
  mlflow_run_id STRING -- Link to MLflow experiment
);

-- Backtest trades - individual trades from backtests
CREATE TABLE IF NOT EXISTS apex.strategy.backtest_trades (
  trade_id STRING,
  backtest_id STRING,
  timestamp TIMESTAMP,
  action STRING, -- 'BUY', 'SELL'
  instrument STRING,
  volume_mw DOUBLE,
  price DOUBLE,
  reasoning STRING,
  confidence DOUBLE,
  pnl DOUBLE, -- Null if entry, value if exit
  cumulative_pnl DOUBLE,
  position_size_mw DOUBLE,
  portfolio_value DOUBLE
);

-- Backtest metrics timeseries
CREATE TABLE IF NOT EXISTS apex.strategy.backtest_metrics_ts (
  backtest_id STRING,
  timestamp TIMESTAMP,
  portfolio_value DOUBLE,
  cash DOUBLE,
  position_value DOUBLE,
  total_pnl DOUBLE,
  drawdown DOUBLE,
  drawdown_pct DOUBLE,
  sharpe_rolling_30d DOUBLE,
  open_positions INT
);

-- ============================================================================
-- MULTI-AGENT COLLABORATION
-- ============================================================================

-- Agent messages - communication between agents
CREATE TABLE IF NOT EXISTS apex.strategy.agent_messages (
  message_id STRING,
  from_agent_id STRING,
  to_agent_id STRING,
  session_id STRING, -- Groups related messages
  timestamp TIMESTAMP,
  message_type STRING, -- 'PROPOSAL', 'APPROVAL', 'VETO', 'QUERY', 'RESPONSE', 'ALERT'
  subject STRING,
  content JSON, -- Message body (could include trade proposal, analysis, etc.)
  priority STRING, -- 'LOW', 'MEDIUM', 'HIGH', 'URGENT'
  status STRING, -- 'SENT', 'READ', 'ACKNOWLEDGED', 'RESPONDED'
  parent_message_id STRING, -- For threading
  metadata JSON
);

-- Agent consensus - tracks multi-agent decision making
CREATE TABLE IF NOT EXISTS apex.strategy.agent_consensus (
  consensus_id STRING,
  session_id STRING,
  timestamp TIMESTAMP,
  decision_type STRING, -- 'TRADE', 'STRATEGY_ADJUST', 'RISK_ALERT'
  proposal JSON, -- Original proposal (e.g., trade details)
  participating_agents ARRAY<STRING>,
  votes JSON, -- Agent votes (APPROVE, REJECT, ABSTAIN)
  final_decision STRING, -- 'APPROVED', 'REJECTED', 'ESCALATED'
  reasoning ARRAY<STRING>, -- Each agent's reasoning
  confidence_score DOUBLE, -- Aggregated confidence
  executed BOOLEAN,
  execution_result JSON,
  created_at TIMESTAMP
);

-- Agent collaboration graph - tracks agent interactions
CREATE TABLE IF NOT EXISTS apex.strategy.agent_collaboration (
  interaction_id STRING,
  timestamp TIMESTAMP,
  agent_1_id STRING,
  agent_2_id STRING,
  interaction_type STRING, -- 'CONSULTED', 'COLLABORATED', 'DISAGREED', 'DEFERRED'
  context STRING, -- What they were working on
  outcome STRING,
  duration_ms DOUBLE
);

-- ============================================================================
-- STRATEGY RESEARCH & DEVELOPMENT
-- ============================================================================

-- Strategy ideas - generated by QuantAgent
CREATE TABLE IF NOT EXISTS apex.strategy.strategy_ideas (
  idea_id STRING,
  agent_id STRING,
  timestamp TIMESTAMP,
  strategy_type STRING,
  description STRING,
  hypothesis STRING,
  data_requirements ARRAY<STRING>,
  expected_sharpe DOUBLE,
  expected_win_rate DOUBLE,
  risk_assessment STRING,
  priority STRING, -- 'LOW', 'MEDIUM', 'HIGH'
  status STRING, -- 'PROPOSED', 'BACKTESTING', 'APPROVED', 'REJECTED', 'LIVE'
  backtest_results JSON,
  approval_agent_id STRING,
  approval_timestamp TIMESTAMP
);

-- Parameter optimization runs
CREATE TABLE IF NOT EXISTS apex.strategy.parameter_optimization (
  optimization_id STRING,
  strategy_id STRING,
  timestamp TIMESTAMP,
  parameter_name STRING,
  parameter_range JSON, -- Min, max, step
  best_value DOUBLE,
  best_sharpe DOUBLE,
  best_win_rate DOUBLE,
  optimization_results JSON, -- Full grid search results
  method STRING, -- 'GRID_SEARCH', 'RANDOM_SEARCH', 'BAYESIAN'
  iterations INT,
  duration_seconds DOUBLE
);

-- ============================================================================
-- REAL-TIME MONITORING
-- ============================================================================

-- Live strategy signals - real-time strategy signals
CREATE TABLE IF NOT EXISTS apex.strategy.live_signals (
  signal_id STRING,
  strategy_id STRING,
  timestamp TIMESTAMP,
  signal_type STRING, -- 'ENTRY', 'EXIT', 'REBALANCE', 'ALERT'
  instrument STRING,
  action STRING,
  volume_mw DOUBLE,
  price DOUBLE,
  confidence DOUBLE,
  reasoning STRING,
  forecasts_used JSON, -- Which forecasts influenced this
  market_snapshot JSON,
  execution_deadline TIMESTAMP,
  executed BOOLEAN,
  execution_timestamp TIMESTAMP
);

-- Risk alerts - real-time risk monitoring
CREATE TABLE IF NOT EXISTS apex.strategy.risk_alerts (
  alert_id STRING,
  strategy_id STRING,
  agent_id STRING,
  timestamp TIMESTAMP,
  alert_type STRING, -- 'VAR_BREACH', 'LOSS_LIMIT', 'CONCENTRATION', 'DRAWDOWN'
  severity STRING, -- 'INFO', 'WARNING', 'CRITICAL'
  description STRING,
  current_value DOUBLE,
  threshold_value DOUBLE,
  recommended_action STRING,
  acknowledged BOOLEAN,
  acknowledged_by STRING,
  acknowledged_at TIMESTAMP,
  resolved BOOLEAN,
  resolved_at TIMESTAMP
);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE apex.strategy.agents IS 'Agent registry with LLM configuration and tools';
COMMENT ON TABLE apex.strategy.strategies IS 'Trading strategy definitions with parameters and risk limits';
COMMENT ON TABLE apex.strategy.execution_log IS 'Complete log of all strategy decisions and executions';
COMMENT ON TABLE apex.strategy.backtest_runs IS 'Backtest run metadata and performance metrics';
COMMENT ON TABLE apex.strategy.agent_messages IS 'Multi-agent communication and collaboration';
COMMENT ON TABLE apex.strategy.agent_consensus IS 'Multi-agent consensus decision making';
COMMENT ON TABLE apex.strategy.live_signals IS 'Real-time strategy signals for live trading';
COMMENT ON TABLE apex.strategy.risk_alerts IS 'Real-time risk monitoring and alerts';
