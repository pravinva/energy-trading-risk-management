import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNEMWEBForecastAccuracy } from '@/api/hooks/apex';
import { LineChart, Line, ScatterChart, Scatter, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Target, TrendingUp, Activity } from 'lucide-react';

interface ForecastAccuracyChartProps {
  regionId?: string;
  days?: number;
}

export function ForecastAccuracyChart({ regionId: initialRegionId = 'NSW1', days: initialDays = 30 }: ForecastAccuracyChartProps) {
  const [regionId, setRegionId] = useState(initialRegionId);
  const [days, setDays] = useState(initialDays);

  const { data, isLoading, error } = useNEMWEBForecastAccuracy(regionId, days);

  const accuracyData = data?.data || [];

  // Calculate summary metrics
  const avgMAE = accuracyData.length > 0 ? accuracyData.reduce((sum, d) => sum + d.mae, 0) / accuracyData.length : 0;
  const avgMAPE = accuracyData.length > 0 ? accuracyData.reduce((sum, d) => sum + d.mape, 0) / accuracyData.length : 0;
  const avgRMSE = accuracyData.length > 0 ? accuracyData.reduce((sum, d) => sum + d.rmse, 0) / accuracyData.length : 0;
  const avgCorrelation = accuracyData.length > 0 ? accuracyData.reduce((sum, d) => sum + d.correlation, 0) / accuracyData.length : 0;

  // Prepare chart data
  const forecastVsActualData = useMemo(() => {
    return [...accuracyData].reverse().map((point) => ({
      date: new Date(point.forecast_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      forecast: point.avg_forecast_price,
      actual: point.avg_actual_price,
      error: point.avg_forecast_price - point.avg_actual_price,
      mae: point.mae,
      mape: point.mape,
    }));
  }, [accuracyData]);

  // Prepare scatter data for correlation plot
  const scatterData = useMemo(() => {
    return accuracyData.map((point) => ({
      forecast: point.avg_forecast_price,
      actual: point.avg_actual_price,
    }));
  }, [accuracyData]);

  // Prepare error distribution data
  const errorDistribution = useMemo(() => {
    const errors = forecastVsActualData.map((d) => d.error);
    const binSize = 10;
    const bins: Record<string, number> = {};

    errors.forEach((error) => {
      const bin = Math.floor(error / binSize) * binSize;
      const binKey = `${bin}`;
      bins[binKey] = (bins[binKey] || 0) + 1;
    });

    return Object.entries(bins)
      .map(([bin, count]) => ({
        bin: `${bin} to ${parseInt(bin) + binSize}`,
        binValue: parseInt(bin),
        count,
      }))
      .sort((a, b) => a.binValue - b.binValue);
  }, [forecastVsActualData]);

  // Determine accuracy rating
  const getAccuracyRating = (mape: number) => {
    if (mape < 10) return { label: 'Excellent', color: 'bg-green-500/20 text-green-300 border-green-500/50' };
    if (mape < 20) return { label: 'Good', color: 'bg-blue-500/20 text-blue-300 border-blue-500/50' };
    if (mape < 30) return { label: 'Fair', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50' };
    return { label: 'Poor', color: 'bg-red-500/20 text-red-300 border-red-500/50' };
  };

  const accuracyRating = getAccuracyRating(avgMAPE);

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading forecast accuracy...</div>
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
            <div className="text-red-400">Error loading forecast accuracy</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (accuracyData.length === 0) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-gray-400">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No forecast accuracy data available</p>
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
            <CardTitle className="text-xl text-gray-100">Forecast Accuracy Analysis</CardTitle>
            <div className="text-sm text-gray-400">Pre-dispatch forecast vs actual prices</div>
          </div>
          <div className="flex items-center gap-3">
            <Badge className={`text-sm ${accuracyRating.color}`}>{accuracyRating.label} Accuracy</Badge>
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
        {/* Summary Metrics */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">MAE (Mean Absolute Error)</div>
              <div className="text-2xl font-bold text-blue-400">${avgMAE.toFixed(2)}</div>
              <div className="text-xs text-gray-500">/MWh</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">MAPE (Mean Absolute % Error)</div>
              <div className={`text-2xl font-bold ${avgMAPE < 15 ? 'text-green-400' : avgMAPE < 25 ? 'text-yellow-400' : 'text-red-400'}`}>
                {avgMAPE.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500">Lower is better</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">RMSE (Root Mean Square Error)</div>
              <div className="text-2xl font-bold text-purple-400">${avgRMSE.toFixed(2)}</div>
              <div className="text-xs text-gray-500">/MWh</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Correlation</div>
              <div className={`text-2xl font-bold ${avgCorrelation >= 0.9 ? 'text-green-400' : avgCorrelation >= 0.7 ? 'text-blue-400' : 'text-yellow-400'}`}>
                {avgCorrelation.toFixed(3)}
              </div>
              <div className="text-xs text-gray-500">1.0 = Perfect</div>
            </CardContent>
          </Card>
        </div>

        {/* Forecast vs Actual Chart */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Forecast vs Actual Prices</div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastVsActualData}>
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
                formatter={(value: any, name: string) => {
                  if (name === 'Forecast' || name === 'Actual') return [`$${value.toFixed(2)}/MWh`, name];
                  if (name === 'Error') return [`$${value.toFixed(2)}`, name];
                  return [value, name];
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line type="monotone" dataKey="forecast" stroke="#3b82f6" name="Forecast" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="actual" stroke="#10b981" name="Actual" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Grid for Scatter and Error Distribution */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Correlation Scatter Plot */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Forecast vs Actual Correlation</div>
            <ResponsiveContainer width="100%" height={250}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  type="number"
                  dataKey="forecast"
                  name="Forecast"
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  label={{ value: 'Forecast ($/MWh)', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }}
                />
                <YAxis
                  type="number"
                  dataKey="actual"
                  name="Actual"
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  label={{ value: 'Actual ($/MWh)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string) => [`$${value.toFixed(2)}`, name]}
                />
                <Scatter name="Forecast vs Actual" data={scatterData} fill="#8b5cf6" />
                {/* Perfect prediction line */}
                <Line
                  type="monotone"
                  dataKey="actual"
                  data={scatterData}
                  stroke="#6b7280"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Perfect Prediction"
                />
              </ScatterChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 mt-2">Points closer to diagonal = better accuracy</div>
          </div>

          {/* Error Distribution */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Forecast Error Distribution</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={errorDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="bin" stroke="#9ca3af" style={{ fontSize: '11px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any) => [`${value} days`, 'Count']}
                />
                <Bar dataKey="count" name="Frequency">
                  {errorDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.binValue === 0 ? '#10b981' : entry.binValue > 0 ? '#3b82f6' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 mt-2">Distribution of forecast errors ($/MWh)</div>
          </div>
        </div>

        {/* Error Metrics Over Time */}
        <div>
          <div className="text-sm font-medium text-gray-300 mb-3">Error Metrics Trend</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={forecastVsActualData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Error', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6',
                }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value: any, name: string) => {
                  if (name === 'MAE') return [`$${value.toFixed(2)}`, name];
                  if (name === 'MAPE') return [`${value.toFixed(2)}%`, name];
                  return [value, name];
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line type="monotone" dataKey="mae" stroke="#f59e0b" name="MAE" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="mape" stroke="#8b5cf6" name="MAPE (%)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
