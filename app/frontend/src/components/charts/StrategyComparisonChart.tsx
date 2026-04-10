import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useBacktestResults } from '@/api/hooks/apex';
import { BarChart, Bar, ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Award, Target, BarChart3 } from 'lucide-react';

interface StrategyComparisonChartProps {
  strategyType?: string | null;
  limit?: number;
}

export function StrategyComparisonChart({ strategyType: initialStrategyType = null, limit: initialLimit = 10 }: StrategyComparisonChartProps) {
  const [strategyType, setStrategyType] = useState<string>(initialStrategyType || 'all');
  const [limit, setLimit] = useState(initialLimit);

  const { data, isLoading, error } = useBacktestResults(strategyType === 'all' ? null : strategyType, limit);

  const strategies = data?.data || [];

  // Prepare comparison data
  const returnComparisonData = useMemo(() => {
    return strategies.map((s) => ({
      name: s.strategy_name.length > 20 ? s.strategy_name.substring(0, 17) + '...' : s.strategy_name,
      fullName: s.strategy_name,
      totalReturn: s.total_return_pct,
      backtest_id: s.backtest_id,
    }));
  }, [strategies]);

  const sharpeComparisonData = useMemo(() => {
    return strategies.map((s) => ({
      name: s.strategy_name.length > 20 ? s.strategy_name.substring(0, 17) + '...' : s.strategy_name,
      fullName: s.strategy_name,
      sharpe: s.sharpe_ratio,
      backtest_id: s.backtest_id,
    }));
  }, [strategies]);

  const winRateComparisonData = useMemo(() => {
    return strategies.map((s) => ({
      name: s.strategy_name.length > 20 ? s.strategy_name.substring(0, 17) + '...' : s.strategy_name,
      fullName: s.strategy_name,
      winRate: s.win_rate * 100,
      backtest_id: s.backtest_id,
    }));
  }, [strategies]);

  const drawdownComparisonData = useMemo(() => {
    return strategies.map((s) => ({
      name: s.strategy_name.length > 20 ? s.strategy_name.substring(0, 17) + '...' : s.strategy_name,
      fullName: s.strategy_name,
      maxDrawdown: Math.abs(s.max_drawdown_pct),
      backtest_id: s.backtest_id,
    }));
  }, [strategies]);

  // Risk-return scatter data
  const riskReturnData = useMemo(() => {
    return strategies.map((s) => ({
      name: s.strategy_name,
      risk: Math.abs(s.max_drawdown_pct),
      return: s.total_return_pct,
      sharpe: s.sharpe_ratio,
      backtest_id: s.backtest_id,
    }));
  }, [strategies]);

  // Radar chart data - normalize metrics to 0-100 scale
  const radarData = useMemo(() => {
    if (strategies.length === 0) return [];

    const maxReturn = Math.max(...strategies.map((s) => Math.abs(s.total_return_pct)), 1);
    const maxSharpe = Math.max(...strategies.map((s) => s.sharpe_ratio), 1);
    const maxWinRate = 100;
    const maxDrawdown = Math.max(...strategies.map((s) => Math.abs(s.max_drawdown_pct)), 1);
    const maxTrades = Math.max(...strategies.map((s) => s.total_trades), 1);

    return strategies.slice(0, 5).map((s) => ({
      strategy: s.strategy_name.length > 15 ? s.strategy_name.substring(0, 12) + '...' : s.strategy_name,
      'Total Return': (s.total_return_pct / maxReturn) * 100,
      'Sharpe Ratio': (s.sharpe_ratio / maxSharpe) * 100,
      'Win Rate': (s.win_rate * 100) / maxWinRate * 100,
      'Robustness': ((maxDrawdown - Math.abs(s.max_drawdown_pct)) / maxDrawdown) * 100, // Inverted - lower drawdown is better
      'Activity': (s.total_trades / maxTrades) * 100,
    }));
  }, [strategies]);

  // Find best performers
  const bestReturn = strategies.length > 0 ? strategies.reduce((max, s) => (s.total_return_pct > max.total_return_pct ? s : max)) : null;
  const bestSharpe = strategies.length > 0 ? strategies.reduce((max, s) => (s.sharpe_ratio > max.sharpe_ratio ? s : max)) : null;
  const bestWinRate = strategies.length > 0 ? strategies.reduce((max, s) => (s.win_rate > max.win_rate ? s : max)) : null;

  // Color scale for bars
  const getColorForValue = (value: number, isPositive: boolean = true) => {
    if (isPositive) {
      if (value >= 50) return '#10b981'; // green
      if (value >= 20) return '#3b82f6'; // blue
      if (value >= 0) return '#8b5cf6'; // purple
      return '#ef4444'; // red
    } else {
      if (value <= 10) return '#10b981'; // green for low drawdown
      if (value <= 20) return '#f59e0b'; // orange
      return '#ef4444'; // red
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading strategy comparison...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-red-400">Error loading strategy comparison</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (strategies.length === 0) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-gray-400">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No strategies to compare</p>
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
            <CardTitle className="text-xl text-gray-100">Strategy Comparison Dashboard</CardTitle>
            <div className="text-sm text-gray-400">Compare backtest performance across strategies</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Filter:</span>
              <Select value={strategyType} onValueChange={setStrategyType}>
                <SelectTrigger className="w-[180px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="all">All Strategies</SelectItem>
                  <SelectItem value="WEATHER_DRIVEN">Weather-Driven</SelectItem>
                  <SelectItem value="MEAN_REVERSION">Mean Reversion</SelectItem>
                  <SelectItem value="ARBITRAGE">Arbitrage</SelectItem>
                  <SelectItem value="MAINTENANCE_AWARE">Maintenance-Aware</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Limit:</span>
              <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
                <SelectTrigger className="w-[100px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Top Performers Summary */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {bestReturn && (
            <Card className="bg-gradient-to-br from-green-500/10 to-green-500/5 border-green-500/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="h-4 w-4 text-green-400" />
                  <div className="text-xs text-green-300 font-medium">Best Return</div>
                </div>
                <div className="text-sm text-gray-200 mb-1">{bestReturn.strategy_name}</div>
                <div className="text-2xl font-bold text-green-400">{bestReturn.total_return_pct >= 0 ? '+' : ''}{bestReturn.total_return_pct.toFixed(1)}%</div>
              </CardContent>
            </Card>
          )}
          {bestSharpe && (
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border-blue-500/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="h-4 w-4 text-blue-400" />
                  <div className="text-xs text-blue-300 font-medium">Best Sharpe</div>
                </div>
                <div className="text-sm text-gray-200 mb-1">{bestSharpe.strategy_name}</div>
                <div className="text-2xl font-bold text-blue-400">{bestSharpe.sharpe_ratio.toFixed(2)}</div>
              </CardContent>
            </Card>
          )}
          {bestWinRate && (
            <Card className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 border-purple-500/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-purple-400" />
                  <div className="text-xs text-purple-300 font-medium">Best Win Rate</div>
                </div>
                <div className="text-sm text-gray-200 mb-1">{bestWinRate.strategy_name}</div>
                <div className="text-2xl font-bold text-purple-400">{(bestWinRate.win_rate * 100).toFixed(1)}%</div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Multi-Metric Comparison Grid */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Total Return Comparison */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Total Return Comparison</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={returnComparisonData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Return (%)', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" style={{ fontSize: '11px' }} width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => [`${value.toFixed(2)}%`, props.payload.fullName]}
                />
                <Bar dataKey="totalReturn" name="Total Return">
                  {returnComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getColorForValue(entry.totalReturn)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Sharpe Ratio Comparison */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Sharpe Ratio Comparison</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={sharpeComparisonData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Sharpe Ratio', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" style={{ fontSize: '11px' }} width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => [value.toFixed(2), props.payload.fullName]}
                />
                <Bar dataKey="sharpe" name="Sharpe Ratio">
                  {sharpeComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.sharpe >= 1.5 ? '#10b981' : entry.sharpe >= 1.0 ? '#3b82f6' : '#f59e0b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Win Rate Comparison */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Win Rate Comparison</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={winRateComparisonData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Win Rate (%)', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" style={{ fontSize: '11px' }} width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => [`${value.toFixed(1)}%`, props.payload.fullName]}
                />
                <Bar dataKey="winRate" name="Win Rate">
                  {winRateComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.winRate >= 60 ? '#10b981' : entry.winRate >= 50 ? '#3b82f6' : '#f59e0b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Max Drawdown Comparison */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Max Drawdown Comparison</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={drawdownComparisonData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Max Drawdown (%)', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" style={{ fontSize: '11px' }} width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => [`-${value.toFixed(1)}%`, props.payload.fullName]}
                />
                <Bar dataKey="maxDrawdown" name="Max Drawdown">
                  {drawdownComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getColorForValue(entry.maxDrawdown, false)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk-Return Scatter Plot */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Risk-Return Profile</div>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                type="number"
                dataKey="risk"
                name="Risk (Max Drawdown %)"
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
                label={{ value: 'Risk - Max Drawdown (%)', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }}
              />
              <YAxis
                type="number"
                dataKey="return"
                name="Return (%)"
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
                label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                formatter={(value: any, name: string) => {
                  if (name === 'Risk (Max Drawdown %)') return [`${value.toFixed(1)}%`, name];
                  if (name === 'Return (%)') return [`${value.toFixed(1)}%`, name];
                  return [value, name];
                }}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''}
              />
              <Scatter name="Strategies" data={riskReturnData} fill="#8b5cf6">
                {riskReturnData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.sharpe >= 1.5 ? '#10b981' : entry.sharpe >= 1.0 ? '#3b82f6' : '#f59e0b'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="text-xs text-gray-500 mt-2">Optimal strategies: Top-left (high return, low risk)</div>
        </div>

        {/* Radar Chart - Top 5 Strategies */}
        {radarData.length > 0 && (
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Multi-Dimensional Performance (Top 5)</div>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="strategy" stroke="#9ca3af" style={{ fontSize: '11px' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" style={{ fontSize: '10px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any) => `${value.toFixed(0)}/100`}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Radar name="Total Return" dataKey="Total Return" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                <Radar name="Sharpe Ratio" dataKey="Sharpe Ratio" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                <Radar name="Win Rate" dataKey="Win Rate" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
                <Radar name="Robustness" dataKey="Robustness" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                <Radar name="Activity" dataKey="Activity" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 mt-2">All metrics normalized to 0-100 scale for comparison</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
