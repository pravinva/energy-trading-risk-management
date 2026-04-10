/**
 * Monte Carlo Simulation Visualization Suite
 *
 * Shows Monte Carlo simulations "in action":
 * 1. P&L Distribution Histogram with VaR markers
 * 2. Individual Simulation Paths
 * 3. Convergence Analysis
 * 4. Animated Path Drawing (optional)
 */
import React, { useState, useMemo, useEffect } from 'react';
import {
  ComposedChart,
  BarChart,
  LineChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
  Cell
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { PlayCircle, PauseCircle, RotateCcw } from 'lucide-react';


interface MonteCarloResult {
  var_95: number;
  var_99: number;
  cvar_95: number;
  cvar_99: number;
  mean_pnl: number;
  median_pnl: number;
  std_pnl: number;
  skewness: number;
  kurtosis: number;
  percentile_1: number;
  percentile_5: number;
  percentile_25: number;
  percentile_75: number;
  percentile_95: number;
  percentile_99: number;
  n_simulations: number;
  n_steps: number;
  pnl_distribution: number[];
  var_95_convergence: number[];
  mean_convergence: number[];
  paths?: SimulationPath[];
}

interface SimulationPath {
  path_id: number;
  prices: number[];
  returns: number[];
  final_pnl: number;
  max_drawdown: number;
  var_breach: boolean;
}

interface MonteCarloVisualizationProps {
  result: MonteCarloResult;
  spotPrice: number;
  exposure: number;
  height?: number;
}

export function MonteCarloVisualization({
  result,
  spotPrice,
  exposure,
  height = 400
}: MonteCarloVisualizationProps) {
  const [selectedTab, setSelectedTab] = useState<'distribution' | 'paths' | 'convergence'>('distribution');
  const [animatedPaths, setAnimatedPaths] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  // 1. P&L Distribution Data
  const distributionData = useMemo(() => {
    // Create histogram bins
    const numBins = 50;
    const min = Math.min(...result.pnl_distribution);
    const max = Math.max(...result.pnl_distribution);
    const binWidth = (max - min) / numBins;

    const bins: { range: string; count: number; pnl: number; color: string }[] = [];

    for (let i = 0; i < numBins; i++) {
      const binStart = min + i * binWidth;
      const binEnd = binStart + binWidth;
      const count = result.pnl_distribution.filter(
        p => p >= binStart && p < binEnd
      ).length;

      // Color bins: red for losses, green for gains
      const color = binStart < 0 ? '#ef4444' : '#10b981';

      bins.push({
        range: `${(binStart / 1000).toFixed(0)}k`,
        pnl: binStart,
        count,
        color
      });
    }

    return bins;
  }, [result.pnl_distribution]);

  // 2. Simulation Paths Data (show subset for performance)
  const pathsData = useMemo(() => {
    if (!result.paths || result.paths.length === 0) return [];

    // Show 50 representative paths
    const pathsToShow = result.paths.slice(0, 50);

    // Transform to chart format
    const maxSteps = Math.max(...pathsToShow.map(p => p.prices.length));
    const chartData: any[] = [];

    for (let step = 0; step < maxSteps; step++) {
      const dataPoint: any = { step };

      pathsToShow.forEach((path, idx) => {
        if (step < path.prices.length) {
          dataPoint[`path_${idx}`] = path.prices[step];
        }
      });

      chartData.push(dataPoint);
    }

    return { chartData, paths: pathsToShow };
  }, [result.paths]);

  // 3. Convergence Data
  const convergenceData = useMemo(() => {
    if (!result.var_95_convergence || result.var_95_convergence.length === 0) {
      return [];
    }

    return result.var_95_convergence.map((var95, idx) => ({
      simulation: idx * Math.floor(result.n_simulations / result.var_95_convergence.length),
      var_95: var95,
      mean: result.mean_convergence?.[idx] || 0
    }));
  }, [result.var_95_convergence, result.mean_convergence, result.n_simulations]);

  // Animation effect for path drawing
  useEffect(() => {
    if (isAnimating && animatedPaths < 50) {
      const timer = setTimeout(() => {
        setAnimatedPaths(prev => Math.min(prev + 1, 50));
      }, 100);
      return () => clearTimeout(timer);
    } else if (animatedPaths >= 50) {
      setIsAnimating(false);
    }
  }, [isAnimating, animatedPaths]);

  const handlePlayAnimation = () => {
    setAnimatedPaths(0);
    setIsAnimating(true);
  };

  const handlePauseAnimation = () => {
    setIsAnimating(false);
  };

  const handleResetAnimation = () => {
    setAnimatedPaths(0);
    setIsAnimating(false);
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">VaR 95%</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              ${(result.var_95 / 1000).toFixed(1)}k
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Maximum expected loss (95% confidence)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">CVaR 95%</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">
              ${(result.cvar_95 / 1000).toFixed(1)}k
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Average loss beyond VaR
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Mean P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${result.mean_pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${(result.mean_pnl / 1000).toFixed(1)}k
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Expected P&L
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Simulations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {result.n_simulations.toLocaleString()}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {result.n_steps} steps each
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setSelectedTab('distribution')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            selectedTab === 'distribution'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          P&L Distribution
        </button>
        <button
          onClick={() => setSelectedTab('paths')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            selectedTab === 'paths'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Simulation Paths
        </button>
        <button
          onClick={() => setSelectedTab('convergence')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            selectedTab === 'convergence'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Convergence Analysis
        </button>
      </div>

      {/* Tab Content */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>
                {selectedTab === 'distribution' && 'P&L Distribution'}
                {selectedTab === 'paths' && 'Monte Carlo Simulation Paths'}
                {selectedTab === 'convergence' && 'VaR Convergence'}
              </CardTitle>
              <p className="text-sm text-gray-500 mt-1">
                {selectedTab === 'distribution' && `${result.n_simulations.toLocaleString()} simulations | Spot: $${spotPrice}/MWh | Exposure: ${exposure} MW`}
                {selectedTab === 'paths' && `Showing ${Math.min(50, result.paths?.length || 0)} of ${result.n_simulations.toLocaleString()} paths`}
                {selectedTab === 'convergence' && 'VaR estimate stability as simulations increase'}
              </p>
            </div>

            {selectedTab === 'paths' && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={isAnimating ? handlePauseAnimation : handlePlayAnimation}
                >
                  {isAnimating ? <PauseCircle className="w-4 h-4 mr-1" /> : <PlayCircle className="w-4 h-4 mr-1" />}
                  {isAnimating ? 'Pause' : 'Animate'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleResetAnimation}
                >
                  <RotateCcw className="w-4 h-4 mr-1" />
                  Reset
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* 1. Distribution Chart */}
          {selectedTab === 'distribution' && (
            <ResponsiveContainer width="100%" height={height}>
              <ComposedChart data={distributionData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="range"
                  label={{ value: 'P&L ($k)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: 'Frequency', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length > 0) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border border-gray-300 rounded shadow">
                          <p className="font-medium">P&L: {data.range}</p>
                          <p className="text-sm">Count: {data.count}</p>
                          <p className="text-sm">Probability: {((data.count / result.n_simulations) * 100).toFixed(2)}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count">
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} opacity={0.8} />
                  ))}
                </Bar>

                {/* VaR Lines */}
                <ReferenceLine
                  x={distributionData.find(d => d.pnl >= -result.var_95)?.range || ''}
                  stroke="#ef4444"
                  strokeWidth={2}
                  label={{ value: 'VaR 95%', position: 'top', fill: '#ef4444' }}
                />
                <ReferenceLine
                  x={distributionData.find(d => d.pnl >= -result.var_99)?.range || ''}
                  stroke="#991b1b"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{ value: 'VaR 99%', position: 'top', fill: '#991b1b' }}
                />
                <ReferenceLine
                  x={distributionData.find(d => d.pnl >= 0)?.range || ''}
                  stroke="#6b7280"
                  strokeDasharray="3 3"
                  label={{ value: 'Break-even', position: 'top' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}

          {/* 2. Paths Chart */}
          {selectedTab === 'paths' && pathsData.chartData && (
            <ResponsiveContainer width="100%" height={height}>
              <LineChart data={pathsData.chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="step"
                  label={{ value: 'Time Steps (Days)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: 'Price ($/MWh)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />

                {/* Starting price reference */}
                <ReferenceLine
                  y={spotPrice}
                  stroke="#6b7280"
                  strokeDasharray="5 5"
                  label={{ value: `Spot: $${spotPrice}`, position: 'right' }}
                />

                {/* Draw paths (animated if enabled) */}
                {pathsData.paths.slice(0, animatedPaths || 50).map((path, idx) => (
                  <Line
                    key={`path_${idx}`}
                    type="monotone"
                    dataKey={`path_${idx}`}
                    stroke={path.var_breach ? '#ef4444' : '#3b82f6'}
                    strokeWidth={0.5}
                    dot={false}
                    opacity={0.3}
                    isAnimationActive={isAnimating}
                    animationDuration={500}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}

          {/* 3. Convergence Chart */}
          {selectedTab === 'convergence' && (
            <ResponsiveContainer width="100%" height={height}>
              <LineChart data={convergenceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="simulation"
                  label={{ value: 'Number of Simulations', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: 'VaR 95% Estimate ($)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="var_95"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="VaR 95%"
                  dot={false}
                />
                <ReferenceLine
                  y={result.var_95}
                  stroke="#991b1b"
                  strokeDasharray="5 5"
                  label={{ value: `Final: $${(result.var_95/1000).toFixed(1)}k`, position: 'right' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}

          {/* Insights */}
          <div className="mt-4 p-4 bg-gray-50 rounded">
            {selectedTab === 'distribution' && (
              <div className="space-y-2 text-sm">
                <h4 className="font-semibold">Distribution Insights:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• <strong>Skewness:</strong> {result.skewness.toFixed(2)} {result.skewness > 0 ? '(right-skewed, tail risk on upside)' : '(left-skewed, tail risk on downside)'}</li>
                  <li>• <strong>Kurtosis:</strong> {result.kurtosis.toFixed(2)} {result.kurtosis > 3 ? '(fat tails, higher extreme event probability)' : '(thin tails, fewer extreme events)'}</li>
                  <li>• <strong>Probability of Loss:</strong> {((result.pnl_distribution.filter(p => p < 0).length / result.n_simulations) * 100).toFixed(1)}%</li>
                  <li>• <strong>Probability of Loss > VaR 95%:</strong> 5.0% (by definition)</li>
                </ul>
              </div>
            )}

            {selectedTab === 'paths' && (
              <div className="space-y-2 text-sm">
                <h4 className="font-semibold">Path Analysis:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• <strong>Red paths:</strong> Scenarios exceeding VaR 95% (worst 5%)</li>
                  <li>• <strong>Blue paths:</strong> Normal scenarios within confidence interval</li>
                  <li>• <strong>Paths breaching VaR:</strong> {pathsData.paths?.filter(p => p.var_breach).length || 0} of {pathsData.paths?.length || 0} shown</li>
                  <li>• <strong>Animation:</strong> Click "Animate" to see paths drawn sequentially</li>
                </ul>
              </div>
            )}

            {selectedTab === 'convergence' && (
              <div className="space-y-2 text-sm">
                <h4 className="font-semibold">Convergence Insights:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• VaR estimate stabilizes as more simulations are added</li>
                  <li>• Final VaR 95%: ${(result.var_95/1000).toFixed(1)}k (with {result.n_simulations.toLocaleString()} simulations)</li>
                  <li>• Well-converged estimates require 10,000+ simulations</li>
                  <li>• Line flattening indicates estimate confidence</li>
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default MonteCarloVisualization;
