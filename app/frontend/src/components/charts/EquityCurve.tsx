import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useEquityCurve, useBacktestTrades } from '@/api/hooks/apex';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot, ComposedChart } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

interface EquityCurveProps {
  backtestId: string;
  strategyName?: string;
  initialCapital?: number;
}

export function EquityCurve({ backtestId, strategyName = 'Strategy', initialCapital = 1000000 }: EquityCurveProps) {
  const { data: equityData, isLoading: isLoadingEquity, error: equityError } = useEquityCurve(backtestId);
  const { data: tradesData, isLoading: isLoadingTrades, error: tradesError } = useBacktestTrades(backtestId);

  const equityCurve = equityData?.data || [];
  const trades = tradesData?.data || [];

  // Calculate summary metrics
  const finalValue = equityCurve.length > 0 ? equityCurve[equityCurve.length - 1].portfolio_value : initialCapital;
  const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100;
  const maxDrawdown = equityCurve.length > 0 ? Math.min(...equityCurve.map((p) => p.drawdown_pct)) : 0;
  const totalPnL = equityCurve.length > 0 ? equityCurve[equityCurve.length - 1].total_pnl : 0;

  // Calculate win rate from trades
  const exitTrades = trades.filter((t) => t.pnl !== null && t.pnl !== undefined);
  const winningTrades = exitTrades.filter((t) => t.pnl! > 0);
  const winRate = exitTrades.length > 0 ? (winningTrades.length / exitTrades.length) * 100 : 0;

  // Calculate Sharpe ratio (simplified - assumes daily returns)
  const returns = useMemo(() => {
    if (equityCurve.length < 2) return [];
    const dailyReturns = [];
    for (let i = 1; i < equityCurve.length; i++) {
      const prevValue = equityCurve[i - 1].portfolio_value;
      const currValue = equityCurve[i].portfolio_value;
      const dailyReturn = (currValue - prevValue) / prevValue;
      dailyReturns.push(dailyReturn);
    }
    return dailyReturns;
  }, [equityCurve]);

  const sharpeRatio = useMemo(() => {
    if (returns.length === 0) return 0;
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
    const stdDev = Math.sqrt(variance);
    return stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // Annualized
  }, [returns]);

  // Prepare chart data
  const chartData = useMemo(() => {
    return equityCurve.map((point, idx) => ({
      date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      timestamp: point.timestamp,
      portfolioValue: point.portfolio_value,
      cash: point.cash,
      positionValue: point.position_value,
      totalPnL: point.total_pnl,
      drawdown: point.drawdown,
      drawdownPct: point.drawdown_pct,
      openPositions: point.open_positions,
    }));
  }, [equityCurve]);

  // Prepare trade markers for the chart
  const tradeMarkers = useMemo(() => {
    return trades
      .filter((t) => t.pnl !== null && t.pnl !== undefined)
      .map((trade) => {
        const dataPoint = chartData.find((d) => d.timestamp === trade.timestamp);
        return {
          date: new Date(trade.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          portfolioValue: trade.portfolio_value,
          action: trade.action,
          pnl: trade.pnl,
          isWin: trade.pnl! > 0,
        };
      });
  }, [trades, chartData]);

  if (isLoadingEquity || isLoadingTrades) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading equity curve...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (equityError || tradesError) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-red-400">Error loading equity curve</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (equityCurve.length === 0) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-gray-400">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No equity curve data available</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl text-gray-100">Equity Curve Analysis</CardTitle>
            <div className="text-sm text-gray-400">{strategyName} Backtest Performance</div>
          </div>
          <Badge className={`text-sm ${totalReturn >= 0 ? 'bg-green-500/20 text-green-300 border-green-500/50' : 'bg-red-500/20 text-red-300 border-red-500/50'}`}>
            {totalReturn >= 0 ? '+' : ''}
            {totalReturn.toFixed(2)}% Total Return
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Final Value</div>
              <div className="text-2xl font-bold text-blue-400">${(finalValue / 1000).toFixed(0)}K</div>
              <div className="text-xs text-gray-500">from ${(initialCapital / 1000).toFixed(0)}K</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Total PnL</div>
              <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalPnL >= 0 ? '+' : ''}${(totalPnL / 1000).toFixed(0)}K
              </div>
              <div className="text-xs text-gray-500">{totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Sharpe Ratio</div>
              <div className={`text-2xl font-bold ${sharpeRatio >= 1.5 ? 'text-green-400' : sharpeRatio >= 1.0 ? 'text-blue-400' : 'text-yellow-400'}`}>
                {sharpeRatio.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">Risk-Adjusted</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Max Drawdown</div>
              <div className="text-2xl font-bold text-red-400">{maxDrawdown.toFixed(2)}%</div>
              <div className="text-xs text-gray-500">Peak to Trough</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Win Rate</div>
              <div className={`text-2xl font-bold ${winRate >= 50 ? 'text-green-400' : 'text-yellow-400'}`}>{winRate.toFixed(1)}%</div>
              <div className="text-xs text-gray-500">
                {winningTrades.length}/{exitTrades.length} wins
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Equity Curve Chart */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Portfolio Value Over Time</div>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={chartData}>
              <defs>
                <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
                label={{ value: 'Portfolio Value ($)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value: any, name: string) => {
                  if (name === 'Portfolio Value') return [`$${(value / 1000).toFixed(2)}K`, name];
                  if (name === 'Total PnL') return [`$${(value / 1000).toFixed(2)}K`, name];
                  return [value, name];
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }} />
              <Area type="monotone" dataKey="portfolioValue" stroke="#3b82f6" fillOpacity={1} fill="url(#colorPortfolio)" name="Portfolio Value" strokeWidth={2} />
              <Line type="monotone" dataKey="totalPnL" stroke="#10b981" name="Total PnL" strokeWidth={0} dot={false} />
              {/* Trade markers */}
              {tradeMarkers.map((marker, idx) => (
                <ReferenceDot
                  key={idx}
                  x={marker.date}
                  y={marker.portfolioValue}
                  r={4}
                  fill={marker.isWin ? '#10b981' : '#ef4444'}
                  stroke={marker.isWin ? '#10b981' : '#ef4444'}
                  strokeWidth={2}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span>Winning Trade</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <span>Losing Trade</span>
            </div>
          </div>
        </div>

        {/* Drawdown Chart */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Drawdown Analysis</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Drawdown (%)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value: any) => [`${value.toFixed(2)}%`, 'Drawdown']}
              />
              <Area type="monotone" dataKey="drawdownPct" stroke="#ef4444" fillOpacity={1} fill="url(#colorDrawdown)" name="Drawdown %" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Portfolio Composition */}
        <div>
          <div className="text-sm font-medium text-gray-300 mb-3">Portfolio Composition</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
                label={{ value: 'Value ($)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value: any, name: string) => [`$${(value / 1000).toFixed(2)}K`, name]}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Area type="monotone" dataKey="cash" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} name="Cash" />
              <Area type="monotone" dataKey="positionValue" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} name="Position Value" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
