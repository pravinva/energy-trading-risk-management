import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useStrategies } from '@/api/hooks/apex';
import { Activity, TrendingUp, Zap, Wrench, BarChart3 } from 'lucide-react';

const strategyIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  WEATHER_DRIVEN: TrendingUp,
  MEAN_REVERSION: BarChart3,
  ARBITRAGE: Activity,
  MAINTENANCE_AWARE: Wrench,
  TEMPORAL_ARBITRAGE: Zap,
};

const statusColors: Record<string, string> = {
  BACKTEST: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
  PAPER: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
  LIVE: 'bg-green-500/20 text-green-300 border-green-500/50',
  PAUSED: 'bg-gray-500/20 text-gray-300 border-gray-500/50',
  RETIRED: 'bg-red-500/20 text-red-300 border-red-500/50',
};

export function StrategyDashboard() {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data, isLoading, error } = useStrategies(statusFilter === 'all' ? null : statusFilter);

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-400">Loading strategies...</div>
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
            <div className="text-red-400">Error loading strategies</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const strategies = data?.data || [];

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader className="border-b border-gray-700">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl text-gray-100">Trading Strategies</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Filter by status:</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px] bg-gray-800 border-gray-700 text-gray-200">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="BACKTEST">Backtest</SelectItem>
                <SelectItem value="PAPER">Paper</SelectItem>
                <SelectItem value="LIVE">Live</SelectItem>
                <SelectItem value="PAUSED">Paused</SelectItem>
                <SelectItem value="RETIRED">Retired</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {strategies.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-gray-400">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No strategies found</p>
              {statusFilter !== 'all' && <p className="text-sm mt-1">Try changing the filter</p>}
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {strategies.map((strategy) => {
              const Icon = strategyIcons[strategy.strategy_type] || Activity;

              return (
                <Card key={strategy.strategy_id} className="bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                          <Icon className="h-5 w-5 text-blue-400" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-100 text-sm">{strategy.strategy_name}</div>
                          <div className="text-xs text-gray-400">{strategy.region_id}</div>
                        </div>
                      </div>
                      <Badge className={`text-xs ${statusColors[strategy.status] || 'bg-gray-500/20 text-gray-300 border-gray-500/50'}`}>{strategy.status}</Badge>
                    </div>

                    <div className="text-sm text-gray-400 mb-3 line-clamp-2">{strategy.description}</div>

                    <div className="flex items-center justify-between text-xs">
                      <div className="text-gray-500">
                        ID: <span className="text-gray-400">{strategy.strategy_id}</span>
                      </div>
                      <div className="text-gray-500">
                        Created: <span className="text-gray-400">{new Date(strategy.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
