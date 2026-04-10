"""
Test Professional Monte Carlo Implementation
"""
import sys
import numpy as np
from app.backend.engines.monte_carlo_professional import (
    ProfessionalMonteCarloEngine,
    STOCHASTIC_AVAILABLE,
    QUANTSTATS_AVAILABLE,
    NUMBA_AVAILABLE
)

def test_professional_monte_carlo():
    """Test the professional Monte Carlo implementation"""

    print("=" * 80)
    print("PROFESSIONAL MONTE CARLO SIMULATION TEST")
    print("=" * 80)
    print()

    # Library status
    print("Library Status:")
    print(f"  stochastic:  {'✅ Available' if STOCHASTIC_AVAILABLE else '❌ Not available'}")
    print(f"  quantstats:  {'✅ Available' if QUANTSTATS_AVAILABLE else '❌ Not available'}")
    print(f"  numba:       {'✅ Available' if NUMBA_AVAILABLE else '❌ Not available'}")
    print()

    # Test parameters (matching APEX use case)
    spot_price = 96.0  # $/MWh
    volatility = 0.35  # 35% annual volatility
    drift = 0.02       # 2% expected return
    exposure_mw = 500.0  # 500 MW position

    print("Simulation Parameters:")
    print(f"  Spot Price:    ${spot_price:.2f}/MWh")
    print(f"  Volatility:    {volatility*100:.1f}%")
    print(f"  Drift:         {drift*100:.1f}%")
    print(f"  Exposure:      {exposure_mw:.0f} MW")
    print(f"  Simulations:   10,000 paths")
    print(f"  Time Steps:    252 (1 year daily)")
    print()

    # Create engine with GBM process
    print("Creating Professional Monte Carlo Engine...")
    engine = ProfessionalMonteCarloEngine(
        spot_price=spot_price,
        volatility=volatility,
        drift=drift,
        process_type='gbm',
        random_seed=42
    )
    print(f"✅ Engine created with process type: {engine.process_type}")
    print()

    # Run simulation
    print("Running simulation...")
    result = engine.simulate_price_paths(
        n_simulations=10_000,
        n_steps=252,
        exposure_mw=exposure_mw,
        save_paths=True
    )
    print("✅ Simulation complete")
    print()

    # Display results
    print("=" * 80)
    print("RISK METRICS")
    print("=" * 80)
    print()

    print("Value at Risk (VaR):")
    print(f"  VaR 95%:  ${result.var_95:,.2f}")
    print(f"  VaR 99%:  ${result.var_99:,.2f}")
    print()

    print("Conditional VaR (Expected Shortfall):")
    print(f"  CVaR 95%: ${result.cvar_95:,.2f}")
    print(f"  CVaR 99%: ${result.cvar_99:,.2f}")
    print()

    print("P&L Distribution:")
    print(f"  Mean P&L:     ${result.mean_pnl:,.2f}")
    print(f"  Median P&L:   ${result.median_pnl:,.2f}")
    print(f"  Std Dev:      ${result.std_pnl:,.2f}")
    print(f"  Skewness:     {result.skewness:.3f} {'(right-skewed)' if result.skewness > 0 else '(left-skewed)'}")
    print(f"  Kurtosis:     {result.kurtosis:.3f} {'(fat tails)' if result.kurtosis > 3 else '(thin tails)'}")
    print()

    print("Percentiles:")
    print(f"  P1:  ${result.percentile_1:,.2f}")
    print(f"  P5:  ${result.percentile_5:,.2f}")
    print(f"  P25: ${result.percentile_25:,.2f}")
    print(f"  P75: ${result.percentile_75:,.2f}")
    print(f"  P95: ${result.percentile_95:,.2f}")
    print(f"  P99: ${result.percentile_99:,.2f}")
    print()

    # Professional risk metrics
    if any([result.sharpe_ratio, result.sortino_ratio, result.calmar_ratio,
            result.omega_ratio, result.tail_ratio]):
        print("=" * 80)
        print("PROFESSIONAL RISK METRICS")
        print("=" * 80)
        print()

        if result.sharpe_ratio is not None:
            print(f"  Sharpe Ratio:  {result.sharpe_ratio:>8.3f}  (risk-adjusted return)")
        if result.sortino_ratio is not None:
            print(f"  Sortino Ratio: {result.sortino_ratio:>8.3f}  (downside risk focus)")
        if result.calmar_ratio is not None:
            print(f"  Calmar Ratio:  {result.calmar_ratio:>8.3f}  (return / max drawdown)")
        if result.omega_ratio is not None:
            print(f"  Omega Ratio:   {result.omega_ratio:>8.3f}  (gains / losses)")
        if result.tail_ratio is not None:
            print(f"  Tail Ratio:    {result.tail_ratio:>8.3f}  (upside / downside tail)")
        print()

    # Simulation paths
    print("=" * 80)
    print("SIMULATION PATHS")
    print("=" * 80)
    print()
    print(f"Total paths saved: {len(result.paths)}")

    if len(result.paths) > 0:
        var_breaches = sum(1 for p in result.paths if p.var_breach)
        print(f"VaR breaches:      {var_breaches} ({var_breaches/len(result.paths)*100:.1f}%)")
        print()

        # Show worst 3 paths
        worst_paths = sorted(result.paths, key=lambda p: p.final_pnl)[:3]
        print("Worst 3 paths:")
        for i, path in enumerate(worst_paths, 1):
            print(f"  #{i}: Final P&L = ${path.final_pnl:,.2f}, Max DD = {path.max_drawdown:.2%}")
        print()

        # Show best 3 paths
        best_paths = sorted(result.paths, key=lambda p: p.final_pnl, reverse=True)[:3]
        print("Best 3 paths:")
        for i, path in enumerate(best_paths, 1):
            print(f"  #{i}: Final P&L = ${path.final_pnl:,.2f}, Max DD = {path.max_drawdown:.2%}")

    print()
    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY ✅")
    print("=" * 80)

    return result


if __name__ == "__main__":
    try:
        result = test_professional_monte_carlo()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
