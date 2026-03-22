import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNEMWEBDailyPriceStats } from '@/api/hooks/apex';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PriceChartProps {
  regionId?: string;
  days?: number;
}

export function PriceChart({ regionId: initialRegionId = 'NSW1', days: initialDays = 30 }: PriceChartProps) {
  const [regionId, setRegionId] = useState(initialRegionId);
  const [days, setDays] = useState(initialDays);

  const { data, isLoading, error } = useNEMWEBDailyPriceStats(regionId, days);

  const priceStats = data?.data || [];

  // Calculate summary stats
  const avgPrice = priceStats.length > 0 ? priceStats.reduce((sum, p) => sum + p.avg_price, 0) / priceStats.length : 0;
  const maxPrice = priceStats.length > 0 ? Math.max(...priceStats.map((p) => p.max_price)) : 0;
  const minPrice = priceStats.length > 0 ? Math.min(...priceStats.map((p) => p.min_price)) : 0;
  const avgVolatility = priceStats.length > 0 ? priceStats.reduce((sum, p) => sum + p.price_volatility, 0) / priceStats.length : 0;

  // Prepare chart data (reverse to show oldest first)
  const chartData = [...priceStats].reverse().map((stat) => ({
    date: new Date(stat.price_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    avgPrice: stat.avg_price,
    minPrice: stat.min_price,
    maxPrice: stat.max_price,
    medianPrice: stat.median_price,
    p95Price: stat.p95_price,
    demand: stat.avg_demand_mw,
  }));

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading price chart...</div>
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
            <div className="text-red-400">Error loading price chart</div>
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
            <CardTitle className="text-xl text-gray-100">Historical Price Analysis</CardTitle>
            <div className="text-sm text-gray-400">Daily price statistics and trends</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Region:</span>
              <Select value={regionId} onValueChange={setRegionId}>
                <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="NSW1">NSW1</SelectItem>
                  <SelectItem value="VIC1">VIC1</SelectItem>
                  <SelectItem value="QLD1">QLD1</SelectItem>
                  <SelectItem value="SA1">SA1</SelectItem>
                  <SelectItem value="TAS1">TAS1</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Period:</span>
              <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v))}>
                <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="60">60 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Avg Price</div>
              <div className="text-2xl font-bold text-blue-400">${avgPrice.toFixed(2)}</div>
              <div className="text-xs text-gray-500">/MWh</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Price Range</div>
              <div className="text-2xl font-bold text-gray-100">
                ${minPrice.toFixed(0)} - ${maxPrice.toFixed(0)}
              </div>
              <div className="text-xs text-gray-500">/MWh</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Avg Volatility</div>
              <div className="text-2xl font-bold text-yellow-400">${avgVolatility.toFixed(2)}</div>
              <div className="text-xs text-gray-500">StdDev</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Data Points</div>
              <div className="text-2xl font-bold text-gray-100">{priceStats.length}</div>
              <div className="text-xs text-gray-500">days</div>
            </CardContent>
          </Card>
        </div>

        {/* Price Chart */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Price Trends (Avg, Min, Max)</div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: '$/MWh', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }} />
              <Area type="monotone" dataKey="maxPrice" stroke="#ef4444" fill="none" name="Max Price" strokeWidth={1} strokeDasharray="3 3" />
              <Area type="monotone" dataKey="avgPrice" stroke="#3b82f6" fillOpacity={1} fill="url(#colorAvg)" name="Avg Price" strokeWidth={2} />
              <Area type="monotone" dataKey="minPrice" stroke="#10b981" fill="none" name="Min Price" strokeWidth={1} strokeDasharray="3 3" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Median vs P95 Chart */}
        <div>
          <div className="text-sm font-medium text-gray-300 mb-3">Distribution (Median vs P95)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: '$/MWh', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line type="monotone" dataKey="medianPrice" stroke="#8b5cf6" name="Median Price" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="p95Price" stroke="#f59e0b" name="P95 Price" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
