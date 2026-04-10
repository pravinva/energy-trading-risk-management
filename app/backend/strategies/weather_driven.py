"""
Weather-Driven Trading Strategy
Uses Phase 1 forecasts (volume, weather, production) to make trading decisions
"""
from __future__ import annotations

from typing import Dict, Any

from app.backend.strategies.base_strategy import (
    BaseStrategy,
    StrategyParameters,
    StrategySignal,
)


class WeatherDrivenStrategy(BaseStrategy):
    """
    Weather-Driven Strategy

    Logic:
    1. Get 15-day volume forecast (BUY/SELL recommendations)
    2. Get weather forecast (wind, solar, temperature)
    3. Get production forecast (renewable generation)
    4. Combine signals for trading decision

    Entry Signals:
    - Volume forecast shows BUY day + High wind forecast → BUY
    - Volume forecast shows SELL day + High renewable production → SELL
    - Weather impact shows price correlation → Anticipate price moves

    Exit Signals:
    - Forecast changes direction
    - Stop loss or take profit hit
    - Confidence drops below threshold
    """

    def __init__(
        self,
        strategy_id: str = 'weather-001',
        parameters: StrategyParameters | None = None,
    ):
        if parameters is None:
            parameters = StrategyParameters(
                region_id='NSW1',
                position_size_mw=150.0,
                max_position_mw=500.0,
                forecast_confidence_threshold=0.6,
            )

        super().__init__(
            strategy_id=strategy_id,
            strategy_name='Weather-Driven Strategy',
            strategy_type='WEATHER_DRIVEN',
            description='Trades based on weather and volume forecasts',
            parameters=parameters,
        )

    async def generate_signal(self) -> StrategySignal:
        """Generate signal from weather and volume forecasts"""

        # Use ForecastAgent to analyze all forecast data
        forecast_instruction = f"""
        Analyze forecasts for {self.parameters.region_id} and identify trading opportunities:

        1. Get the 15-day volume forecast
        2. Get the 7-day weather forecast
        3. Get the 7-day production forecast (focus on RENEWABLES)
        4. Get any plant maintenance/outage events

        Look for:
        - Tomorrow's volume forecast (BUY or SELL day)
        - High wind/solar forecasts (→ more renewable generation → lower prices)
        - Scheduled outages (→ reduced supply → higher prices)
        - Confluence of multiple signals

        Recommend a trading action with confidence level.
        """

        # Forecast agent analyzes all data
        forecast_decision = await self.forecast_agent.act(forecast_instruction)

        # Quant agent makes final trading decision
        quant_instruction = f"""
        Based on the forecast analysis, make a trading decision:

        Forecast Agent Analysis:
        {forecast_decision.reasoning}

        Current positions: {len(self.positions)}
        Region: {self.parameters.region_id}
        Position size: {self.parameters.position_size_mw} MW

        Decide: BUY, SELL, or HOLD
        - If forecasts align strongly → BUY or SELL
        - If mixed signals → HOLD
        - Consider forecast confidence

        Provide clear reasoning and confidence.
        """

        quant_decision = await self.quant_agent.act(quant_instruction)

        # Convert to strategy signal
        signal = StrategySignal(
            signal_type='ENTRY' if quant_decision.decision_type in ['BUY', 'SELL'] else 'REBALANCE',
            action=quant_decision.decision_type,
            instrument=self.parameters.region_id,
            volume_mw=self.parameters.position_size_mw
            if quant_decision.decision_type != 'HOLD'
            else 0.0,
            confidence=quant_decision.confidence,
            reasoning=quant_decision.reasoning,
            metadata={
                'forecast_signals': forecast_decision.metadata.get('signals', []),
                'forecast_horizon': forecast_decision.metadata.get('horizon', 'UNKNOWN'),
                'strategy_type': 'WEATHER_DRIVEN',
            },
        )

        return signal


class MaintenanceAwareStrategy(BaseStrategy):
    """
    Maintenance-Aware Strategy

    Logic:
    1. Monitor plant status timeline (outages, maintenance)
    2. Anticipate capacity shortfalls
    3. Position ahead of scheduled events

    Entry Signals:
    - Large plant outage scheduled → BUY (expect higher prices)
    - Multiple plants returning from maintenance → SELL (expect lower prices)
    - High-impact outage announced → Immediate position

    Exit Signals:
    - Outage ends
    - Price reversion
    - Stop loss/take profit
    """

    def __init__(
        self,
        strategy_id: str = 'maintenance-001',
        parameters: StrategyParameters | None = None,
    ):
        if parameters is None:
            parameters = StrategyParameters(
                region_id='NSW1',
                position_size_mw=200.0,
                max_position_mw=600.0,
            )

        super().__init__(
            strategy_id=strategy_id,
            strategy_name='Maintenance-Aware Strategy',
            strategy_type='MAINTENANCE_AWARE',
            description='Trades ahead of plant outages and maintenance',
            parameters=parameters,
        )

    async def generate_signal(self) -> StrategySignal:
        """Generate signal from plant status data"""

        # Forecast agent gets plant status
        forecast_instruction = f"""
        Analyze plant status and maintenance schedule for {self.parameters.region_id}:

        1. Get plant status events for next 14 days
        2. Identify high-impact outages (OUTAGE with HIGH grid_impact)
        3. Calculate total capacity impact
        4. Look for scheduled maintenance clusters

        Key insights:
        - OUTAGE events → Reduced supply → Higher prices → BUY opportunity
        - MAINTENANCE events → Partial capacity → Moderate price impact
        - RAMP_UP events → Returning capacity → Lower prices → SELL opportunity

        Provide trading recommendation based on upcoming events.
        """

        forecast_decision = await self.forecast_agent.act(forecast_instruction)

        # Quant agent evaluates opportunity
        quant_instruction = f"""
        Based on plant status analysis, evaluate trading opportunity:

        Analysis:
        {forecast_decision.reasoning}

        Decision criteria:
        - High-impact outage (>500 MW) scheduled → Strong BUY signal
        - Multiple plants returning → Strong SELL signal
        - No significant events → HOLD

        Region: {self.parameters.region_id}
        Position size: {self.parameters.position_size_mw} MW

        Make trading decision with reasoning.
        """

        quant_decision = await self.quant_agent.act(quant_instruction)

        signal = StrategySignal(
            signal_type='ENTRY' if quant_decision.decision_type in ['BUY', 'SELL'] else 'REBALANCE',
            action=quant_decision.decision_type,
            instrument=self.parameters.region_id,
            volume_mw=self.parameters.position_size_mw
            if quant_decision.decision_type != 'HOLD'
            else 0.0,
            confidence=quant_decision.confidence,
            reasoning=quant_decision.reasoning,
            metadata={
                'strategy_type': 'MAINTENANCE_AWARE',
                'event_driven': True,
            },
        )

        return signal
