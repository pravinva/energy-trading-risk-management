/**
 * Efficient Frontier Visualization Component
 *
 * Displays the efficient frontier for portfolio optimization
 * Shows risk-return tradeoff and highlights max Sharpe and min variance portfolios
 */
import React, { useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label,
  ReferenceLine
} from 'recharts';
import {  Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';


interface PortfolioMetrics {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  var_95: number;
  cvar_95: number;
  max_drawdown: number;
  weights: Record<string, number>;
}

interface EfficientFrontierData {
  portfolios: PortfolioMetrics[];
  max_sharpe_idx: number;
  min_vol_idx: number;
}

interface EfficientFrontierChartProps {
  data: EfficientFrontierData;
  currentPortfolio?: PortfolioMetrics;
  height?: number;
}


const EfficientFrontierChart: React.FC<EfficientFrontierChartProps> = ({
  data,
  currentPortfolio,
  height = 500
}) => {
  // Transform data for charting
  const chartData = useMemo(() => {
    const frontier = data.portfolios.map((p, idx) => ({
      volatility: p.volatility * 100, // Convert to percentage
      return: p.expected_return * 100,
      sharpe: p.sharpe_ratio,
      weights: p.weights,
      isMaxSharpe: idx === data.max_sharpe_idx,
      isMinVol: idx === data.min_vol_idx,
      type: 'frontier'
    }));

    // Add current portfolio if provided
    if (currentPortfolio) {
      frontier.push({
        volatility: currentPortfolio.volatility * 100,
        return: currentPortfolio.expected_return * 100,
        sharpe: currentPortfolio.sharpe_ratio,
        weights: currentPortfolio.weights,
        isMaxSharpe: false,
        isMinVol: false,
        type: 'current'
      });
    }

    return frontier;
  }, [data, currentPortfolio]);

  // Get key portfolios
  const maxSharpePortfolio = data.portfolios[data.max_sharpe_idx];
  const minVolPortfolio = data.portfolios[data.min_vol_idx];

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length > 0) {
      const p = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold mb-2">
            {p.type === 'current' ? 'Current Portfolio' :
             p.isMaxSharpe ? 'Max Sharpe Portfolio' :
             p.isMinVol ? 'Min Volatility Portfolio' :
             'Frontier Portfolio'}
          </p>
          <p className="text-sm">Return: <span className="font-medium">{p.return.toFixed(2)}%</span></p>
          <p className="text-sm">Volatility: <span className="font-medium">{p.volatility.toFixed(2)}%</span></p>
          <p className="text-sm">Sharpe Ratio: <span className="font-medium">{p.sharpe.toFixed(2)}</span></p>

          <div className="mt-3 pt-3 border-t">
            <p className="text-sm font-semibold mb-1">Allocation:</p>
            {Object.entries(p.weights)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([strategy, weight]) => (
                <p key={strategy} className="text-xs">
                  {strategy}: <span className="font-medium">{((weight as number) * 100).toFixed(1)}%</span>
                </p>
              ))
            }
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Efficient Frontier</CardTitle>
        <p className="text-sm text-gray-500">
          Risk-Return Tradeoff for Portfolio Allocation
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-6">
          {/* Max Sharpe Portfolio Card */}
          <div className="p-4 bg-green-50 border border-green-200 rounded">
            <h4 className="text-sm font-semibold text-green-800 mb-2">Max Sharpe Ratio</h4>
            <p className="text-xs text-gray-600">Return: <span className="font-medium">{(maxSharpePortfolio.expected_return * 100).toFixed(2)}%</span></p>
            <p className="text-xs text-gray-600">Risk: <span className="font-medium">{(maxSharpePortfolio.volatility * 100).toFixed(2)}%</span></p>
            <p className="text-xs text-gray-600">Sharpe: <span className="font-medium text-green-700">{maxSharpePortfolio.sharpe_ratio.toFixed(2)}</span></p>
          </div>

          {/* Min Volatility Portfolio Card */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">Min Volatility</h4>
            <p className="text-xs text-gray-600">Return: <span className="font-medium">{(minVolPortfolio.expected_return * 100).toFixed(2)}%</span></p>
            <p className="text-xs text-gray-600">Risk: <span className="font-medium text-blue-700">{(minVolPortfolio.volatility * 100).toFixed(2)}%</span></p>
            <p className="text-xs text-gray-600">Sharpe: <span className="font-medium">{minVolPortfolio.sharpe_ratio.toFixed(2)}</span></p>
          </div>

          {/* Current Portfolio Card (if provided) */}
          {currentPortfolio && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">Current Portfolio</h4>
              <p className="text-xs text-gray-600">Return: <span className="font-medium">{(currentPortfolio.expected_return * 100).toFixed(2)}%</span></p>
              <p className="text-xs text-gray-600">Risk: <span className="font-medium">{(currentPortfolio.volatility * 100).toFixed(2)}%</span></p>
              <p className="text-xs text-gray-600">Sharpe: <span className="font-medium">{currentPortfolio.sharpe_ratio.toFixed(2)}</span></p>
            </div>
          )}
        </div>

        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis
              type="number"
              dataKey="volatility"
              name="Volatility"
              unit="%"
              domain={['auto', 'auto']}
            >
              <Label
                value="Volatility (Annual %)"
                position="insideBottom"
                offset={-20}
                style={{ fontSize: '14px', fontWeight: 'bold' }}
              />
            </XAxis>

            <YAxis
              type="number"
              dataKey="return"
              name="Return"
              unit="%"
              domain={['auto', 'auto']}
            >
              <Label
                value="Expected Return (Annual %)"
                angle={-90}
                position="insideLeft"
                style={{ fontSize: '14px', fontWeight: 'bold', textAnchor: 'middle' }}
              />
            </YAxis>

            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Efficient Frontier */}
            <Scatter
              name="Efficient Frontier"
              data={chartData.filter(p => p.type === 'frontier' && !p.isMaxSharpe && !p.isMinVol)}
              fill="#8884d8"
              line={{ stroke: '#8884d8', strokeWidth: 2 }}
              lineType="joint"
            />

            {/* Max Sharpe Portfolio */}
            <Scatter
              name="Max Sharpe"
              data={chartData.filter(p => p.isMaxSharpe)}
              fill="#10b981"
              shape="star"
              style={{ fontSize: '20px' }}
            />

            {/* Min Volatility Portfolio */}
            <Scatter
              name="Min Volatility"
              data={chartData.filter(p => p.isMinVol)}
              fill="#3b82f6"
              shape="triangle"
              style={{ fontSize: '20px' }}
            />

            {/* Current Portfolio */}
            {currentPortfolio && (
              <Scatter
                name="Current"
                data={chartData.filter(p => p.type === 'current')}
                fill="#ef4444"
                shape="cross"
                style={{ fontSize: '20px' }}
              />
            )}
          </ScatterChart>
        </ResponsiveContainer>

        <div className="mt-6 p-4 bg-gray-50 rounded">
          <h4 className="text-sm font-semibold mb-2">Interpretation:</h4>
          <ul className="text-xs text-gray-600 space-y-1">
            <li>• <strong>Efficient Frontier:</strong> Portfolios that maximize return for a given risk level</li>
            <li>• <strong>Max Sharpe (⭐):</strong> Best risk-adjusted returns (highest Sharpe ratio)</li>
            <li>• <strong>Min Volatility (▲):</strong> Lowest risk portfolio</li>
            <li>• <strong>Above the curve:</strong> Not achievable with these strategies</li>
            <li>• <strong>Below the curve:</strong> Inefficient - can get better returns for same risk</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default EfficientFrontierChart;
