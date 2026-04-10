import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useBacktestResults } from '@/api/hooks/apex';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';

export function BacktestResults() {
  const [strategyFilter, setStrategyFilter] = useState<string>('all');
  const [limit, setLimit] = useState<number>(10);

  const { data, isLoading, error } = useBacktestResults(strategyFilter === 'all' ? null : strategyFilter, limit);

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-400">Loading backtest results...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-red-400">Error loading backtest results</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const results = data?.data || [];

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl text-gray-100">Backtest Results</CardTitle>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Strategy:</span>
              <Select value={strategyFilter} onValueChange={setStrategyFilter}>
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
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {results.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-gray-400">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No backtest results found</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="p-4">
                  <div className="text-xs text-gray-400 mb-1">Best Sharpe</div>
                  <div className="text-2xl font-bold text-green-400">{Math.max(...results.map((r) => r.sharpe_ratio)).toFixed(2)}</div>
                </CardContent>
              </Card>
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="p-4">
                  <div className="text-xs text-gray-400 mb-1">Avg Win Rate</div>
                  <div className="text-2xl font-bold text-blue-400">{(results.reduce((sum, r) => sum + r.win_rate, 0) / results.length).toFixed(1)}%</div>
                </CardContent>
              </Card>
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="p-4">
                  <div className="text-xs text-gray-400 mb-1">Total Trades</div>
                  <div className="text-2xl font-bold text-gray-100">{results.reduce((sum, r) => sum + r.total_trades, 0).toLocaleString()}</div>
                </CardContent>
              </Card>
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="p-4">
                  <div className="text-xs text-gray-400 mb-1">Total PnL</div>
                  <div className={`text-2xl font-bold ${results.reduce((sum, r) => sum + r.total_pnl, 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ${results.reduce((sum, r) => sum + r.total_pnl, 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Strategy</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Trades</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Win Rate</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Return</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Sharpe</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Max DD</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result, idx) => (
                    <tr key={result.backtest_id} className={`border-b border-gray-800 hover:bg-gray-800/50 ${idx === 0 ? 'bg-blue-500/5' : ''}`}>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {idx === 0 && <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/50 text-xs">Best</Badge>}
                          <div>
                            <div className="text-sm text-gray-200">{result.strategy_name}</div>
                            <div className="text-xs text-gray-500">{result.backtest_id.substring(0, 8)}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right text-sm text-gray-300">{result.total_trades.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {result.win_rate >= 0.5 ? <TrendingUp className="h-3 w-3 text-green-400" /> : <TrendingDown className="h-3 w-3 text-red-400" />}
                          <span className={`text-sm ${result.win_rate >= 0.5 ? 'text-green-400' : 'text-red-400'}`}>{(result.win_rate * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`text-sm ${result.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>{result.total_return_pct >= 0 ? '+' : ''}{result.total_return_pct.toFixed(1)}%</span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Badge
                          className={`text-xs ${result.sharpe_ratio >= 1.5 ? 'bg-green-500/20 text-green-300 border-green-500/50' : result.sharpe_ratio >= 1.0 ? 'bg-blue-500/20 text-blue-300 border-blue-500/50' : 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50'}`}
                        >
                          {result.sharpe_ratio.toFixed(2)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right text-sm text-red-400">-{result.max_drawdown_pct.toFixed(1)}%</td>
                      <td className="py-3 px-4 text-right">
                        <span className={`text-sm font-medium ${result.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>${result.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
