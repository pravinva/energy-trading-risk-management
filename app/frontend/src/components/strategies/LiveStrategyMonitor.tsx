import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useStrategySignals, useStrategyPositions } from '@/api/hooks/apex';
import { TrendingUp, TrendingDown, Activity, CheckCircle, XCircle, Clock } from 'lucide-react';

export function LiveStrategyMonitor() {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all');
  const [signalHours, setSignalHours] = useState<number>(24);

  const { data: signalsData, isLoading: signalsLoading } = useStrategySignals(selectedStrategy === 'all' ? null : selectedStrategy, signalHours);
  const { data: positionsData, isLoading: positionsLoading } = useStrategyPositions(selectedStrategy === 'all' ? null : selectedStrategy);

  const signals = signalsData?.data || [];
  const positions = positionsData?.data || [];

  const actionColors: Record<string, string> = {
    BUY: 'bg-green-500/20 text-green-300 border-green-500/50',
    SELL: 'bg-red-500/20 text-red-300 border-red-500/50',
    HOLD: 'bg-gray-500/20 text-gray-300 border-gray-500/50',
  };

  const totalPnL = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const totalExposure = positions.reduce((sum, p) => sum + p.volume_mw, 0);

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl text-gray-100">Live Strategy Monitor</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Strategy:</span>
            <Select value={selectedStrategy} onValueChange={setSelectedStrategy}>
              <SelectTrigger className="w-[180px] bg-gray-800 border-gray-700 text-gray-200">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="all">All Strategies</SelectItem>
                <SelectItem value="weather-001">Weather-Driven</SelectItem>
                <SelectItem value="mean-rev-001">Mean Reversion</SelectItem>
                <SelectItem value="arbitrage-001">Arbitrage</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Open Positions</div>
              <div className="text-2xl font-bold text-gray-100">{positions.length}</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Total Exposure</div>
              <div className="text-2xl font-bold text-blue-400">{totalExposure.toFixed(0)} MW</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Unrealized PnL</div>
              <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>${totalPnL.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Signals (24h)</div>
              <div className="text-2xl font-bold text-gray-100">{signals.length}</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="signals" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-800">
            <TabsTrigger value="signals">Signals</TabsTrigger>
            <TabsTrigger value="positions">Positions</TabsTrigger>
          </TabsList>

          {/* Signals Tab */}
          <TabsContent value="signals" className="mt-4">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm text-gray-400">{signals.length} signals in last {signalHours}h</div>
              <Select value={signalHours.toString()} onValueChange={(v) => setSignalHours(parseInt(v))}>
                <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="1">1 hour</SelectItem>
                  <SelectItem value="6">6 hours</SelectItem>
                  <SelectItem value="24">24 hours</SelectItem>
                  <SelectItem value="168">7 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {signalsLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="text-gray-400">Loading signals...</div>
              </div>
            ) : signals.length === 0 ? (
              <div className="flex items-center justify-center h-48">
                <div className="text-center text-gray-400">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No signals found</p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {signals.map((signal) => (
                  <Card key={signal.signal_id} className="bg-gray-800 border-gray-700">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge className={actionColors[signal.action] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'}>{signal.action}</Badge>
                          <span className="text-sm text-gray-300">
                            {signal.volume_mw.toFixed(0)} MW @ {signal.instrument}
                          </span>
                          {signal.executed ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Clock className="h-4 w-4 text-yellow-400" />}
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <div className="text-xs text-gray-400">{new Date(signal.timestamp).toLocaleTimeString()}</div>
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-gray-500">Confidence:</span>
                            <span className={`text-xs font-medium ${signal.confidence >= 0.8 ? 'text-green-400' : signal.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'}`}>{(signal.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-400 line-clamp-2">{signal.reasoning}</div>
                      <div className="flex items-center justify-between mt-2 text-xs">
                        <div className="text-gray-500">
                          Strategy: <span className="text-gray-400">{signal.strategy_id}</span>
                        </div>
                        <div className="text-gray-500">
                          Type: <span className="text-gray-400">{signal.signal_type}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Positions Tab */}
          <TabsContent value="positions" className="mt-4">
            <div className="text-sm text-gray-400 mb-4">{positions.length} open positions</div>

            {positionsLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="text-gray-400">Loading positions...</div>
              </div>
            ) : positions.length === 0 ? (
              <div className="flex items-center justify-center h-48">
                <div className="text-center text-gray-400">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No open positions</p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Instrument</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Entry Price</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Volume (MW)</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Unrealized PnL</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position) => (
                      <tr key={position.position_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="text-sm text-gray-200">{position.instrument}</div>
                            <div className="text-xs text-gray-500">{position.position_id.substring(0, 8)}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">${position.entry_price.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">{position.volume_mw.toFixed(0)}</td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {position.unrealized_pnl >= 0 ? <TrendingUp className="h-3 w-3 text-green-400" /> : <TrendingDown className="h-3 w-3 text-red-400" />}
                            <span className={`text-sm font-medium ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>${position.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge className="bg-green-500/20 text-green-300 border-green-500/50 text-xs">{position.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
