"""
Test to verify library detection and usage
"""
import sys

print("Testing library imports within venv...")
print()

# Test stochastic
try:
    from stochastic.processes.continuous import GeometricBrownianMotion
    print("✅ stochastic.GeometricBrownianMotion imported successfully")
    stochastic_available = True
except ImportError as e:
    print(f"❌ stochastic import failed: {e}")
    stochastic_available = False

# Test empyrical
try:
    import empyrical
    print("✅ empyrical imported successfully")
    empyrical_available = True
except ImportError as e:
    print(f"❌ empyrical import failed: {e}")
    empyrical_available = False

# Test numba
try:
    import numba
    print("✅ numba imported successfully")
    numba_available = True
except ImportError as e:
    print(f"❌ numba import failed: {e}")
    numba_available = False

print()
print("=" * 60)
print("Now testing monte_carlo_professional.py detection:")
print("=" * 60)

# Now import and check what monte_carlo_professional detected
from app.backend.engines import monte_carlo_professional as mcp

print(f"STOCHASTIC_AVAILABLE: {mcp.STOCHASTIC_AVAILABLE}")
print(f"EMPYRICAL_AVAILABLE:  {mcp.EMPYRICAL_AVAILABLE}")
print(f"NUMBA_AVAILABLE:      {mcp.NUMBA_AVAILABLE}")

print()

# Run a quick simulation to test actual usage
if stochastic_available:
    print("Testing GBM with stochastic library...")
    engine = mcp.ProfessionalMonteCarloEngine(
        spot_price=100.0,
        volatility=0.3,
        drift=0.05,
        process_type='gbm',
        random_seed=42
    )

    result = engine.simulate_price_paths(
        n_simulations=1000,
        n_steps=100,
        exposure_mw=100.0,
        save_paths=False
    )

    print(f"✅ Simulation complete: VaR 95% = ${result.var_95:,.2f}")
    print(f"   Professional metrics calculated:")
    print(f"   - Sharpe Ratio: {result.sharpe_ratio:.3f}" if result.sharpe_ratio else "   - Sharpe Ratio: Not calculated")
