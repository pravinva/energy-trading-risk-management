"""
Arbitrage Trading Strategy
Exploits price differences between regions or markets
"""
from __future__ import annotations

from app.backend.strategies.base_strategy import (
    BaseStrategy,
    StrategyParameters,
    StrategySignal,
)


class ArbitrageStrategy(BaseStrategy):
    """
    Arbitrage Strategy

    Logic:
    1. Monitor price spreads between two regions (e.g., NSW1 vs VIC1)
    2. When spread exceeds threshold → Execute arbitrage
    3. Buy in cheaper region, sell in expensive region

    Entry Signals:
    - Spread > mean_spread + 2*std_spread → Arbitrage opportunity
    - Buy in region with lower price
    - Sell in region with higher price

    Exit Signals:
    - Spread converges (returns to mean)
    - Stop loss (spread widens further)
    - Take profit (profitable convergence)

    Types:
    - Cross-regional arbitrage (NSW1-VIC1)
    - Temporal arbitrage (Day-ahead vs Intraday)
    - Asset-type arbitrage (Coal vs Gas pricing)
    """

    def __init__(
        self,
        strategy_id: str = 'arbitrage-001',
        parameters: StrategyParameters | None = None,
        region_pair: tuple[str, str] = ('NSW1', 'VIC1'),
        spread_threshold: float = 2.0,
    ):
        if parameters is None:
            parameters = StrategyParameters(
                region_id=region_pair[0],  # Primary region
                position_size_mw=150.0,
                max_position_mw=500.0,
                stop_loss_pct=2.0,
                take_profit_pct=5.0,
            )

        super().__init__(
            strategy_id=strategy_id,
            strategy_name=f'Arbitrage Strategy ({region_pair[0]}-{region_pair[1]})',
            strategy_type='ARBITRAGE',
            description=f'Cross-regional arbitrage between {region_pair[0]} and {region_pair[1]}',
            parameters=parameters,
        )

        self.region_1 = region_pair[0]
        self.region_2 = region_pair[1]
        self.spread_threshold = spread_threshold

    async def generate_signal(self) -> StrategySignal:
        """Generate arbitrage signal"""

        # Quant agent analyzes spread
        quant_instruction = f"""
        Analyze arbitrage opportunity between {self.region_1} and {self.region_2}:

        1. Use analyze_spread tool with:
           - region_1: {self.region_1}
           - region_2: {self.region_2}
           - hours: 24

        2. Get current prices for both regions

        3. Calculate current spread:
           spread = price_{self.region_1} - price_{self.region_2}

        4. Evaluate arbitrage opportunity:
           - If spread > avg_spread + {self.spread_threshold}*std_spread:
             → BUY {self.region_2}, SELL {self.region_1} (spread too wide)
           - If spread < avg_spread - {self.spread_threshold}*std_spread:
             → BUY {self.region_1}, SELL {self.region_2} (spread inverted)
           - If within normal range:
             → HOLD or exit existing arbitrage

        5. Consider transaction costs:
           - Spread must be wide enough to cover costs
           - Minimum profitable spread: $5/MWh

        Current positions: {len(self.positions)}
        Position size: {self.parameters.position_size_mw} MW per leg
        Spread threshold: {self.spread_threshold} std

        Make arbitrage trading decision.
        """

        quant_decision = await self.quant_agent.act(quant_instruction)

        # For arbitrage, we need paired trades
        # The agent should specify which region to buy/sell
        signal = StrategySignal(
            signal_type='ENTRY' if quant_decision.decision_type in ['BUY', 'SELL'] else 'REBALANCE',
            action=quant_decision.decision_type,
            instrument=quant_decision.instrument,  # Agent specifies which region
            volume_mw=self.parameters.position_size_mw
            if quant_decision.decision_type != 'HOLD'
            else 0.0,
            confidence=quant_decision.confidence,
            reasoning=quant_decision.reasoning,
            metadata={
                'strategy_type': 'ARBITRAGE',
                'region_1': self.region_1,
                'region_2': self.region_2,
                'spread_threshold': self.spread_threshold,
                'paired_trade': True,  # Indicates this needs a hedge
            },
        )

        return signal


class TemporalArbitrageStrategy(BaseStrategy):
    """
    Temporal Arbitrage Strategy

    Exploits price differences between time horizons
    Example: Day-ahead vs Intraday vs Real-time markets
    """

    def __init__(
        self,
        strategy_id: str = 'temporal-arb-001',
        parameters: StrategyParameters | None = None,
    ):
        if parameters is None:
            parameters = StrategyParameters(
                region_id='NSW1',
                position_size_mw=100.0,
                max_position_mw=400.0,
            )

        super().__init__(
            strategy_id=strategy_id,
            strategy_name='Temporal Arbitrage Strategy',
            strategy_type='ARBITRAGE',
            description='Arbitrage between day-ahead and intraday markets',
            parameters=parameters,
        )

    async def generate_signal(self) -> StrategySignal:
        """Generate temporal arbitrage signal"""

        quant_instruction = f"""
        Analyze temporal arbitrage opportunity for {self.parameters.region_id}:

        1. Get price forecast for next 24 hours (day-ahead prices)
        2. Get current spot prices (real-time)
        3. Compare forecasted vs actual prices

        Opportunities:
        - If day-ahead forecast significantly below current spot:
          → Lock in day-ahead purchase, sell spot
        - If day-ahead forecast significantly above current spot:
          → Lock in day-ahead sale, buy spot

        Threshold: Price difference > $10/MWh

        Current positions: {len(self.positions)}
        Region: {self.parameters.region_id}

        Make temporal arbitrage decision.
        """

        quant_decision = await self.quant_agent.act(quant_instruction)

        signal = StrategySignal(
            signal_type='ENTRY',
            action=quant_decision.decision_type,
            instrument=self.parameters.region_id,
            volume_mw=self.parameters.position_size_mw
            if quant_decision.decision_type != 'HOLD'
            else 0.0,
            confidence=quant_decision.confidence,
            reasoning=quant_decision.reasoning,
            metadata={
                'strategy_type': 'TEMPORAL_ARBITRAGE',
                'horizon_spread': True,
            },
        )

        return signal
