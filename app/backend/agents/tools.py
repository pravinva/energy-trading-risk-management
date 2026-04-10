"""
Agent Tools - Functions available to trading agents
Provides market data, forecasting, risk calculations, and execution capabilities
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.backend.database import execute_sql
from app.backend.config import get_settings


class AgentTools:
    """Collection of tools available to trading agents"""

    def __init__(self):
        self.catalog = get_settings().apex_catalog

    # ========================================================================
    # FORECASTING TOOLS (Phase 1 Integration)
    # ========================================================================

    async def get_volume_forecast(
        self, region_id: str = 'NSW1', days: int = 15
    ) -> Dict[str, Any]:
        """
        Get 15-day BUY/SELL volume forecast

        Args:
            region_id: NEM region (NSW1, VIC1, QLD1, SA1)
            days: Number of days (1-15)

        Returns:
            Volume forecast data with BUY/SELL recommendations
        """
        sql = f"""
        SELECT
            forecast_date,
            forecast_type,
            volume_mwh,
            weather_impact_pct,
            maintenance_impact_pct,
            outage_impact_pct,
            confidence_level
        FROM {self.catalog}.forecasting.volume_forecast
        WHERE region_id = '{region_id}'
          AND forecast_date >= current_date()
          AND forecast_date <= current_date() + INTERVAL {days} DAYS
        ORDER BY forecast_date ASC
        """
        rows = await execute_sql(sql)
        return {
            'region_id': region_id,
            'forecasts': rows,
            'buy_days': len([r for r in rows if r.get('forecast_type') == 'BUY']),
            'sell_days': len([r for r in rows if r.get('forecast_type') == 'SELL']),
        }

    async def get_weather_forecast(
        self, region_id: str = 'NSW1', days: int = 7
    ) -> Dict[str, Any]:
        """
        Get weather forecast data

        Args:
            region_id: NEM region
            days: Number of days

        Returns:
            Weather forecast with temperature, wind, solar
        """
        sql = f"""
        SELECT
            forecast_datetime,
            temperature_celsius,
            wind_speed_ms,
            solar_irradiance_wm2,
            confidence_level
        FROM {self.catalog}.forecasting.weather_forecast
        WHERE region_id = '{region_id}'
          AND forecast_datetime >= current_timestamp()
          AND forecast_datetime <= current_timestamp() + INTERVAL {days} DAYS
        ORDER BY forecast_datetime ASC
        LIMIT 168
        """
        rows = await execute_sql(sql)
        return {'region_id': region_id, 'forecasts': rows}

    async def get_production_forecast(
        self, region_id: str = 'NSW1', asset_type: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get energy production forecast by asset type

        Args:
            region_id: NEM region
            asset_type: Optional filter (RENEWABLES, COAL, GAS, etc.)
            days: Number of days

        Returns:
            Production forecast data
        """
        asset_filter = f"AND asset_type = '{asset_type}'" if asset_type else ''
        sql = f"""
        SELECT
            forecast_datetime,
            asset_type,
            generation_mw,
            capacity_mw,
            efficiency_percent,
            availability_percent
        FROM {self.catalog}.forecasting.production_forecast
        WHERE region_id = '{region_id}'
          {asset_filter}
          AND forecast_datetime >= current_timestamp()
          AND forecast_datetime <= current_timestamp() + INTERVAL {days} DAYS
        ORDER BY forecast_datetime ASC
        LIMIT 500
        """
        rows = await execute_sql(sql)
        return {'region_id': region_id, 'asset_type': asset_type, 'forecasts': rows}

    async def get_plant_status(
        self, region_id: str = 'NSW1', days: int = 14
    ) -> Dict[str, Any]:
        """
        Get plant outages and maintenance schedule

        Args:
            region_id: NEM region
            days: Number of days

        Returns:
            Plant status events
        """
        sql = f"""
        SELECT
            plant_name,
            plant_type,
            event_type,
            start_datetime,
            end_datetime,
            capacity_impact_mw,
            grid_impact,
            description
        FROM {self.catalog}.forecasting.plant_status
        WHERE region_id = '{region_id}'
          AND start_datetime <= current_timestamp() + INTERVAL {days} DAYS
          AND end_datetime >= current_timestamp()
        ORDER BY start_datetime ASC
        """
        rows = await execute_sql(sql)
        return {'region_id': region_id, 'events': rows}

    # ========================================================================
    # MARKET DATA TOOLS
    # ========================================================================

    async def get_current_prices(
        self, market: str = 'NEM', instrument: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current market prices

        Args:
            market: Market name (NEM, EPEX, ERCOT)
            instrument: Optional instrument filter

        Returns:
            Current price data
        """
        if market == 'NEM':
            instrument_filter = (
                f"AND region_id = '{instrument}'" if instrument else ''
            )
            sql = f"""
            WITH latest AS (
                SELECT
                    region_id AS instrument,
                    rrp AS price,
                    interval_datetime AS timestamp,
                    ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) AS rn
                FROM {self.catalog}.market_nem.prices
                {instrument_filter}
            )
            SELECT instrument, price, timestamp
            FROM latest
            WHERE rn = 1
            """
        else:
            raise NotImplementedError(f'Market {market} not yet implemented')

        rows = await execute_sql(sql)
        return {'market': market, 'prices': rows}

    async def get_price_history(
        self,
        market: str = 'NEM',
        instrument: str = 'NSW1',
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get historical price data

        Args:
            market: Market name
            instrument: Instrument/region
            hours: Hours of history

        Returns:
            Historical price data
        """
        if market == 'NEM':
            sql = f"""
            SELECT
                interval_datetime AS timestamp,
                rrp AS price,
                totaldemand AS demand_mw
            FROM {self.catalog}.market_nem.prices
            WHERE region_id = '{instrument}'
              AND interval_datetime >= current_timestamp() - INTERVAL {hours} HOURS
            ORDER BY interval_datetime ASC
            """
        else:
            raise NotImplementedError(f'Market {market} not yet implemented')

        rows = await execute_sql(sql)
        return {
            'market': market,
            'instrument': instrument,
            'hours': hours,
            'data': rows,
        }

    # ========================================================================
    # POSITION & PORTFOLIO TOOLS
    # ========================================================================

    async def get_current_positions(
        self, strategy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current open positions

        Args:
            strategy_id: Optional filter by strategy

        Returns:
            Current positions
        """
        strategy_filter = (
            f"WHERE strategy_id = '{strategy_id}'" if strategy_id else ''
        )
        sql = f"""
        SELECT
            position_id,
            strategy_id,
            instrument,
            region_id,
            entry_timestamp,
            entry_price,
            volume_mw,
            current_price,
            unrealized_pnl,
            status
        FROM {self.catalog}.strategy.positions
        {strategy_filter}
        WHERE status = 'OPEN'
        ORDER BY entry_timestamp DESC
        """
        try:
            rows = await execute_sql(sql)
        except Exception:
            # Table might not exist yet
            rows = []

        return {'strategy_id': strategy_id, 'positions': rows}

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary across all strategies

        Returns:
            Portfolio metrics
        """
        sql = f"""
        SELECT
            COUNT(DISTINCT strategy_id) AS active_strategies,
            COUNT(*) AS open_positions,
            SUM(volume_mw) AS total_volume_mw,
            SUM(unrealized_pnl) AS total_unrealized_pnl
        FROM {self.catalog}.strategy.positions
        WHERE status = 'OPEN'
        """
        try:
            rows = await execute_sql(sql)
            summary = rows[0] if rows else {}
        except Exception:
            summary = {
                'active_strategies': 0,
                'open_positions': 0,
                'total_volume_mw': 0.0,
                'total_unrealized_pnl': 0.0,
            }

        return summary

    # ========================================================================
    # RISK CALCULATION TOOLS
    # ========================================================================

    async def calculate_var(
        self,
        confidence: float = 0.95,
        volatility: float = 0.3,
        spot_price: float = 50.0,
        position_mw: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk

        Args:
            confidence: Confidence level (0.95 or 0.99)
            volatility: Price volatility (decimal)
            spot_price: Current spot price
            position_mw: Position size in MW

        Returns:
            VaR metrics
        """
        import math

        # Z-scores for confidence levels
        z_scores = {0.95: 1.645, 0.99: 2.326}
        z = z_scores.get(confidence, 1.645)

        # VaR calculation
        var = spot_price * position_mw * volatility * z
        expected_shortfall = var * 1.2  # Simplified ES calculation

        return {
            'var': round(var, 2),
            'expected_shortfall': round(expected_shortfall, 2),
            'confidence': confidence,
            'volatility': volatility,
            'position_mw': position_mw,
            'spot_price': spot_price,
        }

    async def calculate_position_metrics(
        self, entry_price: float, current_price: float, volume_mw: float
    ) -> Dict[str, Any]:
        """
        Calculate position metrics

        Args:
            entry_price: Entry price
            current_price: Current price
            volume_mw: Volume in MW

        Returns:
            Position metrics
        """
        pnl = (current_price - entry_price) * volume_mw
        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        return {
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'entry_price': entry_price,
            'current_price': current_price,
            'volume_mw': volume_mw,
        }

    # ========================================================================
    # STRATEGY ANALYSIS TOOLS
    # ========================================================================

    async def analyze_spread(
        self, region_1: str, region_2: str, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze price spread between two regions (arbitrage opportunity)

        Args:
            region_1: First region
            region_2: Second region
            hours: Hours of history

        Returns:
            Spread analysis
        """
        sql = f"""
        WITH prices AS (
            SELECT
                interval_datetime,
                region_id,
                rrp AS price
            FROM {self.catalog}.market_nem.prices
            WHERE region_id IN ('{region_1}', '{region_2}')
              AND interval_datetime >= current_timestamp() - INTERVAL {hours} HOURS
        ),
        spreads AS (
            SELECT
                p1.interval_datetime,
                p1.price - p2.price AS spread
            FROM prices p1
            JOIN prices p2
                ON p1.interval_datetime = p2.interval_datetime
                AND p1.region_id = '{region_1}'
                AND p2.region_id = '{region_2}'
        )
        SELECT
            AVG(spread) AS avg_spread,
            STDDEV(spread) AS std_spread,
            MIN(spread) AS min_spread,
            MAX(spread) AS max_spread
        FROM spreads
        """
        rows = await execute_sql(sql)
        result = rows[0] if rows else {}

        return {
            'region_1': region_1,
            'region_2': region_2,
            'avg_spread': float(result.get('avg_spread', 0)),
            'std_spread': float(result.get('std_spread', 0)),
            'min_spread': float(result.get('min_spread', 0)),
            'max_spread': float(result.get('max_spread', 0)),
        }

    async def detect_mean_reversion_signal(
        self, instrument: str, window: int = 20, threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect mean reversion trading signal

        Args:
            instrument: Instrument/region
            window: Rolling window for mean calculation
            threshold: Standard deviation threshold

        Returns:
            Mean reversion signal
        """
        sql = f"""
        WITH prices AS (
            SELECT
                interval_datetime,
                rrp AS price,
                AVG(rrp) OVER (ORDER BY interval_datetime ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) AS rolling_mean,
                STDDEV(rrp) OVER (ORDER BY interval_datetime ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) AS rolling_std
            FROM {self.catalog}.market_nem.prices
            WHERE region_id = '{instrument}'
            ORDER BY interval_datetime DESC
            LIMIT 1
        )
        SELECT
            price,
            rolling_mean,
            rolling_std,
            (price - rolling_mean) / NULLIF(rolling_std, 0) AS z_score
        FROM prices
        """
        rows = await execute_sql(sql)
        if not rows:
            return {'signal': 'HOLD', 'confidence': 0.0}

        result = rows[0]
        z_score = float(result.get('z_score', 0))

        # Determine signal
        if z_score > threshold:
            signal = 'SELL'  # Price too high, expect reversion
            confidence = min(abs(z_score) / threshold, 1.0)
        elif z_score < -threshold:
            signal = 'BUY'  # Price too low, expect reversion
            confidence = min(abs(z_score) / threshold, 1.0)
        else:
            signal = 'HOLD'
            confidence = 0.0

        return {
            'instrument': instrument,
            'signal': signal,
            'confidence': round(confidence, 2),
            'z_score': round(z_score, 2),
            'current_price': float(result.get('price', 0)),
            'rolling_mean': float(result.get('rolling_mean', 0)),
            'rolling_std': float(result.get('rolling_std', 0)),
        }

    # ========================================================================
    # TOOL REGISTRY
    # ========================================================================

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM function calling

        Returns:
            List of tool definitions
        """
        return [
            {
                'name': 'get_volume_forecast',
                'description': 'Get 15-day BUY/SELL volume forecast for energy trading',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'region_id': {
                            'type': 'string',
                            'description': 'NEM region (NSW1, VIC1, QLD1, SA1)',
                        },
                        'days': {
                            'type': 'integer',
                            'description': 'Number of days (1-15)',
                        },
                    },
                    'required': ['region_id'],
                },
            },
            {
                'name': 'get_weather_forecast',
                'description': 'Get weather forecast (temperature, wind, solar)',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'region_id': {'type': 'string'},
                        'days': {'type': 'integer'},
                    },
                    'required': ['region_id'],
                },
            },
            {
                'name': 'get_current_prices',
                'description': 'Get current market prices',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'market': {'type': 'string'},
                        'instrument': {'type': 'string'},
                    },
                    'required': ['market'],
                },
            },
            {
                'name': 'get_price_history',
                'description': 'Get historical price data',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'market': {'type': 'string'},
                        'instrument': {'type': 'string'},
                        'hours': {'type': 'integer'},
                    },
                    'required': ['market', 'instrument'],
                },
            },
            {
                'name': 'calculate_var',
                'description': 'Calculate Value at Risk for a position',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'confidence': {'type': 'number'},
                        'volatility': {'type': 'number'},
                        'spot_price': {'type': 'number'},
                        'position_mw': {'type': 'number'},
                    },
                    'required': ['spot_price', 'position_mw'],
                },
            },
            {
                'name': 'analyze_spread',
                'description': 'Analyze price spread between two regions for arbitrage',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'region_1': {'type': 'string'},
                        'region_2': {'type': 'string'},
                        'hours': {'type': 'integer'},
                    },
                    'required': ['region_1', 'region_2'],
                },
            },
            {
                'name': 'detect_mean_reversion_signal',
                'description': 'Detect mean reversion trading opportunity',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'instrument': {'type': 'string'},
                        'window': {'type': 'integer'},
                        'threshold': {'type': 'number'},
                    },
                    'required': ['instrument'],
                },
            },
            {
                'name': 'get_plant_status',
                'description': 'Get plant outages and maintenance schedule',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'region_id': {'type': 'string'},
                        'days': {'type': 'integer'},
                    },
                    'required': ['region_id'],
                },
            },
            {
                'name': 'get_current_positions',
                'description': 'Get current open trading positions',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'strategy_id': {'type': 'string'},
                    },
                },
            },
        ]

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool by name

        Args:
            tool_name: Tool function name
            tool_input: Tool input parameters

        Returns:
            Tool execution result
        """
        tool_methods = {
            'get_volume_forecast': self.get_volume_forecast,
            'get_weather_forecast': self.get_weather_forecast,
            'get_production_forecast': self.get_production_forecast,
            'get_plant_status': self.get_plant_status,
            'get_current_prices': self.get_current_prices,
            'get_price_history': self.get_price_history,
            'get_current_positions': self.get_current_positions,
            'get_portfolio_summary': self.get_portfolio_summary,
            'calculate_var': self.calculate_var,
            'calculate_position_metrics': self.calculate_position_metrics,
            'analyze_spread': self.analyze_spread,
            'detect_mean_reversion_signal': self.detect_mean_reversion_signal,
        }

        if tool_name not in tool_methods:
            raise ValueError(f'Unknown tool: {tool_name}')

        method = tool_methods[tool_name]
        return await method(**tool_input)
