import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePositions, useStressScenarios, useCreditExposure } from '@/api/hooks/apex';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, Shield, TrendingDown, Activity } from 'lucide-react';

interface RiskHeatmapProps {
  market?: 'NEM' | 'EPEX' | 'ERCOT';
  spotPrice?: number;
  volatility?: number;
}

export function RiskHeatmap({ market: initialMarket = 'NEM', spotPrice = 100, volatility = 25 }: RiskHeatmapProps) {
  const [market, setMarket] = useState<'NEM' | 'EPEX' | 'ERCOT'>(initialMarket);
  const [priceInput, setPriceInput] = useState(spotPrice);
  const [volatilityInput, setVolatilityInput] = useState(volatility);

  const { data: positionsData, isLoading: isLoadingPositions, error: positionsError } = usePositions();
  const { data: stressData, isLoading: isLoadingStress, error: stressError } = useStressScenarios(market, priceInput, volatilityInput);
  const { data: creditData, isLoading: isLoadingCredit, error: creditError } = useCreditExposure(market);

  const positions = positionsData?.data || [];
  const stressScenarios = stressData?.data || [];
  const creditExposure = creditData?.data || [];

  // Calculate aggregate risk metrics
  const totalExposure = positions.reduce((sum, p) => sum + Math.abs(p.net_position_mw), 0);
  const longExposure = positions.filter((p) => p.net_position_mw > 0).reduce((sum, p) => sum + p.net_position_mw, 0);
  const shortExposure = positions.filter((p) => p.net_position_mw < 0).reduce((sum, p) => sum + Math.abs(p.net_position_mw), 0);
  const netExposure = longExposure - shortExposure;

  // Calculate portfolio VaR (simplified)
  const portfolioValue = positions.reduce((sum, p) => sum + p.net_position_mw * p.avg_trade_price, 0);
  const var95 = Math.abs(portfolioValue) * (volatilityInput / 100) * 1.65; // 95% confidence
  const var99 = Math.abs(portfolioValue) * (volatilityInput / 100) * 2.33; // 99% confidence

  // Prepare position exposure data with color coding
  const exposureData = useMemo(() => {
    return positions.map((p) => ({
      instrument: p.instrument,
      exposure: p.net_position_mw,
      value: p.net_position_mw * p.avg_trade_price,
      avgPrice: p.avg_trade_price,
    }));
  }, [positions]);

  // Prepare heatmap data for positions (categorize by exposure level)
  const exposureHeatmap = useMemo(() => {
    const categories = [
      { label: 'Critical (>500 MW)', min: 500, max: Infinity, count: 0, totalMW: 0 },
      { label: 'High (200-500 MW)', min: 200, max: 500, count: 0, totalMW: 0 },
      { label: 'Medium (50-200 MW)', min: 50, max: 200, count: 0, totalMW: 0 },
      { label: 'Low (<50 MW)', min: 0, max: 50, count: 0, totalMW: 0 },
    ];

    positions.forEach((p) => {
      const absExposure = Math.abs(p.net_position_mw);
      for (const cat of categories) {
        if (absExposure >= cat.min && absExposure < cat.max) {
          cat.count++;
          cat.totalMW += absExposure;
          break;
        }
      }
    });

    return categories;
  }, [positions]);

  // Color function for exposure bars
  const getExposureColor = (exposure: number) => {
    if (exposure > 0) {
      // Long positions - shades of green
      if (exposure > 300) return '#ef4444'; // High long exposure - risky
      if (exposure > 100) return '#f59e0b'; // Medium long
      return '#10b981'; // Low long
    } else {
      // Short positions - shades of red/purple
      if (exposure < -300) return '#dc2626'; // High short exposure - risky
      if (exposure < -100) return '#7c3aed'; // Medium short
      return '#8b5cf6'; // Low short
    }
  };

  // Get risk level color
  const getRiskLevel = (value: number, threshold: { low: number; medium: number }) => {
    if (value > threshold.medium) return { label: 'High', color: 'bg-red-500/20 text-red-300 border-red-500/50' };
    if (value > threshold.low) return { label: 'Medium', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50' };
    return { label: 'Low', color: 'bg-green-500/20 text-green-300 border-green-500/50' };
  };

  const exposureRisk = getRiskLevel(totalExposure, { low: 500, medium: 1000 });
  const varRisk = getRiskLevel(var95, { low: 50000, medium: 100000 });

  if (isLoadingPositions || isLoadingStress || isLoadingCredit) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-400">Loading risk analysis...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (positionsError || stressError || creditError) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-red-400">Error loading risk data</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (positions.length === 0) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-gray-400">
              <Shield className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No positions to analyze</p>
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
            <CardTitle className="text-xl text-gray-100">Risk Exposure Dashboard</CardTitle>
            <div className="text-sm text-gray-400">Portfolio risk metrics and stress testing</div>
          </div>
          <div className="flex items-center gap-3">
            <Badge className={`text-sm ${exposureRisk.color}`}>
              {exposureRisk.label} Exposure
            </Badge>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Market:</span>
              <Select value={market} onValueChange={(v) => setMarket(v as 'NEM' | 'EPEX' | 'ERCOT')}>
                <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="NEM">NEM</SelectItem>
                  <SelectItem value="EPEX">EPEX</SelectItem>
                  <SelectItem value="ERCOT">ERCOT</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {/* Risk Summary Metrics */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Total Exposure</div>
              <div className="text-2xl font-bold text-blue-400">{totalExposure.toFixed(0)} MW</div>
              <div className="text-xs text-gray-500">Gross Position</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Net Exposure</div>
              <div className={`text-2xl font-bold ${netExposure >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {netExposure >= 0 ? '+' : ''}
                {netExposure.toFixed(0)} MW
              </div>
              <div className="text-xs text-gray-500">{netExposure >= 0 ? 'Long' : 'Short'}</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">Portfolio Value</div>
              <div className="text-2xl font-bold text-purple-400">${(portfolioValue / 1000).toFixed(0)}K</div>
              <div className="text-xs text-gray-500">Mark-to-Market</div>
            </CardContent>
          </Card>
          <Card className={`bg-gray-800 border-gray-700 ${var95 > 100000 ? 'border-red-500/50' : ''}`}>
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">VaR 95%</div>
              <div className={`text-2xl font-bold ${var95 > 100000 ? 'text-red-400' : var95 > 50000 ? 'text-yellow-400' : 'text-green-400'}`}>
                ${(var95 / 1000).toFixed(0)}K
              </div>
              <div className="text-xs text-gray-500">Daily Risk</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">VaR 99%</div>
              <div className="text-2xl font-bold text-red-400">${(var99 / 1000).toFixed(0)}K</div>
              <div className="text-xs text-gray-500">Extreme Risk</div>
            </CardContent>
          </Card>
        </div>

        {/* Exposure Breakdown */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Position Exposure Chart */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Position Exposure by Instrument</div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={exposureData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="instrument" stroke="#9ca3af" style={{ fontSize: '11px' }} angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Net Position (MW)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => {
                    if (name === 'Exposure') return [`${value.toFixed(0)} MW`, 'Net Position'];
                    return [value, name];
                  }}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      return `${label} @ $${payload[0].payload.avgPrice.toFixed(2)}/MWh`;
                    }
                    return label;
                  }}
                />
                <Bar dataKey="exposure" name="Exposure">
                  {exposureData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getExposureColor(entry.exposure)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-400"></div>
                <span>Long</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-purple-400"></div>
                <span>Short</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-400"></div>
                <span>High Risk</span>
              </div>
            </div>
          </div>

          {/* Exposure Heatmap Categories */}
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Exposure Distribution by Risk Level</div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={exposureHeatmap}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="label" stroke="#9ca3af" style={{ fontSize: '11px' }} angle={-20} textAnchor="end" height={80} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => {
                    if (name === 'Count') return [`${value} positions`, name];
                    if (name === 'Total MW') return [`${props.payload.totalMW.toFixed(0)} MW`, name];
                    return [value, name];
                  }}
                />
                <Bar dataKey="count" name="Count">
                  {exposureHeatmap.map((entry, index) => {
                    const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];
                    return <Cell key={`cell-${index}`} fill={colors[exposureHeatmap.length - 1 - index]} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 mt-2">Risk increases with exposure size</div>
          </div>
        </div>

        {/* Stress Scenarios */}
        {stressScenarios.length > 0 && (
          <div className="mb-6">
            <div className="text-sm font-medium text-gray-300 mb-3">Stress Test Scenarios</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stressScenarios}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="scenario" stroke="#9ca3af" style={{ fontSize: '11px' }} angle={-20} textAnchor="end" height={60} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Impact ($)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#f3f4f6',
                  }}
                  formatter={(value: any, name: string, props: any) => [`$${(value / 1000).toFixed(0)}K`, props.payload.shock]}
                />
                <Bar dataKey="impact" name="Impact">
                  {stressScenarios.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.impact < 0 ? '#ef4444' : '#10b981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 mt-2">Estimated portfolio impact under extreme scenarios</div>
          </div>
        )}

        {/* Credit Exposure */}
        {creditExposure.length > 0 && (
          <div>
            <div className="text-sm font-medium text-gray-300 mb-3">Credit Exposure by Counterparty</div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Counterparty</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Trades</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Gross MW</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">MTM PnL</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-gray-400">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {creditExposure.map((exposure, idx) => {
                    const riskLevel = Math.abs(exposure.gross_mw) > 500 ? 'High' : Math.abs(exposure.gross_mw) > 200 ? 'Medium' : 'Low';
                    const riskColor = riskLevel === 'High' ? 'bg-red-500/20 text-red-300' : riskLevel === 'Medium' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-green-500/20 text-green-300';

                    return (
                      <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800/50">
                        <td className="py-3 px-4 text-sm text-gray-200">{exposure.counterparty}</td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">{exposure.trades}</td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">{exposure.gross_mw.toFixed(0)} MW</td>
                        <td className={`py-3 px-4 text-right text-sm font-medium ${exposure.mtm_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ${(exposure.mtm_pnl / 1000).toFixed(0)}K
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge className={`text-xs ${riskColor}`}>{riskLevel}</Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
