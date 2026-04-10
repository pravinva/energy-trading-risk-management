"""
Professional Monte Carlo Simulation Engine
Using Industry-Standard Financial Libraries

Libraries used:
- stochastic: Stochastic process implementations (GBM, OU, Jump processes)
- empyrical: Risk metrics (VaR, CVaR, Sharpe, Sortino, etc.)
- numba: JIT compilation for performance
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd

# Professional financial libraries
try:
    from stochastic.processes.continuous import (
        GeometricBrownianMotion,
        OrnsteinUhlenbeckProcess,
        CoxIngersollRossProcess
    )
    STOCHASTIC_AVAILABLE = True
except ImportError:
    STOCHASTIC_AVAILABLE = False
    print("Warning: 'stochastic' library not installed. Install with: pip install stochastic")

try:
    import quantstats as qs
    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    print("Warning: 'quantstats' library not installed. Install with: pip install quantstats")

try:
    import numba
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("Warning: 'numba' library not installed. Install with: pip install numba")

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
    """Monte Carlo simulation results with professional risk metrics"""

    # VaR metrics (using empyrical)
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

    # Simulation details (required fields)
    n_simulations: int
    n_steps: int
    paths: List[SimulationPath]
    pnl_distribution: np.ndarray

    # Convergence (required fields)
    var_95_convergence: np.ndarray
    mean_convergence: np.ndarray

    # Professional risk metrics (optional, from empyrical)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    omega_ratio: Optional[float] = None
    tail_ratio: Optional[float] = None


class ProfessionalMonteCarloEngine:
    """
    Professional Monte Carlo engine using industry-standard libraries

    Uses:
    - stochastic.GeometricBrownianMotion for price simulation
    - empyrical for risk metrics
    - numba for performance optimization
    """

    def __init__(
        self,
        spot_price: float,
        volatility: float,
        drift: float = 0.0,
        dt: float = 1.0 / 252,  # Daily steps
        random_seed: Optional[int] = None,
        process_type: str = 'gbm'  # 'gbm', 'ou', 'cir'
    ):
        """
        Initialize Monte Carlo engine with professional libraries

        Args:
            spot_price: Current spot price
            volatility: Annual volatility
            drift: Annual drift (expected return)
            dt: Time step (default: 1 day = 1/252 years)
            random_seed: Random seed for reproducibility
            process_type: 'gbm' (Geometric Brownian Motion),
                         'ou' (Ornstein-Uhlenbeck),
                         'cir' (Cox-Ingersoll-Ross)
        """
        self.spot_price = spot_price
        self.volatility = volatility
        self.drift = drift
        self.dt = dt
        self.process_type = process_type

        if random_seed is not None:
            np.random.seed(random_seed)

        # Initialize stochastic process
        if STOCHASTIC_AVAILABLE:
            if process_type == 'gbm':
                # Geometric Brownian Motion (default for prices)
                self.process = GeometricBrownianMotion(
                    drift=drift,
                    volatility=volatility,
                    t=1.0  # 1 year
                )
            elif process_type == 'ou':
                # Ornstein-Uhlenbeck (mean-reverting)
                self.process = OrnsteinUhlenbeckProcess(
                    speed=2.0,  # Mean reversion speed
                    mean=spot_price,  # Long-term mean
                    vol=volatility
                )
            elif process_type == 'cir':
                # Cox-Ingersoll-Ross (interest rates/volatility)
                self.process = CoxIngersollRossProcess(
                    speed=2.0,
                    mean=spot_price,
                    vol=volatility
                )
            else:
                raise ValueError(f"Unknown process type: {process_type}")
        else:
            self.process = None

    def simulate_price_paths(
        self,
        n_simulations: int = 10_000,
        n_steps: int = 252,  # 1 year daily
        exposure_mw: float = 100.0,
        save_paths: bool = False,
        risk_free_rate: float = 0.03
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation using professional libraries

        Args:
            n_simulations: Number of simulation paths
            n_steps: Number of time steps per path
            exposure_mw: Portfolio exposure in MW
            save_paths: Save individual paths (memory intensive)
            risk_free_rate: Risk-free rate for Sharpe ratio

        Returns:
            MonteCarloResult with professional risk metrics
        """
        if STOCHASTIC_AVAILABLE and self.process:
            # Use stochastic library for professional implementation
            price_paths = self._simulate_with_stochastic(n_simulations, n_steps)
        else:
            # Fallback to numpy GBM
            price_paths = self._simulate_with_numpy(n_simulations, n_steps)

        # Calculate P&L for each path
        final_prices = price_paths[:, -1]
        pnl_distribution = (final_prices - self.spot_price) * exposure_mw

        # Calculate returns for empyrical
        returns_matrix = np.diff(price_paths, axis=1) / price_paths[:, :-1]

        # Calculate professional risk metrics (empyrical or manual)
        risk_metrics = self._calculate_risk_metrics(
            returns_matrix,
            pnl_distribution,
            risk_free_rate
        )

        # VaR and CVaR using empyrical or fallback
        var_95, var_99, cvar_95, cvar_99 = self._calculate_var_cvar(
            pnl_distribution
        )

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
        var_95_convergence = self._calculate_convergence(pnl_distribution, 5)
        mean_convergence = self._calculate_mean_convergence(pnl_distribution)

        # Save individual paths if requested
        paths = []
        if save_paths:
            paths = self._extract_paths(
                price_paths,
                pnl_distribution,
                var_95,
                n_paths=min(100, n_simulations)
            )

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
            sharpe_ratio=risk_metrics.get('sharpe_ratio'),
            sortino_ratio=risk_metrics.get('sortino_ratio'),
            calmar_ratio=risk_metrics.get('calmar_ratio'),
            omega_ratio=risk_metrics.get('omega_ratio'),
            tail_ratio=risk_metrics.get('tail_ratio'),
            n_simulations=n_simulations,
            n_steps=n_steps,
            paths=paths,
            pnl_distribution=pnl_distribution,
            var_95_convergence=var_95_convergence,
            mean_convergence=mean_convergence
        )

    def _simulate_with_stochastic(
        self,
        n_simulations: int,
        n_steps: int
    ) -> np.ndarray:
        """
        Simulate using stochastic library (professional implementation)
        """
        times = np.linspace(0, 1, n_steps + 1)

        # Generate multiple paths
        price_paths = np.zeros((n_simulations, n_steps + 1))

        for i in range(n_simulations):
            if self.process_type == 'gbm':
                # GBM returns relative changes, need to scale to price
                path = self.process.sample(n_steps)
                price_paths[i] = self.spot_price * np.exp(path)
            else:
                # OU and CIR return absolute values
                path = self.process.sample(n_steps)
                price_paths[i] = path

        return price_paths

    def _simulate_with_numpy(
        self,
        n_simulations: int,
        n_steps: int
    ) -> np.ndarray:
        """
        Fallback: Simulate using numpy GBM
        """
        price_paths = np.zeros((n_simulations, n_steps + 1))
        price_paths[:, 0] = self.spot_price

        z = np.random.standard_normal((n_simulations, n_steps))

        drift_term = (self.drift - 0.5 * self.volatility ** 2) * self.dt
        diffusion_term = self.volatility * np.sqrt(self.dt)

        for t in range(n_steps):
            price_paths[:, t + 1] = price_paths[:, t] * np.exp(
                drift_term + diffusion_term * z[:, t]
            )

        return price_paths

    def _calculate_risk_metrics(
        self,
        returns_matrix: np.ndarray,
        pnl_distribution: np.ndarray,
        risk_free_rate: float
    ) -> Dict[str, float]:
        """
        Calculate professional risk metrics using quantstats library
        """
        if not QUANTSTATS_AVAILABLE:
            raise ImportError(
                "quantstats library required for professional risk metrics. "
                "Install with: pip install quantstats"
            )

        metrics = {}

        # Use portfolio returns (average across simulations)
        avg_returns = np.mean(returns_matrix, axis=0)

        # Create datetime index for quantstats (required)
        dates = pd.date_range(start='2024-01-01', periods=len(avg_returns), freq='D')
        returns_series = pd.Series(avg_returns, index=dates)

        # Calculate professional metrics using quantstats
        try:
            # Sharpe ratio (annualized)
            metrics['sharpe_ratio'] = float(qs.stats.sharpe(
                returns_series,
                rf=risk_free_rate,
                periods=252
            ))

            # Sortino ratio (annualized)
            metrics['sortino_ratio'] = float(qs.stats.sortino(
                returns_series,
                rf=risk_free_rate,
                periods=252
            ))

            # Calmar ratio (return / max drawdown)
            metrics['calmar_ratio'] = float(qs.stats.calmar(returns_series))

            # Omega ratio (probability weighted ratio of gains vs losses)
            # Note: quantstats doesn't have omega_ratio, use gain/loss ratio
            metrics['omega_ratio'] = float(qs.stats.gain_to_pain_ratio(returns_series))

            # Tail ratio (95th / 5th percentile)
            p95 = returns_series.quantile(0.95)
            p5 = returns_series.quantile(0.05)
            metrics['tail_ratio'] = float(p95 / abs(p5)) if p5 != 0 else 0.0

        except Exception as e:
            raise RuntimeError(f"Error calculating professional risk metrics: {e}")

        return metrics

    def _calculate_var_cvar(
        self,
        pnl_distribution: np.ndarray
    ) -> Tuple[float, float, float, float]:
        """
        Calculate VaR and CVaR using quantstats library
        """
        if not QUANTSTATS_AVAILABLE:
            raise ImportError(
                "quantstats library required for VaR/CVaR calculation. "
                "Install with: pip install quantstats"
            )

        try:
            pnl_series = pd.Series(pnl_distribution)

            # VaR using quantstats (Value at Risk)
            var_95 = -float(qs.stats.value_at_risk(pnl_series, confidence=0.95))
            var_99 = -float(qs.stats.value_at_risk(pnl_series, confidence=0.99))

            # CVaR using quantstats (Conditional Value at Risk / Expected Shortfall)
            cvar_95 = -float(qs.stats.cvar(pnl_series, confidence=0.95))
            cvar_99 = -float(qs.stats.cvar(pnl_series, confidence=0.99))

            return var_95, var_99, cvar_95, cvar_99

        except Exception as e:
            raise RuntimeError(f"Error calculating VaR/CVaR: {e}")

    def _calculate_convergence(
        self,
        pnl_distribution: np.ndarray,
        percentile: float
    ) -> np.ndarray:
        """Calculate VaR convergence"""
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

    def _extract_paths(
        self,
        price_paths: np.ndarray,
        pnl_distribution: np.ndarray,
        var_95: float,
        n_paths: int = 100
    ) -> List[SimulationPath]:
        """Extract individual simulation paths"""
        paths = []

        for i in range(min(n_paths, len(price_paths))):
            returns = np.diff(price_paths[i]) / price_paths[i, :-1]

            # Calculate max drawdown using quantstats
            if not QUANTSTATS_AVAILABLE:
                raise ImportError("quantstats library required for max drawdown calculation")

            try:
                # Create datetime index for quantstats
                dates = pd.date_range(start='2024-01-01', periods=len(returns), freq='D')
                returns_series = pd.Series(returns, index=dates)
                max_dd = float(qs.stats.max_drawdown(returns_series))
            except Exception as e:
                raise RuntimeError(f"Error calculating max drawdown: {e}")

            paths.append(SimulationPath(
                path_id=i,
                prices=price_paths[i],
                returns=returns,
                final_pnl=pnl_distribution[i],
                max_drawdown=max_dd,
                var_breach=pnl_distribution[i] < -var_95
            ))

        return paths


# Example usage with professional libraries
def main():
    """Example using professional Monte Carlo engine"""

    print("=" * 80)
    print("Professional Monte Carlo Simulation")
    print("Using: stochastic + quantstats + numba")
    print("=" * 80)
    print()

    # Check library availability
    print("Library Status:")
    print(f"  stochastic: {'✅ Available' if STOCHASTIC_AVAILABLE else '❌ Not installed'}")
    print(f"  quantstats: {'✅ Available' if QUANTSTATS_AVAILABLE else '❌ Not installed'}")
    print(f"  numba: {'✅ Available' if NUMBA_AVAILABLE else '❌ Not installed'}")
    print()

    # Setup
    spot_price = 96.0
    volatility = 0.35
    drift = 0.02
    exposure_mw = 500.0

    print(f"Parameters:")
    print(f"  Spot Price: ${spot_price}/MWh")
    print(f"  Volatility: {volatility*100:.1f}%")
    print(f"  Drift: {drift*100:.1f}%")
    print(f"  Exposure: {exposure_mw} MW")
    print(f"  Process: Geometric Brownian Motion")
    print()

    # Create engine with professional libraries
    engine = ProfessionalMonteCarloEngine(
        spot_price=spot_price,
        volatility=volatility,
        drift=drift,
        process_type='gbm',  # Can also try 'ou' or 'cir'
        random_seed=42
    )

    print("Running 10,000 simulations...")
    print()

    result = engine.simulate_price_paths(
        n_simulations=10_000,
        n_steps=252,
        exposure_mw=exposure_mw,
        save_paths=True,
        risk_free_rate=0.03
    )

    # Display results
    print("=" * 80)
    print("RESULTS (Using Professional Libraries)")
    print("=" * 80)
    print()

    print("Value at Risk (empyrical library):")
    print(f"  VaR 95%: ${result.var_95:,.2f}")
    print(f"  VaR 99%: ${result.var_99:,.2f}")
    print()

    print("Conditional VaR (Expected Shortfall):")
    print(f"  CVaR 95%: ${result.cvar_95:,.2f}")
    print(f"  CVaR 99%: ${result.cvar_99:,.2f}")
    print()

    print("P&L Distribution:")
    print(f"  Mean: ${result.mean_pnl:,.2f}")
    print(f"  Median: ${result.median_pnl:,.2f}")
    print(f"  Std Dev: ${result.std_pnl:,.2f}")
    print()

    print("Professional Risk Metrics (empyrical):")
    if result.sharpe_ratio is not None:
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"  Sortino Ratio: {result.sortino_ratio:.3f}")
        print(f"  Calmar Ratio: {result.calmar_ratio:.3f}")
        print(f"  Omega Ratio: {result.omega_ratio:.3f}")
        print(f"  Tail Ratio: {result.tail_ratio:.3f}")
    else:
        print("  (Install empyrical for professional risk metrics)")
    print()

    print(f"Simulation paths saved: {len(result.paths)}")
    print()

    print("=" * 80)


if __name__ == '__main__':
    main()
