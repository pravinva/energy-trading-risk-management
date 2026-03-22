"""
Portfolio Optimization API Routes

Provides endpoints for:
- Portfolio optimization (max Sharpe, min variance, risk parity)
- Efficient frontier generation
- Black-Litterman optimization with views
- Rebalancing recommendations
"""
from typing import Dict, List, Literal, Optional
from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from app.backend.portfolio import PortfolioOptimizer, OptimizationConstraints, PortfolioMetrics


router = APIRouter(prefix="/api/v1/optimization", tags=["portfolio-optimization"])


# Request/Response models
class OptimizationRequest(BaseModel):
    """Portfolio optimization request"""

    strategies: List[str] = Field(..., description="List of strategy IDs to include")
    objective: Literal['max_sharpe', 'min_variance', 'max_return', 'risk_parity'] = Field(
        default='max_sharpe',
        description="Optimization objective"
    )

    # Constraints
    min_weight: float = Field(default=0.0, ge=-1.0, le=1.0, description="Minimum weight per asset")
    max_weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Maximum weight per asset")
    max_volatility: Optional[float] = Field(default=None, description="Maximum portfolio volatility")
    max_var_95: Optional[float] = Field(default=None, description="Maximum VaR at 95% confidence")
    max_turnover: Optional[float] = Field(default=None, description="Maximum turnover vs current")

    # Parameters
    risk_free_rate: float = Field(default=0.03, description="Risk-free rate for Sharpe ratio")
    lookback_days: int = Field(default=252, description="Days of historical returns to use")
    target_return: Optional[float] = Field(default=None, description="Target return (for min_variance)")

    # Current portfolio (for rebalancing)
    current_weights: Optional[Dict[str, float]] = Field(default=None, description="Current weights")


class BlackLittermanRequest(BaseModel):
    """Black-Litterman optimization with market views"""

    strategies: List[str] = Field(..., description="List of strategy IDs")
    views: Dict[str, float] = Field(..., description="Market views {strategy_id: expected_return}")
    view_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in views")

    # Constraints
    min_weight: float = Field(default=0.0, ge=-1.0, le=1.0)
    max_weight: float = Field(default=1.0, ge=0.0, le=1.0)

    # Parameters
    risk_free_rate: float = Field(default=0.03)
    lookback_days: int = Field(default=252)


class EfficientFrontierRequest(BaseModel):
    """Efficient frontier generation request"""

    strategies: List[str] = Field(..., description="List of strategy IDs")
    n_points: int = Field(default=50, ge=10, le=200, description="Number of frontier points")

    # Constraints
    min_weight: float = Field(default=0.0)
    max_weight: float = Field(default=1.0)

    # Parameters
    risk_free_rate: float = Field(default=0.03)
    lookback_days: int = Field(default=252)


class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics response"""

    expected_return: float = Field(..., description="Annualized expected return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    var_95: float = Field(..., description="Value at Risk (95% confidence)")
    cvar_95: float = Field(..., description="Conditional VaR (Expected Shortfall)")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    weights: Dict[str, float] = Field(..., description="Optimal weights")


class EfficientFrontierResponse(BaseModel):
    """Efficient frontier response"""

    portfolios: List[PortfolioMetricsResponse]
    max_sharpe_idx: int = Field(..., description="Index of max Sharpe portfolio")
    min_vol_idx: int = Field(..., description="Index of min volatility portfolio")


# API Endpoints
@router.post("/optimize", response_model=PortfolioMetricsResponse)
async def optimize_portfolio(request: OptimizationRequest):
    """
    Optimize portfolio allocation across strategies

    Returns optimal weights based on selected objective and constraints.

    **Example:**
    ```json
    {
      "strategies": ["momentum_nsw1", "mean_reversion_qld1", "ml_forecast_nsw1"],
      "objective": "max_sharpe",
      "min_weight": 0.0,
      "max_weight": 0.5,
      "risk_free_rate": 0.03
    }
    ```
    """
    try:
        # Fetch strategy returns from database
        returns = await _fetch_strategy_returns(
            request.strategies,
            request.lookback_days
        )

        # Create optimizer
        optimizer = PortfolioOptimizer(
            returns=returns,
            risk_free_rate=request.risk_free_rate
        )

        # Build constraints
        constraints = OptimizationConstraints(
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            max_volatility=request.max_volatility,
            max_var_95=request.max_var_95,
            max_turnover=request.max_turnover
        )

        # Optimize
        result = optimizer.optimize(
            objective=request.objective,
            constraints=constraints,
            target_return=request.target_return,
            current_weights=request.current_weights
        )

        return PortfolioMetricsResponse(
            expected_return=result.expected_return * 252,  # Annualize
            volatility=result.volatility * np.sqrt(252),  # Annualize
            sharpe_ratio=result.sharpe_ratio,
            var_95=result.var_95,
            cvar_95=result.cvar_95,
            max_drawdown=result.max_drawdown,
            weights=result.weights
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/black-litterman", response_model=PortfolioMetricsResponse)
async def black_litterman_optimization(request: BlackLittermanRequest):
    """
    Black-Litterman portfolio optimization with market views

    Incorporates trader/analyst views about expected returns using Bayesian approach.

    **Example:**
    ```json
    {
      "strategies": ["momentum_nsw1", "ml_forecast_nsw1"],
      "views": {
        "momentum_nsw1": 0.15,
        "ml_forecast_nsw1": 0.12
      },
      "view_confidence": 0.7
    }
    ```
    """
    try:
        # Fetch strategy returns
        returns = await _fetch_strategy_returns(
            request.strategies,
            request.lookback_days
        )

        # Create optimizer
        optimizer = PortfolioOptimizer(
            returns=returns,
            risk_free_rate=request.risk_free_rate
        )

        # Build constraints
        constraints = OptimizationConstraints(
            min_weight=request.min_weight,
            max_weight=request.max_weight
        )

        # Convert annual views to daily
        daily_views = {
            strategy: annual_return / 252
            for strategy, annual_return in request.views.items()
        }

        # Optimize with views
        result = optimizer.black_litterman(
            views=daily_views,
            view_confidence=request.view_confidence,
            constraints=constraints
        )

        return PortfolioMetricsResponse(
            expected_return=result.expected_return * 252,
            volatility=result.volatility * np.sqrt(252),
            sharpe_ratio=result.sharpe_ratio,
            var_95=result.var_95,
            cvar_95=result.cvar_95,
            max_drawdown=result.max_drawdown,
            weights=result.weights
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/efficient-frontier", response_model=EfficientFrontierResponse)
async def generate_efficient_frontier(request: EfficientFrontierRequest):
    """
    Generate efficient frontier - optimal portfolios for different risk levels

    Returns a series of portfolios from minimum variance to maximum return.

    **Use Case:** Visualize risk-return tradeoffs across different allocations.
    """
    try:
        # Fetch strategy returns
        returns = await _fetch_strategy_returns(
            request.strategies,
            request.lookback_days
        )

        # Create optimizer
        optimizer = PortfolioOptimizer(
            returns=returns,
            risk_free_rate=request.risk_free_rate
        )

        # Build constraints
        constraints = OptimizationConstraints(
            min_weight=request.min_weight,
            max_weight=request.max_weight
        )

        # Generate frontier
        frontier = optimizer.efficient_frontier(
            n_points=request.n_points,
            constraints=constraints
        )

        # Convert to response format
        portfolios = [
            PortfolioMetricsResponse(
                expected_return=p.expected_return * 252,
                volatility=p.volatility * np.sqrt(252),
                sharpe_ratio=p.sharpe_ratio,
                var_95=p.var_95,
                cvar_95=p.cvar_95,
                max_drawdown=p.max_drawdown,
                weights=p.weights
            )
            for p in frontier
        ]

        # Find max Sharpe and min vol portfolios
        sharpes = [p.sharpe_ratio for p in portfolios]
        vols = [p.volatility for p in portfolios]

        max_sharpe_idx = int(np.argmax(sharpes))
        min_vol_idx = int(np.argmin(vols))

        return EfficientFrontierResponse(
            portfolios=portfolios,
            max_sharpe_idx=max_sharpe_idx,
            min_vol_idx=min_vol_idx
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/strategies", response_model=List[str])
async def list_available_strategies():
    """
    List all available strategies for portfolio optimization

    Strategies must have sufficient historical return data.
    """
    try:
        # Query available strategies from database
        # For now, return mock data
        return [
            "momentum_nsw1_v1",
            "mean_reversion_qld1_v2",
            "spread_trading_vic1_sa1_v1",
            "ml_forecast_nsw1_v3",
            "arbitrage_dam_rtm_v1",
            "momentum_sa1_v1",
            "stat_arb_multi_region_v2"
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _fetch_strategy_returns(
    strategy_ids: List[str],
    lookback_days: int
) -> pd.DataFrame:
    """
    Fetch historical returns for strategies

    In production, this would query the database for strategy P&L.
    For now, we generate synthetic data.
    """
    # TODO: Replace with actual database query
    # Example query:
    # SELECT date, strategy_id, daily_return
    # FROM strategy_performance
    # WHERE strategy_id IN (...)
    # AND date >= DATE_SUB(CURRENT_DATE, INTERVAL ? DAY)
    # ORDER BY date, strategy_id

    # For now, generate synthetic returns
    np.random.seed(42)
    dates = pd.date_range(
        end=datetime.now().date(),
        periods=lookback_days,
        freq='D'
    )

    # Simulate returns with different characteristics
    returns_data = {}
    for strategy_id in strategy_ids:
        # Use hash of strategy_id for reproducible randomness
        seed = hash(strategy_id) % 10000
        np.random.seed(seed)

        # Random return parameters
        mu = np.random.uniform(0.0005, 0.0015)  # Mean return
        sigma = np.random.uniform(0.01, 0.03)  # Volatility

        returns_data[strategy_id] = np.random.normal(mu, sigma, lookback_days)

    return pd.DataFrame(returns_data, index=dates)
