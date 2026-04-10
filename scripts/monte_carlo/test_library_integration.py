"""
Test to verify all professional libraries are properly integrated
"""
import sys
import numpy as np

print("=" * 80)
print("PROFESSIONAL LIBRARY INTEGRATION TEST")
print("=" * 80)
print()

# Test 1: Import all libraries directly
print("Test 1: Direct library imports")
print("-" * 80)

try:
    from stochastic.processes.continuous import GeometricBrownianMotion
    print("✅ stochastic.GeometricBrownianMotion imported")
except ImportError as e:
    print(f"❌ stochastic import failed: {e}")
    sys.exit(1)

try:
    import quantstats as qs
    print("✅ quantstats imported")
except ImportError as e:
    print(f"❌ quantstats import failed: {e}")
    sys.exit(1)

try:
    import numba
    print("✅ numba imported")
except ImportError as e:
    print(f"❌ numba import failed: {e}")
    sys.exit(1)

print()

# Test 2: Create a GBM process with stochastic library
print("Test 2: Stochastic library GBM process")
print("-" * 80)

try:
    gbm = GeometricBrownianMotion(drift=0.05, volatility=0.2, t=1.0)
    path = gbm.sample(100)
    print(f"✅ GBM process created and sampled")
    print(f"   Generated {len(path)} time steps")
    print(f"   Path range: [{np.min(path):.4f}, {np.max(path):.4f}]")
except Exception as e:
    print(f"❌ GBM process failed: {e}")
    sys.exit(1)

print()

# Test 3: Calculate metrics with quantstats
print("Test 3: Quantstats risk metrics")
print("-" * 80)

try:
    import pandas as pd

    # Generate sample returns
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)
    dates = pd.date_range(start='2024-01-01', periods=len(returns), freq='D')
    returns_series = pd.Series(returns, index=dates)

    sharpe = qs.stats.sharpe(returns_series, rf=0.02, periods=252)
    sortino = qs.stats.sortino(returns_series, rf=0.02, periods=252)
    calmar = qs.stats.calmar(returns_series)
    max_dd = qs.stats.max_drawdown(returns_series)

    print(f"✅ Quantstats metrics calculated:")
    print(f"   Sharpe Ratio:    {sharpe:.3f}")
    print(f"   Sortino Ratio:   {sortino:.3f}")
    print(f"   Calmar Ratio:    {calmar:.3f}")
    print(f"   Max Drawdown:    {max_dd:.2%}")
except Exception as e:
    print(f"❌ Quantstats metrics failed: {e}")
    sys.exit(1)

print()

# Test 4: Full Monte Carlo simulation with professional engine
print("Test 4: Professional Monte Carlo Engine")
print("-" * 80)

try:
    from app.backend.engines.monte_carlo_professional import (
        ProfessionalMonteCarloEngine,
        STOCHASTIC_AVAILABLE,
        QUANTSTATS_AVAILABLE,
        NUMBA_AVAILABLE
    )

    print(f"Engine library status:")
    print(f"  STOCHASTIC_AVAILABLE:  {STOCHASTIC_AVAILABLE}")
    print(f"  QUANTSTATS_AVAILABLE:  {QUANTSTATS_AVAILABLE}")
    print(f"  NUMBA_AVAILABLE:       {NUMBA_AVAILABLE}")
    print()

    # Create engine
    engine = ProfessionalMonteCarloEngine(
        spot_price=100.0,
        volatility=0.30,
        drift=0.05,
        process_type='gbm',
        random_seed=42
    )

    # Run small simulation
    result = engine.simulate_price_paths(
        n_simulations=1000,
        n_steps=100,
        exposure_mw=100.0,
        save_paths=False
    )

    print(f"✅ Professional Monte Carlo completed:")
    print(f"   VaR 95%:         ${result.var_95:,.2f}")
    print(f"   CVaR 95%:        ${result.cvar_95:,.2f}")
    print(f"   Sharpe Ratio:    {result.sharpe_ratio:.3f}")
    print(f"   Sortino Ratio:   {result.sortino_ratio:.3f}")
    print(f"   Calmar Ratio:    {result.calmar_ratio:.3f}")
    print(f"   Omega Ratio:     {result.omega_ratio:.3f}")
    print(f"   Tail Ratio:      {result.tail_ratio:.3f}")

except Exception as e:
    print(f"❌ Professional Monte Carlo failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("ALL PROFESSIONAL LIBRARIES VERIFIED ✅")
print("=" * 80)
print()
print("Summary:")
print("  ✅ stochastic - GBM process generation")
print("  ✅ quantstats - Professional risk metrics")
print("  ✅ numba - JIT compilation")
print("  ✅ Professional Monte Carlo Engine - Full integration")
