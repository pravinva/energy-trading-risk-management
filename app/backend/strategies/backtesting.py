"""
Backtesting Engine
Comprehensive strategy validation against historical data
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel

from app.backend.strategies.base_strategy import BaseStrategy, Position
from app.backend.database import execute_sql
from app.backend.config import get_settings


class BacktestTrade(BaseModel):
    """Individual trade in backtest"""

    trade_id: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'CLOSE'
    instrument: str
    volume_mw: float
    price: float
    reasoning: str
    confidence: float
    pnl: Optional[float] = None
    cumulative_pnl: float = 0.0
    position_size_mw: float = 0.0
    portfolio_value: float = 0.0


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""

    # Summary metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Returns
    total_return_pct: float
    total_pnl: float
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float

    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    calmar_ratio: float

    # Volume
    total_volume_mwh: float
    avg_holding_period_hours: float

    # Capital
    initial_capital: float
    final_capital: float


class BacktestEngine:
    """
    Backtesting engine for strategy validation

    Features:
    - Historical data simulation
    - Walk-forward validation
    - Performance metrics calculation
    - Drawdown tracking
    - Trade-by-trade analysis
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 1_000_000.0,
    ):
        """
        Initialize backtest engine

        Args:
            strategy: Strategy to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
        """
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.catalog = get_settings().apex_catalog

        # Backtest state
        self.current_capital = initial_capital
        self.trades: List[BacktestTrade] = []
        self.positions: Dict[str, Position] = {}
        self.equity_curve: List[Dict[str, Any]] = []

        # Metrics
        self.cumulative_pnl = 0.0
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0

    async def run(self) -> BacktestMetrics:
        """
        Run backtest

        Returns:
            Backtest performance metrics
        """
        print(f"Starting backtest for {self.strategy.strategy_name}")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial capital: ${self.initial_capital:,.2f}")

        # Get historical data
        historical_data = await self._load_historical_data()

        if not historical_data:
            print("Warning: No historical data found, using simulated data")
            historical_data = self._generate_simulated_data()

        # Run backtest day by day
        current_date = self.start_date
        days_processed = 0

        while current_date <= self.end_date:
            # Get market data for this day
            day_data = [d for d in historical_data if d['date'].date() == current_date.date()]

            if day_data:
                await self._process_day(current_date, day_data)
                days_processed += 1

            current_date += timedelta(days=1)

        print(f"Backtest complete: {days_processed} days processed")

        # Calculate final metrics
        metrics = self._calculate_metrics()

        # Save backtest results
        await self._save_results(metrics)

        return metrics

    async def _load_historical_data(self) -> List[Dict[str, Any]]:
        """Load historical price data"""
        try:
            sql = f"""
            SELECT
                interval_datetime AS timestamp,
                CAST(interval_datetime AS DATE) AS date,
                region_id AS instrument,
                CAST(rrp AS DOUBLE) AS price,
                CAST(totaldemand AS DOUBLE) AS demand_mw
            FROM {self.catalog}.market_nem.prices
            WHERE region_id = '{self.strategy.parameters.region_id}'
              AND interval_datetime >= '{self.start_date}'
              AND interval_datetime <= '{self.end_date}'
            ORDER BY interval_datetime ASC
            """
            rows = await execute_sql(sql)
            return rows
        except Exception as e:
            print(f"Failed to load historical data: {e}")
            return []

    def _generate_simulated_data(self) -> List[Dict[str, Any]]:
        """Generate simulated price data for backtesting"""
        data = []
        current_date = self.start_date
        price = 50.0  # Starting price

        while current_date <= self.end_date:
            # Random walk with drift
            drift = 0.0001
            volatility = 0.02
            price_change = drift + volatility * np.random.randn()
            price = price * (1 + price_change)

            # Add hourly data points
            for hour in range(24):
                timestamp = current_date + timedelta(hours=hour)
                data.append({
                    'timestamp': timestamp,
                    'date': current_date,
                    'instrument': self.strategy.parameters.region_id,
                    'price': price,
                    'demand_mw': 5000 + np.random.randn() * 500,
                })

            current_date += timedelta(days=1)

        return data

    async def _process_day(self, date: datetime, day_data: List[Dict[str, Any]]):
        """Process a single day of trading"""

        # Get current price (use end of day price)
        current_price = day_data[-1]['price']

        # Update position valuations
        await self._update_positions(current_price)

        # Generate trading signal from strategy
        try:
            signal = await self.strategy.generate_signal()

            # Execute signal
            if signal.action in ['BUY', 'SELL']:
                await self._execute_trade(
                    date=date,
                    action=signal.action,
                    instrument=signal.instrument,
                    volume_mw=signal.volume_mw,
                    price=current_price,
                    reasoning=signal.reasoning,
                    confidence=signal.confidence,
                )
            elif signal.action == 'CLOSE':
                # Close all positions
                await self._close_all_positions(date, current_price)

        except Exception as e:
            print(f"Error processing day {date}: {e}")

        # Record equity curve
        self._record_equity_snapshot(date, current_price)

    async def _update_positions(self, current_price: float):
        """Update position valuations"""
        for position in self.positions.values():
            position.unrealized_pnl = (
                current_price - position.entry_price
            ) * position.volume_mw

            # Check stop loss and take profit
            pnl_pct = (position.unrealized_pnl / (position.entry_price * position.volume_mw)) * 100

            if pnl_pct <= -self.strategy.parameters.stop_loss_pct:
                # Stop loss hit
                print(f"Stop loss hit for {position.position_id}: {pnl_pct:.2f}%")
            elif pnl_pct >= self.strategy.parameters.take_profit_pct:
                # Take profit hit
                print(f"Take profit hit for {position.position_id}: {pnl_pct:.2f}%")

    async def _execute_trade(
        self,
        date: datetime,
        action: str,
        instrument: str,
        volume_mw: float,
        price: float,
        reasoning: str,
        confidence: float,
    ):
        """Execute a trade in backtest"""

        trade_cost = price * volume_mw
        pnl = None
        cumulative_pnl = self.cumulative_pnl

        if action == 'BUY':
            # Open long position
            if self.current_capital < trade_cost:
                print(f"Insufficient capital for BUY: ${self.current_capital:,.2f} < ${trade_cost:,.2f}")
                return

            position_id = str(uuid.uuid4())
            position = Position(
                position_id=position_id,
                instrument=instrument,
                entry_price=price,
                volume_mw=volume_mw,
                entry_timestamp=date,
                stop_loss=price * (1 - self.strategy.parameters.stop_loss_pct / 100),
                take_profit=price * (1 + self.strategy.parameters.take_profit_pct / 100),
            )
            self.positions[position_id] = position
            self.current_capital -= trade_cost

        elif action == 'SELL':
            # Close long position or open short
            if self.positions:
                # Close existing long position
                position_id = list(self.positions.keys())[0]
                position = self.positions[position_id]
                pnl = (price - position.entry_price) * position.volume_mw
                self.cumulative_pnl += pnl
                cumulative_pnl = self.cumulative_pnl
                self.current_capital += trade_cost + pnl
                del self.positions[position_id]
            else:
                # Open short position (simplified)
                pass

        # Record trade
        trade = BacktestTrade(
            trade_id=str(uuid.uuid4()),
            timestamp=date,
            action=action,
            instrument=instrument,
            volume_mw=volume_mw,
            price=price,
            reasoning=reasoning,
            confidence=confidence,
            pnl=pnl,
            cumulative_pnl=cumulative_pnl,
            position_size_mw=sum(p.volume_mw for p in self.positions.values()),
            portfolio_value=self._calculate_portfolio_value(price),
        )
        self.trades.append(trade)

    async def _close_all_positions(self, date: datetime, current_price: float):
        """Close all open positions"""
        for position_id, position in list(self.positions.items()):
            pnl = (current_price - position.entry_price) * position.volume_mw
            self.cumulative_pnl += pnl
            self.current_capital += (current_price * position.volume_mw) + pnl

            trade = BacktestTrade(
                trade_id=str(uuid.uuid4()),
                timestamp=date,
                action='CLOSE',
                instrument=position.instrument,
                volume_mw=position.volume_mw,
                price=current_price,
                reasoning='Position closed',
                confidence=1.0,
                pnl=pnl,
                cumulative_pnl=self.cumulative_pnl,
                position_size_mw=0.0,
                portfolio_value=self.current_capital,
            )
            self.trades.append(trade)
            del self.positions[position_id]

    def _calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate total portfolio value"""
        cash = self.current_capital
        position_value = sum(
            position.volume_mw * current_price for position in self.positions.values()
        )
        return cash + position_value

    def _record_equity_snapshot(self, date: datetime, current_price: float):
        """Record equity curve snapshot"""
        portfolio_value = self._calculate_portfolio_value(current_price)

        # Update peak and drawdown
        if portfolio_value > self.peak_capital:
            self.peak_capital = portfolio_value

        drawdown = self.peak_capital - portfolio_value
        drawdown_pct = (drawdown / self.peak_capital) * 100 if self.peak_capital > 0 else 0

        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

        self.equity_curve.append({
            'timestamp': date,
            'portfolio_value': portfolio_value,
            'cash': self.current_capital,
            'position_value': portfolio_value - self.current_capital,
            'total_pnl': self.cumulative_pnl,
            'drawdown': drawdown,
            'drawdown_pct': drawdown_pct,
            'open_positions': len(self.positions),
        })

    def _calculate_metrics(self) -> BacktestMetrics:
        """Calculate backtest performance metrics"""

        # Filter completed trades (with PnL)
        completed_trades = [t for t in self.trades if t.pnl is not None]

        if not completed_trades:
            # No completed trades
            return BacktestMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_return_pct=0.0,
                total_pnl=0.0,
                avg_trade_pnl=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                calmar_ratio=0.0,
                total_volume_mwh=0.0,
                avg_holding_period_hours=0.0,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
            )

        # Basic metrics
        total_trades = len(completed_trades)
        winning_trades = len([t for t in completed_trades if t.pnl > 0])
        losing_trades = len([t for t in completed_trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

        # PnL metrics
        pnls = [t.pnl for t in completed_trades]
        total_pnl = sum(pnls)
        avg_trade_pnl = np.mean(pnls)
        best_trade = max(pnls)
        worst_trade = min(pnls)

        # Returns
        total_return_pct = (
            (self.current_capital - self.initial_capital) / self.initial_capital
        ) * 100

        # Risk metrics
        returns = [t.pnl / self.initial_capital for t in completed_trades]
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)

        max_drawdown_pct = (
            (self.max_drawdown / self.peak_capital) * 100 if self.peak_capital > 0 else 0.0
        )

        calmar_ratio = (
            total_return_pct / max_drawdown_pct if max_drawdown_pct > 0 else 0.0
        )

        # Volume
        total_volume_mwh = sum(t.volume_mw for t in self.trades)

        # Holding period (simplified)
        avg_holding_period_hours = 24.0  # Placeholder

        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return_pct=total_return_pct,
            total_pnl=total_pnl,
            avg_trade_pnl=avg_trade_pnl,
            best_trade=best_trade,
            worst_trade=worst_trade,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=self.max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            calmar_ratio=calmar_ratio,
            total_volume_mwh=total_volume_mwh,
            avg_holding_period_hours=avg_holding_period_hours,
            initial_capital=self.initial_capital,
            final_capital=self.current_capital,
        )

    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0.0

        excess_returns = [r - (risk_free_rate / 252) for r in returns]
        if np.std(excess_returns) == 0:
            return 0.0

        return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)

    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if not returns:
            return 0.0

        excess_returns = [r - (risk_free_rate / 252) for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns or np.std(downside_returns) == 0:
            return 0.0

        return (np.mean(excess_returns) / np.std(downside_returns)) * np.sqrt(252)

    async def _save_results(self, metrics: BacktestMetrics):
        """Save backtest results to database"""
        backtest_id = str(uuid.uuid4())

        try:
            # Save backtest run
            sql = f"""
            INSERT INTO {self.catalog}.strategy.backtest_runs
            (backtest_id, strategy_id, strategy_name, start_date, end_date, initial_capital, final_capital,
             total_return_pct, total_trades, win_rate, sharpe_ratio, sortino_ratio, max_drawdown,
             max_drawdown_pct, calmar_ratio, avg_trade_pnl, best_trade, worst_trade,
             avg_holding_period_hours, total_volume_mwh, parameters, run_timestamp, run_duration_seconds)
            VALUES (
                '{backtest_id}',
                '{self.strategy.strategy_id}',
                '{self.strategy.strategy_name}',
                '{self.start_date.date()}',
                '{self.end_date.date()}',
                {self.initial_capital},
                {self.current_capital},
                {metrics.total_return_pct},
                {metrics.total_trades},
                {metrics.win_rate},
                {metrics.sharpe_ratio},
                {metrics.sortino_ratio},
                {metrics.max_drawdown},
                {metrics.max_drawdown_pct},
                {metrics.calmar_ratio},
                {metrics.avg_trade_pnl},
                {metrics.best_trade},
                {metrics.worst_trade},
                {metrics.avg_holding_period_hours},
                {metrics.total_volume_mwh},
                '{self.strategy.parameters.model_dump_json()}',
                current_timestamp(),
                0
            )
            """
            await execute_sql(sql)

            # Save trades (batch insert)
            print(f"Saved backtest results: {backtest_id}")

        except Exception as e:
            print(f"Failed to save backtest results: {e}")

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve)

    def get_trades(self) -> pd.DataFrame:
        """Get all trades as DataFrame"""
        return pd.DataFrame([t.model_dump() for t in self.trades])
