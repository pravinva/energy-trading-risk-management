"""
Strategy & Agents API Routes
Endpoints for strategy management, backtesting, and agent collaboration
"""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

# Strategy imports
from app.backend.strategies.base_strategy import StrategyParameters
from app.backend.strategies.weather_driven import WeatherDrivenStrategy, MaintenanceAwareStrategy
from app.backend.strategies.mean_reversion import MeanReversionStrategy
from app.backend.strategies.arbitrage import ArbitrageStrategy, TemporalArbitrageStrategy
from app.backend.strategies.backtesting import BacktestEngine
from app.backend.strategies.executor import StrategyExecutor
from app.backend.strategies.mlflow_integration import get_mlflow_tracker

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])

# ============================================================================
# Pydantic Models
# ============================================================================

class StrategyInfo(BaseModel):
    strategy_id: str
    strategy_name: str
    strategy_type: str
    description: str
    region_id: str
    status: str
    created_at: str


class BacktestRequest(BaseModel):
    strategy_type: str  # 'WEATHER_DRIVEN', 'MEAN_REVERSION', 'ARBITRAGE', 'MAINTENANCE_AWARE'
    region_id: str = 'NSW1'
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    initial_capital: float = 1_000_000.0
    parameters: Optional[Dict[str, Any]] = None


class BacktestResult(BaseModel):
    backtest_id: str
    strategy_name: str
    total_trades: int
    win_rate: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    total_pnl: float


class AgentInfo(BaseModel):
    agent_id: str
    agent_type: str
    agent_name: str
    description: str
    status: str


class SignalInfo(BaseModel):
    signal_id: str
    strategy_id: str
    timestamp: str
    signal_type: str
    action: str
    instrument: str
    volume_mw: float
    confidence: float
    reasoning: str
    executed: bool


class PositionInfo(BaseModel):
    position_id: str
    strategy_id: str
    instrument: str
    entry_price: float
    volume_mw: float
    unrealized_pnl: float
    status: str


class AgentMessage(BaseModel):
    message_id: str
    from_agent_id: str
    to_agent_id: str
    message_type: str
    timestamp: str
    content: str
    status: str


# ============================================================================
# Strategy Management Endpoints
# ============================================================================

@router.get("/list", response_model=APIResponse[List[StrategyInfo]])
async def list_strategies(
    status: Optional[str] = Query(default=None),
) -> APIResponse[List[StrategyInfo]]:
    """
    List all strategies

    Args:
        status: Optional filter by status (BACKTEST, PAPER, LIVE, PAUSED, RETIRED)

    Returns:
        List of strategies
    """
    catalog = get_settings().apex_catalog

    status_filter = f"WHERE status = '{status}'" if status else ""

    sql = f"""
    SELECT
        strategy_id,
        strategy_name,
        strategy_type,
        description,
        region_id,
        status,
        CAST(created_at AS STRING) AS created_at
    FROM {catalog}.strategy.strategies
    {status_filter}
    ORDER BY created_at DESC
    """

    rows = await execute_sql(sql)
    strategies = [StrategyInfo.model_validate(r) for r in rows]

    return APIResponse(data=strategies)


@router.post("/create/{strategy_type}")
async def create_strategy(
    strategy_type: str,
    parameters: StrategyParameters,
) -> APIResponse[StrategyInfo]:
    """
    Create a new strategy

    Args:
        strategy_type: Strategy type
        parameters: Strategy parameters

    Returns:
        Created strategy info
    """
    # Create strategy instance
    strategy = _create_strategy_instance(strategy_type, parameters)

    # Save to database
    await strategy.save_to_database()

    return APIResponse(data=StrategyInfo(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.strategy_name,
        strategy_type=strategy.strategy_type,
        description=strategy.description,
        region_id=strategy.parameters.region_id,
        status='BACKTEST',
        created_at=datetime.now().isoformat(),
    ))


# ============================================================================
# Backtesting Endpoints
# ============================================================================

@router.post("/backtest", response_model=APIResponse[BacktestResult])
async def run_backtest(
    request: BacktestRequest,
) -> APIResponse[BacktestResult]:
    """
    Run strategy backtest

    Args:
        request: Backtest configuration

    Returns:
        Backtest results
    """
    # Parse dates
    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)

    # Create strategy
    params = StrategyParameters(region_id=request.region_id)
    if request.parameters:
        params = StrategyParameters(**request.parameters)

    strategy = _create_strategy_instance(request.strategy_type, params)

    # Run backtest
    backtest_engine = BacktestEngine(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=request.initial_capital,
    )

    metrics = await backtest_engine.run()

    # Log to MLflow
    mlflow_tracker = get_mlflow_tracker()
    mlflow_run_id = mlflow_tracker.log_backtest(strategy, metrics)

    result = BacktestResult(
        backtest_id=mlflow_run_id or 'unknown',
        strategy_name=strategy.strategy_name,
        total_trades=metrics.total_trades,
        win_rate=metrics.win_rate,
        total_return_pct=metrics.total_return_pct,
        sharpe_ratio=metrics.sharpe_ratio,
        max_drawdown_pct=metrics.max_drawdown_pct,
        total_pnl=metrics.total_pnl,
    )

    return APIResponse(data=result)


@router.get("/backtest/results", response_model=APIResponse[List[BacktestResult]])
async def get_backtest_results(
    strategy_type: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> APIResponse[List[BacktestResult]]:
    """
    Get backtest results

    Args:
        strategy_type: Optional filter by strategy type
        limit: Number of results

    Returns:
        List of backtest results
    """
    catalog = get_settings().apex_catalog

    type_filter = f"WHERE strategy_name LIKE '%{strategy_type}%'" if strategy_type else ""

    sql = f"""
    SELECT
        backtest_id,
        strategy_name,
        CAST(total_trades AS INT) AS total_trades,
        CAST(win_rate AS DOUBLE) AS win_rate,
        CAST(total_return_pct AS DOUBLE) AS total_return_pct,
        CAST(sharpe_ratio AS DOUBLE) AS sharpe_ratio,
        CAST(max_drawdown_pct AS DOUBLE) AS max_drawdown_pct,
        CAST(total_pnl AS DOUBLE) AS total_pnl
    FROM {catalog}.strategy.backtest_runs
    {type_filter}
    ORDER BY run_timestamp DESC
    LIMIT {limit}
    """

    rows = await execute_sql(sql)
    results = [BacktestResult.model_validate(r) for r in rows]

    return APIResponse(data=results)


# ============================================================================
# Live Strategy Endpoints
# ============================================================================

@router.get("/signals", response_model=APIResponse[List[SignalInfo]])
async def get_strategy_signals(
    strategy_id: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
) -> APIResponse[List[SignalInfo]]:
    """
    Get recent strategy signals

    Args:
        strategy_id: Optional filter by strategy
        hours: Hours of history

    Returns:
        List of signals
    """
    catalog = get_settings().apex_catalog

    strategy_filter = f"AND strategy_id = '{strategy_id}'" if strategy_id else ""

    sql = f"""
    SELECT
        signal_id,
        strategy_id,
        CAST(timestamp AS STRING) AS timestamp,
        signal_type,
        action,
        instrument,
        CAST(volume_mw AS DOUBLE) AS volume_mw,
        CAST(confidence AS DOUBLE) AS confidence,
        reasoning,
        executed
    FROM {catalog}.strategy.live_signals
    WHERE timestamp >= current_timestamp() - INTERVAL {hours} HOURS
      {strategy_filter}
    ORDER BY timestamp DESC
    LIMIT 100
    """

    rows = await execute_sql(sql)
    signals = [SignalInfo.model_validate(r) for r in rows]

    return APIResponse(data=signals)


@router.get("/positions", response_model=APIResponse[List[PositionInfo]])
async def get_positions(
    strategy_id: Optional[str] = Query(default=None),
) -> APIResponse[List[PositionInfo]]:
    """
    Get open positions

    Args:
        strategy_id: Optional filter by strategy

    Returns:
        List of positions
    """
    catalog = get_settings().apex_catalog

    strategy_filter = f"WHERE strategy_id = '{strategy_id}'" if strategy_id else ""

    sql = f"""
    SELECT
        position_id,
        strategy_id,
        instrument,
        CAST(entry_price AS DOUBLE) AS entry_price,
        CAST(volume_mw AS DOUBLE) AS volume_mw,
        CAST(unrealized_pnl AS DOUBLE) AS unrealized_pnl,
        status
    FROM {catalog}.strategy.positions
    {strategy_filter}
      AND status = 'OPEN'
    ORDER BY entry_timestamp DESC
    """

    rows = await execute_sql(sql)
    positions = [PositionInfo.model_validate(r) for r in rows]

    return APIResponse(data=positions)


# ============================================================================
# Agent Endpoints
# ============================================================================

@router.get("/agents", response_model=APIResponse[List[AgentInfo]])
async def list_agents() -> APIResponse[List[AgentInfo]]:
    """
    List all agents

    Returns:
        List of agents
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        agent_id,
        agent_type,
        agent_name,
        description,
        status
    FROM {catalog}.strategy.agents
    WHERE status = 'ACTIVE'
    ORDER BY agent_type, agent_name
    """

    try:
        rows = await execute_sql(sql)
        agents = [AgentInfo.model_validate(r) for r in rows]
    except Exception:
        # Table may not exist yet
        agents = []

    return APIResponse(data=agents)


@router.get("/agents/messages", response_model=APIResponse[List[AgentMessage]])
async def get_agent_messages(
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> APIResponse[List[AgentMessage]]:
    """
    Get agent collaboration messages

    Args:
        session_id: Optional filter by session
        limit: Number of messages

    Returns:
        List of messages
    """
    catalog = get_settings().apex_catalog

    session_filter = f"WHERE session_id = '{session_id}'" if session_id else ""

    sql = f"""
    SELECT
        message_id,
        from_agent_id,
        to_agent_id,
        message_type,
        CAST(timestamp AS STRING) AS timestamp,
        CAST(content AS STRING) AS content,
        status
    FROM {catalog}.strategy.agent_messages
    {session_filter}
    ORDER BY timestamp DESC
    LIMIT {limit}
    """

    try:
        rows = await execute_sql(sql)
        messages = [AgentMessage.model_validate(r) for r in rows]
    except Exception:
        messages = []

    return APIResponse(data=messages)


# ============================================================================
# Helper Functions
# ============================================================================

def _create_strategy_instance(
    strategy_type: str,
    parameters: StrategyParameters,
) -> Any:
    """Create strategy instance by type"""
    strategies = {
        'WEATHER_DRIVEN': WeatherDrivenStrategy,
        'MEAN_REVERSION': MeanReversionStrategy,
        'ARBITRAGE': ArbitrageStrategy,
        'TEMPORAL_ARBITRAGE': TemporalArbitrageStrategy,
        'MAINTENANCE_AWARE': MaintenanceAwareStrategy,
    }

    strategy_class = strategies.get(strategy_type.upper())
    if not strategy_class:
        raise HTTPException(
            status_code=400,
            detail=f'Unknown strategy type: {strategy_type}',
        )

    return strategy_class(parameters=parameters)
