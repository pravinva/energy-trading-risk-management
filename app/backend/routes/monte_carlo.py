"""
Monte Carlo Simulation API Routes

Provides endpoints for running and visualizing Monte Carlo simulations
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import numpy as np

from app.backend.engines.monte_carlo_professional import (
    ProfessionalMonteCarloEngine as MonteCarloEngine,
    MonteCarloResult,
    SimulationPath
)


router = APIRouter(prefix="/api/v1/monte-carlo", tags=["monte-carlo"])


# Request/Response Models
class SimulationRequest(BaseModel):
    """Monte Carlo simulation request"""

    spot_price: float = Field(..., gt=0, description="Current spot price ($/MWh)")
    volatility: float = Field(..., gt=0, le=2.0, description="Annual volatility (0.0-2.0)")
    drift: float = Field(default=0.0, ge=-0.5, le=0.5, description="Annual drift/expected return")
    exposure_mw: float = Field(..., description="Position exposure in MW")

    n_simulations: int = Field(default=10_000, ge=100, le=100_000, description="Number of simulation paths")
    n_steps: int = Field(default=252, ge=1, le=1000, description="Time steps per path (default 252 = 1 year daily)")

    save_paths: bool = Field(default=False, description="Save individual paths (memory intensive)")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class SimulationPathResponse(BaseModel):
    """Simulation path data"""

    path_id: int
    prices: List[float]
    returns: List[float]
    final_pnl: float
    max_drawdown: float
    var_breach: bool


class MonteCarloResultResponse(BaseModel):
    """Monte Carlo simulation results with professional risk metrics"""

    # VaR metrics
    var_95: float = Field(..., description="Value at Risk (95% confidence)")
    var_99: float = Field(..., description="Value at Risk (99% confidence)")
    cvar_95: float = Field(..., description="Conditional VaR (95%)")
    cvar_99: float = Field(..., description="Conditional VaR (99%)")

    # Distribution statistics
    mean_pnl: float
    median_pnl: float
    std_pnl: float
    skewness: float
    kurtosis: float

    # Percentiles
    percentile_1: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    percentile_99: float

    # Simulation details
    n_simulations: int
    n_steps: int
    pnl_distribution: List[float]

    # Convergence
    var_95_convergence: List[float]
    mean_convergence: List[float]

    # Professional risk metrics (from empyrical or manual calculation)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio (risk-adjusted return)")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio (downside risk)")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio (return / max drawdown)")
    omega_ratio: Optional[float] = Field(None, description="Omega ratio (gains / losses)")
    tail_ratio: Optional[float] = Field(None, description="Tail ratio (upside / downside tail)")

    # Paths (if requested)
    paths: List[SimulationPathResponse] = []

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now)
    spot_price: float
    volatility: float
    exposure_mw: float


# API Endpoints
@router.post("/simulate", response_model=MonteCarloResultResponse)
async def run_simulation(request: SimulationRequest):
    """
    Run Monte Carlo simulation for portfolio VaR calculation

    **Example:**
    ```json
    {
      "spot_price": 96.0,
      "volatility": 0.35,
      "drift": 0.02,
      "exposure_mw": 500.0,
      "n_simulations": 10000,
      "n_steps": 252,
      "save_paths": true
    }
    ```

    **Returns:**
    - VaR and CVaR at 95% and 99% confidence
    - P&L distribution statistics
    - Convergence analysis
    - Individual paths (if save_paths=true)
    """
    try:
        # Create Monte Carlo engine
        engine = MonteCarloEngine(
            spot_price=request.spot_price,
            volatility=request.volatility,
            drift=request.drift,
            random_seed=request.random_seed
        )

        # Run simulation
        result = engine.simulate_price_paths(
            n_simulations=request.n_simulations,
            n_steps=request.n_steps,
            exposure_mw=request.exposure_mw,
            save_paths=request.save_paths
        )

        # Convert paths to response format
        paths_response = []
        if request.save_paths and result.paths:
            paths_response = [
                SimulationPathResponse(
                    path_id=p.path_id,
                    prices=p.prices.tolist(),
                    returns=p.returns.tolist(),
                    final_pnl=p.final_pnl,
                    max_drawdown=p.max_drawdown,
                    var_breach=p.var_breach
                )
                for p in result.paths
            ]

        return MonteCarloResultResponse(
            var_95=result.var_95,
            var_99=result.var_99,
            cvar_95=result.cvar_95,
            cvar_99=result.cvar_99,
            mean_pnl=result.mean_pnl,
            median_pnl=result.median_pnl,
            std_pnl=result.std_pnl,
            skewness=result.skewness,
            kurtosis=result.kurtosis,
            percentile_1=result.percentile_1,
            percentile_5=result.percentile_5,
            percentile_25=result.percentile_25,
            percentile_75=result.percentile_75,
            percentile_95=result.percentile_95,
            percentile_99=result.percentile_99,
            n_simulations=result.n_simulations,
            n_steps=result.n_steps,
            pnl_distribution=result.pnl_distribution.tolist(),
            var_95_convergence=result.var_95_convergence.tolist(),
            mean_convergence=result.mean_convergence.tolist(),
            paths=paths_response,
            spot_price=request.spot_price,
            volatility=request.volatility,
            exposure_mw=request.exposure_mw
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quick-var", response_model=dict)
async def quick_var(
    spot_price: float = Query(..., gt=0, description="Spot price ($/MWh)"),
    volatility: float = Query(..., gt=0, le=2.0, description="Annual volatility"),
    exposure_mw: float = Query(..., description="Exposure in MW"),
    confidence: float = Query(default=0.95, ge=0.9, le=0.99, description="Confidence level")
):
    """
    Quick VaR calculation with default parameters

    **Faster than full simulation - uses 1,000 paths**

    Example: `/api/v1/monte-carlo/quick-var?spot_price=96&volatility=0.35&exposure_mw=500&confidence=0.95`
    """
    try:
        engine = MonteCarloEngine(
            spot_price=spot_price,
            volatility=volatility,
            drift=0.0,
            random_seed=42
        )

        result = engine.simulate_price_paths(
            n_simulations=1_000,  # Faster for quick estimates
            n_steps=252,
            exposure_mw=exposure_mw,
            save_paths=False
        )

        if confidence == 0.95:
            var = result.var_95
            cvar = result.cvar_95
        elif confidence == 0.99:
            var = result.var_99
            cvar = result.cvar_99
        else:
            # Custom confidence level
            percentile_idx = int((1 - confidence) * result.n_simulations)
            sorted_pnl = np.sort(result.pnl_distribution)
            var = -float(sorted_pnl[percentile_idx])
            cvar = -float(np.mean(sorted_pnl[:percentile_idx]))

        return {
            "var": round(var, 2),
            "cvar": round(cvar, 2),
            "confidence": confidence,
            "spot_price": spot_price,
            "volatility": volatility,
            "exposure_mw": exposure_mw,
            "n_simulations": 1_000
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scenario-analysis", response_model=List[dict])
async def scenario_analysis(
    spot_price: float = Query(..., gt=0),
    exposure_mw: float = Query(...),
    base_volatility: float = Query(default=0.25, gt=0, le=2.0)
):
    """
    Run multiple scenarios with varying volatility

    **Returns VaR across volatility spectrum**

    Example: Stress test by increasing volatility from 10% to 50%
    """
    try:
        scenarios = []

        # Test volatilities: 10%, 15%, 20%, 25%, 30%, 35%, 40%, 50%
        test_vols = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]

        for vol in test_vols:
            engine = MonteCarloEngine(
                spot_price=spot_price,
                volatility=vol,
                drift=0.0,
                random_seed=42
            )

            result = engine.simulate_price_paths(
                n_simulations=5_000,
                n_steps=252,
                exposure_mw=exposure_mw,
                save_paths=False
            )

            scenarios.append({
                "volatility": vol,
                "volatility_pct": vol * 100,
                "var_95": round(result.var_95, 2),
                "var_99": round(result.var_99, 2),
                "cvar_95": round(result.cvar_95, 2),
                "mean_pnl": round(result.mean_pnl, 2),
                "std_pnl": round(result.std_pnl, 2)
            })

        return scenarios

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stress-test", response_model=dict)
async def stress_test(
    spot_price: float = Query(..., gt=0),
    exposure_mw: float = Query(...),
    volatility: float = Query(default=0.25),
    shock_pct: float = Query(default=50.0, ge=0, le=200, description="Volatility shock %")
):
    """
    Stress test: Compare base case vs shocked volatility

    **Example:** shock_pct=50 means 50% increase in volatility
    """
    try:
        # Base case
        engine_base = MonteCarloEngine(
            spot_price=spot_price,
            volatility=volatility,
            drift=0.0,
            random_seed=42
        )

        result_base = engine_base.simulate_price_paths(
            n_simulations=10_000,
            n_steps=252,
            exposure_mw=exposure_mw,
            save_paths=False
        )

        # Shocked case
        shocked_vol = volatility * (1 + shock_pct / 100)
        engine_shocked = MonteCarloEngine(
            spot_price=spot_price,
            volatility=shocked_vol,
            drift=0.0,
            random_seed=42
        )

        result_shocked = engine_shocked.simulate_price_paths(
            n_simulations=10_000,
            n_steps=252,
            exposure_mw=exposure_mw,
            save_paths=False
        )

        return {
            "base_case": {
                "volatility": volatility,
                "var_95": round(result_base.var_95, 2),
                "var_99": round(result_base.var_99, 2),
                "cvar_95": round(result_base.cvar_95, 2)
            },
            "shocked_case": {
                "volatility": shocked_vol,
                "var_95": round(result_shocked.var_95, 2),
                "var_99": round(result_shocked.var_99, 2),
                "cvar_95": round(result_shocked.cvar_95, 2)
            },
            "impact": {
                "var_95_increase": round(result_shocked.var_95 - result_base.var_95, 2),
                "var_95_increase_pct": round(
                    ((result_shocked.var_95 - result_base.var_95) / result_base.var_95) * 100, 2
                ),
                "cvar_95_increase": round(result_shocked.cvar_95 - result_base.cvar_95, 2)
            },
            "shock_applied_pct": shock_pct
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
