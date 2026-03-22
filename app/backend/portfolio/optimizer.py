"""
Portfolio Optimization Module

Implements various portfolio optimization techniques for energy trading:
- Mean-Variance Optimization (Markowitz)
- Risk Parity
- Black-Litterman
- Minimum Variance
- Maximum Sharpe Ratio

Supports constraints:
- Position limits (long/short)
- Risk limits (VaR, volatility)
- Asset allocation limits
- Turnover constraints
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy import linalg


@dataclass
class OptimizationConstraints:
    """Portfolio optimization constraints"""

    # Position constraints
    min_weight: float = 0.0  # Minimum weight per asset (0 = long-only)
    max_weight: float = 1.0  # Maximum weight per asset

    # Risk constraints
    max_volatility: Optional[float] = None  # Maximum portfolio volatility
    max_var_95: Optional[float] = None  # Maximum VaR at 95% confidence

    # Allocation constraints
    min_assets: Optional[int] = None  # Minimum number of assets in portfolio
    max_assets: Optional[int] = None  # Maximum number of assets

    # Trading constraints
    max_turnover: Optional[float] = None  # Maximum turnover vs current portfolio

    # Custom constraints
    sector_limits: Optional[Dict[str, Tuple[float, float]]] = None  # Sector exposure limits
    asset_groups: Optional[Dict[str, List[str]]] = None  # Asset groupings


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""

    expected_return: float
    volatility: float
    sharpe_ratio: float
    var_95: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    max_drawdown: float
    weights: Dict[str, float]



class PortfolioOptimizer:
    """
    Portfolio optimization engine for energy trading strategies

    Supports multiple optimization objectives:
    - max_sharpe: Maximum Sharpe ratio
    - min_variance: Minimum variance (risk)
    - max_return: Maximum return (given risk constraint)
    - risk_parity: Equal risk contribution
    - black_litterman: Bayesian views incorporation
    """

    def __init__(
        self,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.03
    ):
        """
        Initialize portfolio optimizer

        Args:
            returns: DataFrame of asset returns (rows=dates, cols=assets)
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
        """
        self.returns = returns
        self.risk_free_rate = risk_free_rate
        self.n_assets = len(returns.columns)
        self.asset_names = list(returns.columns)

        # Calculate statistics
        self.mean_returns = returns.mean()
        self.cov_matrix = returns.cov()

    def optimize(
        self,
        objective: Literal['max_sharpe', 'min_variance', 'max_return', 'risk_parity'] = 'max_sharpe',
        constraints: Optional[OptimizationConstraints] = None,
        target_return: Optional[float] = None,
        current_weights: Optional[Dict[str, float]] = None
    ) -> PortfolioMetrics:
        """
        Optimize portfolio allocation

        Args:
            objective: Optimization objective
            constraints: Portfolio constraints
            target_return: Target return (for min_variance with return constraint)
            current_weights: Current portfolio weights (for turnover constraint)

        Returns:
            Optimized portfolio metrics and weights
        """
        if constraints is None:
            constraints = OptimizationConstraints()

        # Convert current weights to array
        w_current = None
        if current_weights:
            w_current = np.array([current_weights.get(asset, 0.0) for asset in self.asset_names])

        # Initial guess: equal weights
        w0 = np.ones(self.n_assets) / self.n_assets

        # Build constraints
        scipy_constraints = self._build_constraints(
            constraints,
            target_return,
            w_current
        )

        # Build bounds
        bounds = tuple(
            (constraints.min_weight, constraints.max_weight)
            for _ in range(self.n_assets)
        )

        # Choose objective function
        if objective == 'max_sharpe':
            result = minimize(
                self._neg_sharpe_ratio,
                w0,
                method='SLSQP',
                bounds=bounds,
                constraints=scipy_constraints
            )
        elif objective == 'min_variance':
            result = minimize(
                self._portfolio_variance,
                w0,
                method='SLSQP',
                bounds=bounds,
                constraints=scipy_constraints
            )
        elif objective == 'max_return':
            result = minimize(
                self._neg_portfolio_return,
                w0,
                method='SLSQP',
                bounds=bounds,
                constraints=scipy_constraints
            )
        elif objective == 'risk_parity':
            return self._risk_parity_optimization(constraints)
        else:
            raise ValueError(f"Unknown objective: {objective}")

        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")

        # Build portfolio metrics
        weights_dict = {
            asset: float(w)
            for asset, w in zip(self.asset_names, result.x)
            if abs(w) > 1e-6  # Filter out tiny weights
        }

        return self._calculate_metrics(result.x, weights_dict)

    def efficient_frontier(
        self,
        n_points: int = 100,
        constraints: Optional[OptimizationConstraints] = None
    ) -> List[PortfolioMetrics]:
        """
        Generate efficient frontier portfolios

        Args:
            n_points: Number of portfolios to generate
            constraints: Portfolio constraints

        Returns:
            List of portfolio metrics along the efficient frontier
        """
        if constraints is None:
            constraints = OptimizationConstraints()

        # Get return range
        min_ret = float(self.mean_returns.min())
        max_ret = float(self.mean_returns.max())

        # Generate target returns
        target_returns = np.linspace(min_ret, max_ret, n_points)

        frontier = []
        for target_return in target_returns:
            try:
                portfolio = self.optimize(
                    objective='min_variance',
                    constraints=constraints,
                    target_return=target_return
                )
                frontier.append(portfolio)
            except ValueError:
                # Skip infeasible target returns
                continue

        return frontier

    def black_litterman(
        self,
        views: Dict[str, float],
        view_confidence: float = 0.5,
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioMetrics:
        """
        Black-Litterman portfolio optimization with investor views

        Args:
            views: Dictionary of asset views {asset_name: expected_return}
            view_confidence: Confidence in views (0-1), higher = more confident
            constraints: Portfolio constraints

        Returns:
            Optimized portfolio using Black-Litterman model
        """
        # Market equilibrium returns (reverse optimization from equal weights)
        market_weights = np.ones(self.n_assets) / self.n_assets
        risk_aversion = 2.5  # Typical value

        pi = risk_aversion * self.cov_matrix @ market_weights  # Equilibrium returns

        # Build view matrix
        P = np.zeros((len(views), self.n_assets))
        Q = np.zeros(len(views))

        for i, (asset, view_return) in enumerate(views.items()):
            if asset in self.asset_names:
                asset_idx = self.asset_names.index(asset)
                P[i, asset_idx] = 1.0
                Q[i] = view_return

        # View uncertainty (Omega)
        omega = np.diag(np.diag(P @ self.cov_matrix.values @ P.T)) / view_confidence

        # Black-Litterman formula
        tau = 0.05  # Scaling factor for prior uncertainty

        M_inv = linalg.inv(tau * self.cov_matrix.values)
        posterior_cov = linalg.inv(M_inv + P.T @ linalg.inv(omega) @ P)
        posterior_returns = posterior_cov @ (
            M_inv @ pi +
            P.T @ linalg.inv(omega) @ Q
        )

        # Use posterior returns for optimization
        original_returns = self.mean_returns.copy()
        self.mean_returns = pd.Series(posterior_returns, index=self.asset_names)

        try:
            result = self.optimize(
                objective='max_sharpe',
                constraints=constraints
            )
        finally:
            # Restore original returns
            self.mean_returns = original_returns

        return result

    def _build_constraints(
        self,
        constraints: OptimizationConstraints,
        target_return: Optional[float],
        current_weights: Optional[np.ndarray]
    ) -> List[Dict]:
        """Build scipy optimization constraints"""
        scipy_constraints = []

        # Weights must sum to 1
        scipy_constraints.append({
            'type': 'eq',
            'fun': lambda w: np.sum(w) - 1.0
        })

        # Target return constraint
        if target_return is not None:
            scipy_constraints.append({
                'type': 'eq',
                'fun': lambda w: self._portfolio_return(w) - target_return
            })

        # Volatility constraint
        if constraints.max_volatility is not None:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda w: constraints.max_volatility - np.sqrt(self._portfolio_variance(w))
            })

        # VaR constraint
        if constraints.max_var_95 is not None:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda w: constraints.max_var_95 - self._portfolio_var_95(w)
            })

        # Turnover constraint
        if constraints.max_turnover is not None and current_weights is not None:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda w: constraints.max_turnover - np.sum(np.abs(w - current_weights))
            })

        return scipy_constraints

    def _portfolio_return(self, weights: np.ndarray) -> float:
        """Calculate expected portfolio return"""
        return float(weights @ self.mean_returns.values)

    def _portfolio_variance(self, weights: np.ndarray) -> float:
        """Calculate portfolio variance"""
        return float(weights @ self.cov_matrix.values @ weights)

    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Calculate portfolio volatility (std dev)"""
        return np.sqrt(self._portfolio_variance(weights))

    def _sharpe_ratio(self, weights: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        ret = self._portfolio_return(weights)
        vol = self._portfolio_volatility(weights)
        return (ret - self.risk_free_rate) / vol if vol > 0 else 0.0

    def _neg_sharpe_ratio(self, weights: np.ndarray) -> float:
        """Negative Sharpe ratio (for minimization)"""
        return -self._sharpe_ratio(weights)

    def _neg_portfolio_return(self, weights: np.ndarray) -> float:
        """Negative return (for minimization)"""
        return -self._portfolio_return(weights)

    def _portfolio_var_95(self, weights: np.ndarray) -> float:
        """Calculate portfolio VaR at 95% confidence"""
        portfolio_returns = (self.returns.values @ weights)
        return float(np.percentile(portfolio_returns, 5))

    def _portfolio_cvar_95(self, weights: np.ndarray) -> float:
        """Calculate portfolio CVaR (Expected Shortfall) at 95% confidence"""
        portfolio_returns = (self.returns.values @ weights)
        var_95 = np.percentile(portfolio_returns, 5)
        return float(portfolio_returns[portfolio_returns <= var_95].mean())

    def _risk_parity_optimization(
        self,
        constraints: OptimizationConstraints
    ) -> PortfolioMetrics:
        """
        Risk parity optimization - equal risk contribution

        Each asset contributes equally to portfolio risk
        """
        # Initial guess
        w0 = np.ones(self.n_assets) / self.n_assets

        # Bounds
        bounds = tuple(
            (constraints.min_weight, constraints.max_weight)
            for _ in range(self.n_assets)
        )

        # Constraint: weights sum to 1
        scipy_constraints = [{
            'type': 'eq',
            'fun': lambda w: np.sum(w) - 1.0
        }]

        # Objective: minimize difference in risk contributions
        def risk_parity_objective(weights):
            # Risk contributions
            portfolio_vol = self._portfolio_volatility(weights)
            marginal_contrib = self.cov_matrix.values @ weights
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Target equal contribution
            target = portfolio_vol / self.n_assets
            return np.sum((risk_contrib - target) ** 2)

        result = minimize(
            risk_parity_objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints
        )

        if not result.success:
            raise ValueError(f"Risk parity optimization failed: {result.message}")

        weights_dict = {
            asset: float(w)
            for asset, w in zip(self.asset_names, result.x)
            if abs(w) > 1e-6
        }

        return self._calculate_metrics(result.x, weights_dict)

    def _calculate_metrics(
        self,
        weights: np.ndarray,
        weights_dict: Dict[str, float]
    ) -> PortfolioMetrics:
        """Calculate portfolio metrics"""

        # Calculate returns series
        portfolio_returns = (self.returns.values @ weights)

        # Maximum drawdown
        cumulative = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())

        return PortfolioMetrics(
            expected_return=self._portfolio_return(weights),
            volatility=self._portfolio_volatility(weights),
            sharpe_ratio=self._sharpe_ratio(weights),
            var_95=self._portfolio_var_95(weights),
            cvar_95=self._portfolio_cvar_95(weights),
            max_drawdown=max_dd,
            weights=weights_dict
        )


# Example usage
async def main():
    """Example portfolio optimization"""

    # Example: Optimize allocation across 5 NEM trading strategies
    # Generate synthetic strategy returns
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', '2026-03-22', freq='D')

    strategies = [
        'momentum_nsw1',
        'mean_reversion_qld1',
        'spread_trading_vic1_sa1',
        'ml_forecast_nsw1',
        'arbitrage_dam_rtm'
    ]

    # Simulate returns (daily)
    returns_data = {
        'momentum_nsw1': np.random.normal(0.001, 0.02, len(dates)),
        'mean_reversion_qld1': np.random.normal(0.0008, 0.015, len(dates)),
        'spread_trading_vic1_sa1': np.random.normal(0.0012, 0.025, len(dates)),
        'ml_forecast_nsw1': np.random.normal(0.0015, 0.018, len(dates)),
        'arbitrage_dam_rtm': np.random.normal(0.0005, 0.01, len(dates)),
    }

    returns = pd.DataFrame(returns_data, index=dates)

    # Initialize optimizer
    optimizer = PortfolioOptimizer(returns, risk_free_rate=0.03)

    print("=" * 80)
    print("Portfolio Optimization Example")
    print("=" * 80)
    print()

    # 1. Maximum Sharpe Ratio
    print("1. Maximum Sharpe Ratio Portfolio")
    print("-" * 80)

    constraints = OptimizationConstraints(
        min_weight=0.0,  # Long-only
        max_weight=0.4,  # No more than 40% in single strategy
    )

    max_sharpe = optimizer.optimize(
        objective='max_sharpe',
        constraints=constraints
    )

    print(f"Expected Return: {max_sharpe.expected_return:.2%}")
    print(f"Volatility: {max_sharpe.volatility:.2%}")
    print(f"Sharpe Ratio: {max_sharpe.sharpe_ratio:.2f}")
    print(f"VaR (95%): {max_sharpe.var_95:.2%}")
    print()
    print("Weights:")
    for asset, weight in sorted(max_sharpe.weights.items(), key=lambda x: -x[1]):
        print(f"  {asset:30} {weight:>6.1%}")
    print()

    # 2. Minimum Variance
    print("2. Minimum Variance Portfolio")
    print("-" * 80)

    min_var = optimizer.optimize(
        objective='min_variance',
        constraints=constraints
    )

    print(f"Expected Return: {min_var.expected_return:.2%}")
    print(f"Volatility: {min_var.volatility:.2%}")
    print(f"Sharpe Ratio: {min_var.sharpe_ratio:.2f}")
    print()
    print("Weights:")
    for asset, weight in sorted(min_var.weights.items(), key=lambda x: -x[1]):
        print(f"  {asset:30} {weight:>6.1%}")
    print()

    # 3. Risk Parity
    print("3. Risk Parity Portfolio")
    print("-" * 80)

    risk_parity = optimizer.optimize(
        objective='risk_parity',
        constraints=constraints
    )

    print(f"Expected Return: {risk_parity.expected_return:.2%}")
    print(f"Volatility: {risk_parity.volatility:.2%}")
    print(f"Sharpe Ratio: {risk_parity.sharpe_ratio:.2f}")
    print()
    print("Weights:")
    for asset, weight in sorted(risk_parity.weights.items(), key=lambda x: -x[1]):
        print(f"  {asset:30} {weight:>6.1%}")
    print()

    # 4. Black-Litterman with views
    print("4. Black-Litterman with Market Views")
    print("-" * 80)
    print("Views: Bullish on momentum_nsw1 (expect 15% annual return)")
    print("       Bearish on spread_trading (expect 5% annual return)")
    print()

    views = {
        'momentum_nsw1': 0.15 / 252,  # Daily return
        'spread_trading_vic1_sa1': 0.05 / 252,
    }

    bl_portfolio = optimizer.black_litterman(
        views=views,
        view_confidence=0.7,
        constraints=constraints
    )

    print(f"Expected Return: {bl_portfolio.expected_return:.2%}")
    print(f"Volatility: {bl_portfolio.volatility:.2%}")
    print(f"Sharpe Ratio: {bl_portfolio.sharpe_ratio:.2f}")
    print()
    print("Weights:")
    for asset, weight in sorted(bl_portfolio.weights.items(), key=lambda x: -x[1]):
        print(f"  {asset:30} {weight:>6.1%}")
    print()

    print("=" * 80)
    print("Portfolio Optimization Complete!")
    print("=" * 80)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
