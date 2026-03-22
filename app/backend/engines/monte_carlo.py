"""
Advanced Monte Carlo Simulation Engine

Supports:
- VaR and CVaR calculation
- Price path simulation
- Portfolio simulation
- Correlation-aware simulations
- Convergence analysis
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class SimulationPath:
    """Single simulation path"""
    path_id: int
    prices: np.ndarray
    returns: np.ndarray
    final_pnl: float
    max_drawdown: float
    var_breach: bool


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation results"""

    # VaR metrics
    var_95: float
    var_99: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float

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
    paths: List[SimulationPath]
    pnl_distribution: np.ndarray

    # Convergence
    var_95_convergence: np.ndarray  # VaR convergence over simulations
    mean_convergence: np.ndarray


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for portfolio risk analysis

    Simulates thousands of price paths to calculate risk metrics
    """

    def __init__(
        self,
        spot_price: float,
        volatility: float,
        drift: float = 0.0,
        dt: float = 1.0 / 252,  # Daily steps
        random_seed: Optional[int] = None
    ):
        """
        Initialize Monte Carlo engine

        Args:
            spot_price: Current spot price
            volatility: Annual volatility
            drift: Annual drift (expected return)
            dt: Time step (default: 1 day = 1/252 years)
            random_seed: Random seed for reproducibility
        """
        self.spot_price = spot_price
        self.volatility = volatility
        self.drift = drift
        self.dt = dt

        if random_seed is not None:
            np.random.seed(random_seed)

    def simulate_price_paths(
        self,
        n_simulations: int = 10_000,
        n_steps: int = 252,  # 1 year daily
        exposure_mw: float = 100.0,
        save_paths: bool = False
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation using Geometric Brownian Motion

        Price follows: dS = μ S dt + σ S dW

        Args:
            n_simulations: Number of simulation paths
            n_steps: Number of time steps per path
            exposure_mw: Portfolio exposure in MW
            save_paths: Save individual paths (memory intensive)

        Returns:
            MonteCarloResult with VaR, CVaR, and distribution statistics
        """
        # Pre-allocate arrays for performance
        price_paths = np.zeros((n_simulations, n_steps + 1))
        price_paths[:, 0] = self.spot_price

        # Generate all random shocks at once (faster)
        z = np.random.standard_normal((n_simulations, n_steps))

        # Calculate price increments using Geometric Brownian Motion
        # S(t+dt) = S(t) * exp((μ - 0.5σ²)dt + σ√dt * Z)
        drift_term = (self.drift - 0.5 * self.volatility ** 2) * self.dt
        diffusion_term = self.volatility * np.sqrt(self.dt)

        for t in range(n_steps):
            price_paths[:, t + 1] = price_paths[:, t] * np.exp(
                drift_term + diffusion_term * z[:, t]
            )

        # Calculate P&L for each path
        final_prices = price_paths[:, -1]
        pnl_distribution = (final_prices - self.spot_price) * exposure_mw

        # Sort for percentile calculations
        sorted_pnl = np.sort(pnl_distribution)

        # Calculate VaR and CVaR
        var_95_idx = int(0.05 * n_simulations)
        var_99_idx = int(0.01 * n_simulations)

        var_95 = -sorted_pnl[var_95_idx]  # Negative because we want loss
        var_99 = -sorted_pnl[var_99_idx]

        # CVaR (Expected Shortfall) - average of losses beyond VaR
        cvar_95 = -np.mean(sorted_pnl[:var_95_idx]) if var_95_idx > 0 else 0.0
        cvar_99 = -np.mean(sorted_pnl[:var_99_idx]) if var_99_idx > 0 else 0.0

        # Distribution statistics
        mean_pnl = float(np.mean(pnl_distribution))
        median_pnl = float(np.median(pnl_distribution))
        std_pnl = float(np.std(pnl_distribution))
        skewness = float(stats.skew(pnl_distribution))
        kurtosis = float(stats.kurtosis(pnl_distribution))

        # Percentiles
        percentiles = np.percentile(
            pnl_distribution,
            [1, 5, 25, 75, 95, 99]
        )

        # Convergence analysis
        var_95_convergence = self._calculate_convergence(
            pnl_distribution,
            percentile=5
        )
        mean_convergence = self._calculate_mean_convergence(pnl_distribution)

        # Save individual paths if requested
        paths = []
        if save_paths:
            for i in range(min(n_simulations, 100)):  # Limit to 100 paths for memory
                returns = np.diff(price_paths[i]) / price_paths[i, :-1]
                max_dd = self._calculate_max_drawdown(price_paths[i])

                paths.append(SimulationPath(
                    path_id=i,
                    prices=price_paths[i],
                    returns=returns,
                    final_pnl=pnl_distribution[i],
                    max_drawdown=max_dd,
                    var_breach=pnl_distribution[i] < -var_95
                ))

        return MonteCarloResult(
            var_95=float(var_95),
            var_99=float(var_99),
            cvar_95=float(cvar_95),
            cvar_99=float(cvar_99),
            mean_pnl=mean_pnl,
            median_pnl=median_pnl,
            std_pnl=std_pnl,
            skewness=skewness,
            kurtosis=kurtosis,
            percentile_1=float(percentiles[0]),
            percentile_5=float(percentiles[1]),
            percentile_25=float(percentiles[2]),
            percentile_75=float(percentiles[3]),
            percentile_95=float(percentiles[4]),
            percentile_99=float(percentiles[5]),
            n_simulations=n_simulations,
            n_steps=n_steps,
            paths=paths,
            pnl_distribution=pnl_distribution,
            var_95_convergence=var_95_convergence,
            mean_convergence=mean_convergence
        )

    def simulate_portfolio_paths(
        self,
        positions: Dict[str, float],  # {instrument: exposure_mw}
        correlations: Optional[np.ndarray] = None,
        n_simulations: int = 10_000,
        n_steps: int = 252
    ) -> MonteCarloResult:
        """
        Simulate multi-asset portfolio with correlations

        Args:
            positions: Dictionary of {instrument: exposure_mw}
            correlations: Correlation matrix (if None, assumes independent)
            n_simulations: Number of paths
            n_steps: Steps per path

        Returns:
            Portfolio-level Monte Carlo results
        """
        n_assets = len(positions)
        instruments = list(positions.keys())
        exposures = np.array([positions[inst] for inst in instruments])

        # Generate correlated random shocks
        if correlations is None:
            # Independent assets
            z = np.random.standard_normal((n_simulations, n_steps, n_assets))
        else:
            # Correlated assets using Cholesky decomposition
            L = np.linalg.cholesky(correlations)
            z_independent = np.random.standard_normal((n_simulations, n_steps, n_assets))
            z = np.einsum('ij,klj->kli', L, z_independent)

        # Simulate each asset
        drift_term = (self.drift - 0.5 * self.volatility ** 2) * self.dt
        diffusion_term = self.volatility * np.sqrt(self.dt)

        portfolio_pnl = np.zeros(n_simulations)

        for asset_idx in range(n_assets):
            prices = np.ones((n_simulations, n_steps + 1)) * self.spot_price

            for t in range(n_steps):
                prices[:, t + 1] = prices[:, t] * np.exp(
                    drift_term + diffusion_term * z[:, t, asset_idx]
                )

            # P&L for this asset
            asset_pnl = (prices[:, -1] - self.spot_price) * exposures[asset_idx]
            portfolio_pnl += asset_pnl

        # Calculate metrics from portfolio P&L
        sorted_pnl = np.sort(portfolio_pnl)

        var_95_idx = int(0.05 * n_simulations)
        var_99_idx = int(0.01 * n_simulations)

        var_95 = -sorted_pnl[var_95_idx]
        var_99 = -sorted_pnl[var_99_idx]
        cvar_95 = -np.mean(sorted_pnl[:var_95_idx]) if var_95_idx > 0 else 0.0
        cvar_99 = -np.mean(sorted_pnl[:var_99_idx]) if var_99_idx > 0 else 0.0

        percentiles = np.percentile(portfolio_pnl, [1, 5, 25, 75, 95, 99])

        return MonteCarloResult(
            var_95=float(var_95),
            var_99=float(var_99),
            cvar_95=float(cvar_95),
            cvar_99=float(cvar_99),
            mean_pnl=float(np.mean(portfolio_pnl)),
            median_pnl=float(np.median(portfolio_pnl)),
            std_pnl=float(np.std(portfolio_pnl)),
            skewness=float(stats.skew(portfolio_pnl)),
            kurtosis=float(stats.kurtosis(portfolio_pnl)),
            percentile_1=float(percentiles[0]),
            percentile_5=float(percentiles[1]),
            percentile_25=float(percentiles[2]),
            percentile_75=float(percentiles[3]),
            percentile_95=float(percentiles[4]),
            percentile_99=float(percentiles[5]),
            n_simulations=n_simulations,
            n_steps=n_steps,
            paths=[],
            pnl_distribution=portfolio_pnl,
            var_95_convergence=self._calculate_convergence(portfolio_pnl, 5),
            mean_convergence=self._calculate_mean_convergence(portfolio_pnl)
        )

    def _calculate_convergence(
        self,
        pnl_distribution: np.ndarray,
        percentile: float
    ) -> np.ndarray:
        """
        Calculate VaR convergence as simulations increase

        Shows how VaR estimate stabilizes with more paths
        """
        n = len(pnl_distribution)
        convergence = np.zeros(n)

        for i in range(100, n, max(1, n // 100)):
            subset = pnl_distribution[:i]
            convergence[i] = -np.percentile(subset, percentile)

        return convergence[convergence > 0]

    def _calculate_mean_convergence(self, pnl_distribution: np.ndarray) -> np.ndarray:
        """Calculate mean convergence"""
        n = len(pnl_distribution)
        convergence = np.zeros(n)

        for i in range(100, n, max(1, n // 100)):
            convergence[i] = np.mean(pnl_distribution[:i])

        return convergence[convergence != 0]

    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown for a price path"""
        peak = np.maximum.accumulate(prices)
        drawdown = (prices - peak) / peak
        return float(np.min(drawdown))


# Example usage
def main():
    """Example Monte Carlo simulation"""

    print("=" * 80)
    print("Monte Carlo Simulation - Energy Trading Risk Analysis")
    print("=" * 80)
    print()

    # Setup
    spot_price = 96.0  # $/MWh
    volatility = 0.35  # 35% annual volatility (energy markets are volatile!)
    drift = 0.02       # 2% annual drift
    exposure_mw = 500.0  # 500 MW position

    print(f"Parameters:")
    print(f"  Spot Price: ${spot_price}/MWh")
    print(f"  Volatility: {volatility*100:.1f}%")
    print(f"  Drift: {drift*100:.1f}%")
    print(f"  Exposure: {exposure_mw} MW")
    print()

    # Run simulation
    engine = MonteCarloEngine(
        spot_price=spot_price,
        volatility=volatility,
        drift=drift,
        random_seed=42
    )

    print("Running 10,000 simulations over 252 days (1 year)...")
    print()

    result = engine.simulate_price_paths(
        n_simulations=10_000,
        n_steps=252,
        exposure_mw=exposure_mw,
        save_paths=True
    )

    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Value at Risk (VaR):")
    print(f"  VaR 95%: ${result.var_95:,.2f}")
    print(f"  VaR 99%: ${result.var_99:,.2f}")
    print()

    print("Conditional VaR (Expected Shortfall):")
    print(f"  CVaR 95%: ${result.cvar_95:,.2f}  (average loss beyond VaR 95%)")
    print(f"  CVaR 99%: ${result.cvar_99:,.2f}  (average loss beyond VaR 99%)")
    print()

    print("P&L Distribution:")
    print(f"  Mean: ${result.mean_pnl:,.2f}")
    print(f"  Median: ${result.median_pnl:,.2f}")
    print(f"  Std Dev: ${result.std_pnl:,.2f}")
    print(f"  Skewness: {result.skewness:.3f}")
    print(f"  Kurtosis: {result.kurtosis:.3f}")
    print()

    print("Percentiles:")
    print(f"  1%:  ${result.percentile_1:,.2f}")
    print(f"  5%:  ${result.percentile_5:,.2f}")
    print(f"  25%: ${result.percentile_25:,.2f}")
    print(f"  50%: ${result.median_pnl:,.2f}")
    print(f"  75%: ${result.percentile_75:,.2f}")
    print(f"  95%: ${result.percentile_95:,.2f}")
    print(f"  99%: ${result.percentile_99:,.2f}")
    print()

    print(f"Simulation paths saved: {len(result.paths)}")
    print(f"Convergence data points: {len(result.var_95_convergence)}")
    print()

    print("=" * 80)
    print("Simulation Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
