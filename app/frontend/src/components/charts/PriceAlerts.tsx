import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNEMWEBDailyPriceStats } from '@/api/hooks/apex';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';
import { Bell, AlertCircle, TrendingUp, TrendingDown, Activity, CheckCircle } from 'lucide-react';

interface PriceAlertsProps {
  regionId?: string;
  days?: number;
}

export function PriceAlerts({ regionId: initialRegionId = 'NSW1', days: initialDays = 7 }: PriceAlertsProps) {
  const [regionId, setRegionId] = useState(initialRegionId);
  const [days, setDays] = useState(initialDays);
  const [upperThreshold, setUpperThreshold] = useState(300);
  const [lowerThreshold, setLowerThreshold] = useState(50);

  const { data, isLoading, error } = useNEMWEBDailyPriceStats(regionId, days);

  const priceStats = data?.data || [];

  // Generate alerts based on thresholds
  const alerts = useMemo(() => {
    const generatedAlerts: Array<{
      id: string;
      date: string;
      type: 'HIGH' | 'LOW' | 'SPIKE' | 'NORMAL';
      severity: 'critical' | 'warning' | 'info';
      message: string;
      value: number;
      threshold?: number;
    }> = [];

    priceStats.forEach((stat, idx) => {
      const date = stat.price_date;
      const avgPrice = stat.avg_price;
      const maxPrice = stat.max_price;
      const minPrice = stat.min_price;
      const volatility = stat.price_volatility;

      // High price alert
      if (maxPrice > upperThreshold) {
        generatedAlerts.push({
          id: `high-${date}-${idx}`,
          date,
          type: 'HIGH',
          severity: maxPrice > upperThreshold * 1.5 ? 'critical' : 'warning',
          message: `Price exceeded ${upperThreshold} $/MWh`,
          value: maxPrice,
          threshold: upperThreshold,
        });
      }

      // Low price alert
      if (minPrice < lowerThreshold) {
        generatedAlerts.push({
          id: `low-${date}-${idx}`,
          date,
          type: 'LOW',
          severity: 'info',
          message: `Price below ${lowerThreshold} $/MWh`,
          value: minPrice,
          threshold: lowerThreshold,
        });
      }

      // Volatility spike alert
      if (volatility > 100) {
        generatedAlerts.push({
          id: `spike-${date}-${idx}`,
          date,
          type: 'SPIKE',
          severity: volatility > 200 ? 'critical' : 'warning',
          message: `High volatility detected`,
          value: volatility,
        });
      }
    });

    return generatedAlerts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [priceStats, upperThreshold, lowerThreshold]);

  // Count alerts by severity
  const criticalAlerts = alerts.filter((a) => a.severity === 'critical').length;
  const warningAlerts = alerts.filter((a) => a.severity === 'warning').length;
  const infoAlerts = alerts.filter((a) => a.severity === 'info').length;

  // Prepare chart data with alert markers
  const chartData = useMemo(() => {
    return [...priceStats].reverse().map((stat) => {
      const dayAlerts = alerts.filter((a) => a.date === stat.price_date);
      const hasHighAlert = dayAlerts.some((a) => a.type === 'HIGH');
      const hasLowAlert = dayAlerts.some((a) => a.type === 'LOW');
      const hasSpikeAlert = dayAlerts.some((a) => a.type === 'SPIKE');

      return {
        date: new Date(stat.price_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        fullDate: stat.price_date,
        avgPrice: stat.avg_price,
        maxPrice: stat.max_price,
        minPrice: stat.min_price,
        volatility: stat.price_volatility,
        hasHighAlert,
        hasLowAlert,
        hasSpikeAlert,
      };
    });
  }, [priceStats, alerts]);

  // Alert type icons
  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'HIGH':
        return TrendingUp;
      case 'LOW':
        return TrendingDown;
      case 'SPIKE':
        return Activity;
      default:
        return AlertCircle;
    }
  };

  // Alert severity colors
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/20 text-red-300 border-red-500/50';
      case 'warning':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50';
      case 'info':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/50';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/50';
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading price alerts...</div>
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
            <div className="text-red-400">Error loading price alerts</div>
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
            <CardTitle className="text-xl text-gray-100">Price Alert Monitor</CardTitle>
            <div className="text-sm text-gray-400">Real-time price threshold monitoring</div>
          </div>
          <div className="flex items-center gap-3">
            {alerts.length === 0 ? (
              <Badge className="bg-green-500/20 text-green-300 border-green-500/50 text-sm">
                <CheckCircle className="h-3 w-3 mr-1" />
                All Clear
              </Badge>
            ) : (
              <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-500/50 text-sm">
                <Bell className="h-3 w-3 mr-1" />
                {alerts.length} Active Alerts
              </Badge>
            )}
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
                  <SelectItem value="14">14 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Alert Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Total Alerts</div>
              <div className="text-2xl font-bold text-gray-100">{alerts.length}</div>
              <div className="text-xs text-gray-500">Last {days} days</div>
            </CardContent>
          </Card>
          <Card className={`bg-gray-800 ${criticalAlerts > 0 ? 'border-red-500/50' : 'border-gray-700'}`}>
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Critical</div>
              <div className="text-2xl font-bold text-red-400">{criticalAlerts}</div>
              <div className="text-xs text-gray-500">Immediate Action</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Warning</div>
              <div className="text-2xl font-bold text-yellow-400">{warningAlerts}</div>
              <div className="text-xs text-gray-500">Monitor Closely</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Info</div>
              <div className="text-2xl font-bold text-blue-400">{infoAlerts}</div>
              <div className="text-xs text-gray-500">For Awareness</div>
            </CardContent>
          </Card>
        </div>

        {/* Threshold Configuration */}
        <div className="mb-6 p-4 bg-gray-800 border border-gray-700 rounded-lg">
          <div className="text-sm font-medium text-gray-300 mb-3">Alert Thresholds</div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Upper Threshold ($/MWh)</label>
              <input
                type="number"
                value={upperThreshold}
                onChange={(e) => setUpperThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-gray-200 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Lower Threshold ($/MWh)</label>
              <input
                type="number"
                value={lowerThreshold}
                onChange={(e) => setLowerThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-gray-200 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Price Chart with Alert Markers */}
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-300 mb-3">Price Trend with Alert Zones</div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <defs>
                <linearGradient id="colorAlert" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
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
                formatter={(value: any, name: string) => [`$${value.toFixed(2)}/MWh`, name]}
              />
              {/* Alert zones */}
              <ReferenceArea y1={upperThreshold} y2={1000} fill="#ef4444" fillOpacity={0.1} />
              <ReferenceArea y1={0} y2={lowerThreshold} fill="#3b82f6" fillOpacity={0.1} />
              {/* Threshold lines */}
              <ReferenceLine y={upperThreshold} stroke="#ef4444" strokeDasharray="3 3" label={{ value: `Upper: $${upperThreshold}`, position: 'right', fill: '#ef4444', fontSize: 12 }} />
              <ReferenceLine y={lowerThreshold} stroke="#3b82f6" strokeDasharray="3 3" label={{ value: `Lower: $${lowerThreshold}`, position: 'right', fill: '#3b82f6', fontSize: 12 }} />
              {/* Price lines */}
              <Line type="monotone" dataKey="maxPrice" stroke="#ef4444" name="Max Price" strokeWidth={1} dot={false} strokeDasharray="2 2" />
              <Line type="monotone" dataKey="avgPrice" stroke="#3b82f6" name="Avg Price" strokeWidth={2} dot={(props: any) => {
                const hasAlert = props.payload.hasHighAlert || props.payload.hasLowAlert || props.payload.hasSpikeAlert;
                if (hasAlert) {
                  return (
                    <circle
                      cx={props.cx}
                      cy={props.cy}
                      r={6}
                      fill="#f59e0b"
                      stroke="#f59e0b"
                      strokeWidth={2}
                    />
                  );
                }
                return null;
              }} />
              <Line type="monotone" dataKey="minPrice" stroke="#10b981" name="Min Price" strokeWidth={1} dot={false} strokeDasharray="2 2" />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <span>Alert Triggered</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-2 bg-red-400 opacity-20"></div>
              <span>High Alert Zone</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-2 bg-blue-400 opacity-20"></div>
              <span>Low Alert Zone</span>
            </div>
          </div>
        </div>

        {/* Alert History */}
        <div>
          <div className="text-sm font-medium text-gray-300 mb-3">Alert History</div>
          {alerts.length === 0 ? (
            <div className="flex items-center justify-center h-32 bg-gray-800 border border-gray-700 rounded-lg">
              <div className="text-center text-gray-400">
                <CheckCircle className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p>No alerts triggered</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Date</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Message</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Value</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.slice(0, 10).map((alert) => {
                    const Icon = getAlertIcon(alert.type);
                    return (
                      <tr key={alert.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                        <td className="py-3 px-4 text-sm text-gray-300">{new Date(alert.date).toLocaleDateString()}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-300">{alert.type}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-300">{alert.message}</td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">
                          {alert.type === 'SPIKE' ? `${alert.value.toFixed(0)} StdDev` : `$${alert.value.toFixed(2)}/MWh`}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge className={`text-xs ${getSeverityColor(alert.severity)}`}>{alert.severity.toUpperCase()}</Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {alerts.length > 10 && <div className="text-xs text-gray-500 mt-2 text-center">Showing 10 of {alerts.length} alerts</div>}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
