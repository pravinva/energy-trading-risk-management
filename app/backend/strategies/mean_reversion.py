"""
Mean Reversion Trading Strategy
Identifies overbought/oversold conditions and trades reversion to mean
"""
from __future__ import annotations

from app.backend.strategies.base_strategy import (
    BaseStrategy,
    StrategyParameters,
    StrategySignal,
)


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy

    Logic:
    1. Calculate rolling mean and standard deviation of prices
    2. Detect when price deviates >2 std from mean
    3. Trade expecting reversion to mean

    Entry Signals:
    - Price > mean + 2*std → SELL (overbought, expect drop)
    - Price < mean - 2*std → BUY (oversold, expect rise)
    - Z-score threshold determines signal strength

    Exit Signals:
    - Price reverts to mean
    - Z-score < 1.0 (back to normal range)
    - Stop loss (price continues trend)
    - Take profit (strong reversion)

    Parameters:
    - lookback_window: Rolling window for mean calculation (default: 20 periods)
    - entry_threshold: Z-score threshold for entry (default: 2.0)
    - exit_threshold: Z-score threshold for exit (default: 0.5)
    """

    def __init__(
        self,
        strategy_id: str = 'mean-reversion-001',
        parameters: StrategyParameters | None = None,
        lookback_window: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
    ):
        if parameters is None:
            parameters = StrategyParameters(
                region_id='NSW1',
                position_size_mw=100.0,
                max_position_mw=400.0,
                stop_loss_pct=3.0,
                take_profit_pct=8.0,
            )

        super().__init__(
            strategy_id=strategy_id,
            strategy_name='Mean Reversion Strategy',
            strategy_type='MEAN_REVERSION',
            description='Trades price deviations from statistical mean',
            parameters=parameters,
        )

        self.lookback_window = lookback_window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    async def generate_signal(self) -> StrategySignal:
        """Generate mean reversion signal"""

        # Quant agent detects mean reversion opportunity
        quant_instruction = f"""
        Detect mean reversion trading opportunity for {self.parameters.region_id}:

        1. Use detect_mean_reversion_signal tool with:
           - instrument: {self.parameters.region_id}
           - window: {self.lookback_window}
           - threshold: {self.entry_threshold}

        2. Get current price and recent price history

        3. Analyze the signal:
           - Z-score > {self.entry_threshold} → SELL signal (price too high)
           - Z-score < -{self.entry_threshold} → BUY signal (price too low)
           - -threshold < Z-score < threshold → HOLD (normal range)

        4. Check current positions for exit signals:
           - If long position and price reverted → Consider EXIT
           - If short position and price reverted → Consider COVER

        Current positions: {len(self.positions)}
        Entry threshold: {self.entry_threshold} std
        Exit threshold: {self.exit_threshold} std

        Make trading decision with statistical reasoning.
        """

        quant_decision = await self.quant_agent.act(quant_instruction)

        # Determine signal type based on positions
        signal_type = 'ENTRY'
        if len(self.positions) > 0:
            # Have open positions - check for exits
            signal_type = 'EXIT' if quant_decision.decision_type in ['CLOSE', 'HOLD'] else 'REBALANCE'

        signal = StrategySignal(
            signal_type=signal_type,
            action=quant_decision.decision_type,
            instrument=self.parameters.region_id,
            volume_mw=self.parameters.position_size_mw
            if quant_decision.decision_type in ['BUY', 'SELL']
            else 0.0,
            confidence=quant_decision.confidence,
            reasoning=quant_decision.reasoning,
            metadata={
                'strategy_type': 'MEAN_REVERSION',
                'lookback_window': self.lookback_window,
                'entry_threshold': self.entry_threshold,
                'exit_threshold': self.exit_threshold,
            },
        )

        return signal
