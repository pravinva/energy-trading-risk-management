"""
Strategy Executor
Runs strategies in live/paper trading mode with monitoring and risk management
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.backend.strategies.base_strategy import BaseStrategy, Position
from app.backend.database import execute_sql
from app.backend.config import get_settings


class StrategyExecutor:
    """
    Strategy executor for live and paper trading

    Features:
    - Continuous strategy execution
    - Real-time position monitoring
    - Risk limit enforcement
    - Performance tracking
    - Alert generation
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        mode: str = 'PAPER',  # 'PAPER' or 'LIVE'
        execution_interval_seconds: int = 60,
    ):
        """
        Initialize strategy executor

        Args:
            strategy: Strategy to execute
            mode: Trading mode (PAPER or LIVE)
            execution_interval_seconds: Time between executions
        """
        self.strategy = strategy
        self.mode = mode
        self.execution_interval = execution_interval_seconds
        self.catalog = get_settings().apex_catalog

        # State
        self.is_running = False
        self.total_executions = 0
        self.last_signal = None

    async def start(self):
        """Start strategy execution loop"""
        self.is_running = True
        print(f"Starting {self.strategy.strategy_name} in {self.mode} mode")
        print(f"Execution interval: {self.execution_interval}s")

        await self._initialize_strategy()

        while self.is_running:
            try:
                await self._execute_cycle()
                self.total_executions += 1

            except Exception as e:
                print(f"Error in execution cycle: {e}")
                await self._log_error(str(e))

            # Wait for next execution
            await asyncio.sleep(self.execution_interval)

    async def stop(self):
        """Stop strategy execution"""
        self.is_running = False
        print(f"Stopping {self.strategy.strategy_name}")

        # Close all positions if in paper mode
        if self.mode == 'PAPER':
            await self._close_all_positions()

    async def _initialize_strategy(self):
        """Initialize strategy state"""
        # Load existing positions
        await self._load_positions()

        # Save strategy to database
        await self.strategy.save_to_database()

        print(f"Strategy initialized: {len(self.strategy.positions)} positions loaded")

    async def _execute_cycle(self):
        """Execute one strategy cycle"""
        print(f"\n=== Execution cycle {self.total_executions + 1} ===")

        # Get current market prices
        current_prices = await self._get_current_prices()

        # Update position valuations
        await self.strategy.update_positions(current_prices)

        # Check risk limits
        risk_status = await self._check_risk_limits()
        if not risk_status['ok']:
            await self._handle_risk_breach(risk_status)
            return

        # Execute strategy
        signal = await self.strategy.execute_strategy()
        self.last_signal = signal

        print(f"Signal: {signal.action} {signal.volume_mw} MW @ {signal.instrument}")
        print(f"Confidence: {signal.confidence:.2f}")
        print(f"Reasoning: {signal.reasoning[:100]}...")

        # Execute signal if approved
        if signal.action in ['BUY', 'SELL'] and signal.confidence > 0.5:
            if self.mode == 'LIVE':
                await self._execute_live_trade(signal)
            else:
                await self._execute_paper_trade(signal)

        # Log execution
        await self._log_execution(signal)

    async def _get_current_prices(self) -> Dict[str, float]:
        """Get current market prices"""
        try:
            sql = f"""
            WITH latest AS (
                SELECT
                    region_id,
                    CAST(rrp AS DOUBLE) AS price,
                    ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) AS rn
                FROM {self.catalog}.market_nem.prices
            )
            SELECT region_id, price
            FROM latest
            WHERE rn = 1
            """
            rows = await execute_sql(sql)
            return {str(r.get('region_id')): float(r.get('price', 50.0)) for r in rows}
        except Exception:
            # Return default prices if query fails
            return {self.strategy.parameters.region_id: 50.0}

    async def _check_risk_limits(self) -> Dict[str, any]:
        """Check if strategy is within risk limits"""
        total_exposure = self.strategy.get_total_exposure()
        max_exposure = self.strategy.parameters.max_position_mw

        if total_exposure > max_exposure:
            return {
                'ok': False,
                'reason': f'Position limit exceeded: {total_exposure} MW > {max_exposure} MW',
                'severity': 'HIGH',
            }

        # Check portfolio-level limits (if needed)
        # TODO: Add VaR check, concentration limits, etc.

        return {'ok': True}

    async def _handle_risk_breach(self, risk_status: Dict[str, any]):
        """Handle risk limit breach"""
        print(f"RISK ALERT: {risk_status['reason']}")

        # Create risk alert
        try:
            sql = f"""
            INSERT INTO {self.catalog}.strategy.risk_alerts
            (alert_id, strategy_id, timestamp, alert_type, severity, description, current_value, threshold_value, acknowledged)
            VALUES (
                '{str(uuid.uuid4())}',
                '{self.strategy.strategy_id}',
                current_timestamp(),
                'POSITION_LIMIT',
                '{risk_status.get('severity', 'HIGH')}',
                '{risk_status['reason']}',
                {self.strategy.get_total_exposure()},
                {self.strategy.parameters.max_position_mw},
                false
            )
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Failed to create risk alert: {e}")

    async def _execute_paper_trade(self, signal):
        """Execute trade in paper trading mode"""
        print(f"PAPER TRADE: {signal.action} {signal.volume_mw} MW")

        # Simulate trade execution
        position_id = str(uuid.uuid4())
        current_price = 50.0  # Default price

        try:
            # Get actual current price
            prices = await self._get_current_prices()
            current_price = prices.get(signal.instrument, 50.0)
        except Exception:
            pass

        # Create position
        if signal.action == 'BUY':
            position = Position(
                position_id=position_id,
                instrument=signal.instrument,
                entry_price=current_price,
                volume_mw=signal.volume_mw,
                entry_timestamp=datetime.now(timezone.utc),
                stop_loss=current_price * (1 - self.strategy.parameters.stop_loss_pct / 100),
                take_profit=current_price * (1 + self.strategy.parameters.take_profit_pct / 100),
            )
            self.strategy.positions.append(position)

            # Save to database
            await self._save_position(position)

        elif signal.action == 'SELL' and self.strategy.positions:
            # Close position
            position = self.strategy.positions.pop(0)
            pnl = (current_price - position.entry_price) * position.volume_mw

            print(f"Position closed: PnL = ${pnl:,.2f}")

            # Update position in database
            await self._close_position(position.position_id, current_price, pnl)

    async def _execute_live_trade(self, signal):
        """Execute trade in live trading mode"""
        # TODO: Integrate with actual trading API
        print(f"LIVE TRADE: {signal.action} {signal.volume_mw} MW")
        print("Note: Live trading integration not yet implemented")

    async def _load_positions(self):
        """Load existing positions from database"""
        try:
            sql = f"""
            SELECT
                position_id,
                instrument,
                entry_price,
                volume_mw,
                entry_timestamp,
                stop_loss,
                take_profit,
                unrealized_pnl
            FROM {self.catalog}.strategy.positions
            WHERE strategy_id = '{self.strategy.strategy_id}'
              AND status = 'OPEN'
            """
            rows = await execute_sql(sql)

            for row in rows:
                position = Position(
                    position_id=str(row.get('position_id')),
                    instrument=str(row.get('instrument')),
                    entry_price=float(row.get('entry_price')),
                    volume_mw=float(row.get('volume_mw')),
                    entry_timestamp=row.get('entry_timestamp'),
                    stop_loss=float(row.get('stop_loss')),
                    take_profit=float(row.get('take_profit')),
                    unrealized_pnl=float(row.get('unrealized_pnl', 0)),
                )
                self.strategy.positions.append(position)

        except Exception as e:
            print(f"Failed to load positions: {e}")

    async def _save_position(self, position: Position):
        """Save position to database"""
        try:
            sql = f"""
            INSERT INTO {self.catalog}.strategy.positions
            (position_id, strategy_id, instrument, region_id, entry_timestamp, entry_price, volume_mw,
             current_price, unrealized_pnl, stop_loss, take_profit, status)
            VALUES (
                '{position.position_id}',
                '{self.strategy.strategy_id}',
                '{position.instrument}',
                '{self.strategy.parameters.region_id}',
                '{position.entry_timestamp}',
                {position.entry_price},
                {position.volume_mw},
                {position.entry_price},
                0.0,
                {position.stop_loss},
                {position.take_profit},
                'OPEN'
            )
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Failed to save position: {e}")

    async def _close_position(self, position_id: str, close_price: float, pnl: float):
        """Close position in database"""
        try:
            sql = f"""
            UPDATE {self.catalog}.strategy.positions
            SET status = 'CLOSED',
                closed_timestamp = current_timestamp(),
                closed_price = {close_price},
                realized_pnl = {pnl}
            WHERE position_id = '{position_id}'
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Failed to close position: {e}")

    async def _close_all_positions(self):
        """Close all open positions"""
        print("Closing all positions...")
        prices = await self._get_current_prices()

        for position in list(self.strategy.positions):
            current_price = prices.get(position.instrument, position.entry_price)
            pnl = (current_price - position.entry_price) * position.volume_mw

            await self._close_position(position.position_id, current_price, pnl)
            self.strategy.positions.remove(position)

            print(f"Closed position {position.position_id}: PnL = ${pnl:,.2f}")

    async def _log_execution(self, signal):
        """Log execution cycle"""
        # Signal is already logged by strategy
        # Additional logging can be added here
        pass

    async def _log_error(self, error_message: str):
        """Log execution error"""
        print(f"ERROR: {error_message}")

    def get_status(self) -> Dict[str, any]:
        """Get executor status"""
        return {
            'strategy_name': self.strategy.strategy_name,
            'mode': self.mode,
            'is_running': self.is_running,
            'total_executions': self.total_executions,
            'open_positions': len(self.strategy.positions),
            'total_exposure_mw': self.strategy.get_total_exposure(),
            'last_signal': self.last_signal.model_dump() if self.last_signal else None,
        }
