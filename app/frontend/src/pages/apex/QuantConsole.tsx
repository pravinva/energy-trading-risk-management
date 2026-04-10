import { useMemo } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useBacktestStrategies, useBacktests, useForecastMetadata, useModelLineage, useModelPerformance, usePredispatch, useBacktestResults } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';
// import { WeatherImpact, VolumeForecast, ProductionForecast } from '@/components/forecasting';
// import { StrategyDashboard, BacktestResults, LiveStrategyMonitor, AgentCollaboration } from '@/components/strategies';
// import { DataFreshness, IngestionLogs, DataQuality } from '@/components/nemweb';
// import { PriceChart, ForecastAccuracyChart, PriceAlerts, StrategyComparisonChart, RiskHeatmap } from '@/components/charts';
import { Tooltip } from '@/components/Tooltip';
import { getMetricInfo } from '@/config/dataDictionary';

export function QuantConsole(): JSX.Element {
  const market = useTradingStore((s) => s.market);

  // Map market to region_id for NEM forecasting
  // TODO: Add EPEX and ERCOT region mappings when expanding to multiple markets
  const regionId = market === 'NEM' ? 'NSW1' : 'NSW1';
  const models = useModelPerformance();
  const backtests = useBacktests();
  const strategies = useBacktestStrategies(market);
  const lineage = useModelLineage(market);
  const predispatch = usePredispatch(24, market);
  const forecastMeta = useForecastMetadata(market);
  const strategyTabs = strategies.data ?? [];
  const points = useMemo(
    () =>
      [...(predispatch.data ?? [])]
        .slice(0, 48)
        .reverse()
        .map((row) => row.forecast_price),
    [predispatch.data],
  );
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const chartPath = points
    .map((value, idx) => {
      const x = points.length > 1 ? (idx / (points.length - 1)) * 100 : 0;
      const y = max === min ? 36 : 62 - ((value - min) / (max - min)) * 52;
      return `${x},${y}`;
    })
    .join(' ');
  const forecastPath = points
    .map((value, idx) => {
      const prior = idx > 0 ? points[idx - 1] : value;
      const next = idx < points.length - 1 ? points[idx + 1] : value;
      const smoothed = (prior + value + next) / 3;
      const x = points.length > 1 ? (idx / (points.length - 1)) * 100 : 0;
      const y = max === min ? 36 : 62 - ((smoothed - min) / (max - min)) * 52;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      {/* Phase 4: Advanced Analytics & Visualization - Market Data */}
      {/* <PriceChart regionId={regionId} days={30} /> */}
      {/* <ForecastAccuracyChart regionId={regionId} days={30} /> */}
      {/* <PriceAlerts regionId={regionId} days={7} /> */}

      {/* Phase 4: Advanced Analytics & Visualization - Strategy Analysis */}
      {/* <StrategyComparisonChart strategyType={null} limit={10} /> */}

      {/* Phase 4: Advanced Analytics & Visualization - Risk Management */}
      {/* <RiskHeatmap market={market} spotPrice={100} volatility={25} /> */}

      {/* Phase 1: Forecasting & Predictive Analytics */}
      {/* <VolumeForecast regionId={regionId} days={15} /> */}
      {/* <WeatherImpact regionId={regionId} days={7} /> */}
      {/* <ProductionForecast regionId={regionId} days={7} /> */}

      {/* Phase 2: Strategy Development with Agents */}
      {/* <StrategyDashboard /> */}
      {/* <BacktestResults /> */}
      {/* <LiveStrategyMonitor /> */}
      {/* <AgentCollaboration /> */}

      {/* Phase 3: NEMWEB Data Ingestion & Monitoring */}
      {/* <DataFreshness /> */}
      {/* <IngestionLogs /> */}
      {/* <DataQuality /> */}

      {/* Existing Analytics */}
      <Panel persona="quant" title="Model Performance" subtitle="Champion vs challenger">
        <DataTable
          data={models.data ?? []}
          columns={[
            {
              header: () => <Tooltip {...getMetricInfo('model_name')!}>Model</Tooltip>,
              accessorKey: 'model_name'
            },
            {
              header: () => <Tooltip {...getMetricInfo('mape')!}>MAPE</Tooltip>,
              accessorKey: 'mape',
              meta: { kind: 'pct' }
            },
            {
              header: () => <Tooltip {...getMetricInfo('rmse')!}>RMSE</Tooltip>,
              accessorKey: 'rmse',
              meta: { kind: 'price' }
            },
            {
              header: () => <Tooltip {...getMetricInfo('r2')!}>R²</Tooltip>,
              accessorKey: 'r2',
              meta: { kind: 'pct' }
            },
          ]}
        />
      </Panel>
      <Panel persona="quant" title="Model Lineage" subtitle="Run provenance · training window · feature signature">
        <DataTable
          data={lineage.data ?? []}
          columns={[
            {
              header: () => <Tooltip {...getMetricInfo('market')!}>Market</Tooltip>,
              accessorKey: 'market'
            },
            {
              header: () => <Tooltip {...getMetricInfo('model_name')!}>Model</Tooltip>,
              accessorKey: 'model_name'
            },
            {
              header: () => <Tooltip {...getMetricInfo('run_timestamp')!}>Last Run (UTC)</Tooltip>,
              accessorKey: 'run_timestamp'
            },
            {
              header: () => <Tooltip {...getMetricInfo('training_start')!}>Train Start (UTC)</Tooltip>,
              accessorKey: 'training_start_utc'
            },
            {
              header: () => <Tooltip {...getMetricInfo('training_end')!}>Train End (UTC)</Tooltip>,
              accessorKey: 'training_end_utc'
            },
            {
              header: () => <Tooltip {...getMetricInfo('feature_hash')!}>Feature Hash</Tooltip>,
              accessorKey: 'feature_hash'
            },
            {
              header: () => <Tooltip {...getMetricInfo('feature_set')!}>Feature Set</Tooltip>,
              accessorKey: 'feature_set'
            },
          ]}
        />
      </Panel>
      <Panel
        persona="quant"
        title="Strategy Backtest"
        subtitle={forecastMeta.data ? `Strategy benchmarking · ${forecastMeta.data.model_name}` : 'Strategy benchmarking'}
      >
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          {strategyTabs.map((tab) => {
            const disabled = !tab.available;
            return (
              <span
                key={tab.strategy}
                title={disabled ? 'Unavailable for selected market' : undefined}
                style={{
                  padding: '6px 10px',
                  border: '1px solid var(--color-border-subtle)',
                  background: disabled ? 'var(--color-bg-surface)' : 'var(--color-bg-surface-strong)',
                  color: disabled ? 'var(--color-text-tertiary)' : 'var(--color-text-primary)',
                  borderRadius: 4,
                  fontSize: 11,
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                {tab.strategy}
              </span>
            );
          })}
        </div>
        <div className="label-caps" style={{ marginBottom: 6 }}>Forecast vs Actual — Last 48h</div>
        <svg width="100%" height="86" viewBox="0 0 100 72" style={{ marginBottom: 8 }}>
          <polyline fill="none" stroke="var(--color-text-secondary)" strokeWidth="1.4" points={chartPath} />
          <polyline fill="none" stroke="var(--color-persona-quant)" strokeWidth="1.4" strokeDasharray="2,2" points={forecastPath} />
          {/* Legend */}
          <g transform="translate(5, 5)">
            <line x1="0" y1="0" x2="8" y2="0" stroke="var(--color-text-secondary)" strokeWidth="1.4" />
            <text x="10" y="4" fontSize="8" fill="var(--color-text-tertiary)" fontFamily="var(--font-ui)">Actual</text>
            <line x1="35" y1="0" x2="43" y2="0" stroke="var(--color-persona-quant)" strokeWidth="1.4" strokeDasharray="2,2" />
            <text x="45" y="4" fontSize="8" fill="var(--color-text-tertiary)" fontFamily="var(--font-ui)">Forecast</text>
          </g>
        </svg>
        <DataTable
          data={backtests.data ?? []}
          columns={[
            {
              header: () => <Tooltip {...getMetricInfo('strategy')!}>Strategy</Tooltip>,
              accessorKey: 'strategy'
            },
            {
              header: () => <Tooltip {...getMetricInfo('trades')!}>Trades</Tooltip>,
              accessorKey: 'trades',
              meta: { kind: 'mw' }
            },
            {
              header: () => <Tooltip {...getMetricInfo('win_rate')!}>Win Rate</Tooltip>,
              accessorKey: 'win_rate',
              meta: { kind: 'pct' }
            },
            {
              header: () => <Tooltip {...getMetricInfo('total_pnl')!}>Total PnL</Tooltip>,
              accessorKey: 'total_pnl',
              meta: { kind: 'price' }
            },
            {
              header: () => <Tooltip {...getMetricInfo('sharpe')!}>Sharpe</Tooltip>,
              accessorKey: 'sharpe',
              meta: { kind: 'pct' }
            },
          ]}
        />
      </Panel>
    </div>
  );
}
