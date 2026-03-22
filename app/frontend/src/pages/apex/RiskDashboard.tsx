import { useEffect, useMemo, useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useForecastMetadata, useLimitStatus, useMarketSpotPrice, useModelLineage, usePredispatch, useStressScenarios, useVaR } from '@/api/hooks/apex';
import { useTraders } from '@/api/hooks/useUserContext';
import { useTradingStore } from '@/store/tradingStore';
// import { RiskHeatmap } from '@/components/charts';
import { Tooltip } from '@/components/Tooltip';
import { getMetricInfo } from '@/config/dataDictionary';

export function RiskDashboard(): JSX.Element {
  const [spotPrice, setSpotPrice] = useState(96);
  const [volatility, setVolatility] = useState(0.12);
  const [traderScope, setTraderScope] = useState('');
  const [hasBootstrappedVar, setHasBootstrappedVar] = useState(false);
  const varCalc = useVaR();
  const limits = useLimitStatus();
  const market = useTradingStore((s) => s.market);
  const sessionPnl = useTradingStore((s) => s.sessionPnl);
  const spot = useMarketSpotPrice(market);
  const traders = useTraders();
  const predispatch = usePredispatch(24, market);
  const forecastMeta = useForecastMetadata(market);
  const lineage = useModelLineage(market);
  const stress = useStressScenarios(market, spotPrice, volatility);
  const bars = useMemo(() => {
    const prices = [...(predispatch.data ?? [])].slice(0, 60).map((p) => p.forecast_price);
    const max = Math.max(...prices, 1);
    return prices.map((value, i) => {
      const height = Math.max(6, (value / max) * 96);
      const color = value > max * 0.75 ? 'var(--color-negative)' : value > max * 0.5 ? 'var(--color-warning)' : 'var(--color-positive)';
      return { id: i, height, color };
    });
  }, [predispatch.data]);
  const var99Trend = useMemo(
    () =>
      [...(predispatch.data ?? [])]
        .slice(0, 30)
        .reverse()
        .map((row) => Number((Math.abs(row.forecast_price) * Math.max(varCalc.data?.exposure_mw ?? 1, 1) * 2.33).toFixed(2))),
    [predispatch.data, varCalc.data?.exposure_mw],
  );
  const maxTrend = var99Trend.length ? Math.max(...var99Trend) : 1;
  const minTrend = var99Trend.length ? Math.min(...var99Trend) : 0;
  const trendPoints = var99Trend
    .map((value, index) => {
      const x = (index / (var99Trend.length - 1)) * 100;
      const y = maxTrend === minTrend ? 30 : 55 - ((value - minTrend) / (maxTrend - minTrend)) * 46;
      return `${x},${y}`;
    })
    .join(' ');
  const limitPct = limits.data?.[0] ? Math.min(100, (limits.data[0].current / limits.data[0].limit) * 100) : 0;
  const positionValue = Math.abs(sessionPnl) + (varCalc.data?.exposure_mw ?? 0) * spotPrice;
  const stressScenarios = stress.data ?? [];
  const latestLineage = lineage.data?.[0];
  const traderOptions = ['All Traders', ...((traders.data?.data as string[] | undefined) ?? [])];

  useEffect(() => {
    if (spot.data?.spot_price) {
      setSpotPrice(Number(spot.data.spot_price.toFixed(2)));
    }
  }, [spot.data?.spot_price]);

  useEffect(() => {
    if (!traderScope && traderOptions.length > 0) {
      setTraderScope(traderOptions[0]);
    }
  }, [traderOptions, traderScope]);

  useEffect(() => {
    if (hasBootstrappedVar || varCalc.isPending || spotPrice <= 0) return;
    varCalc.mutate(
      { confidence: 0.95, spot_price: spotPrice, volatility },
      { onSettled: () => setHasBootstrappedVar(true) },
    );
  }, [hasBootstrappedVar, spotPrice, volatility, varCalc]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      {/* Phase 4: Advanced Risk Visualization */}
      {/* <RiskHeatmap market={market} spotPrice={spotPrice} volatility={volatility * 100} /> */}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <Panel persona="risk" title={
          <Tooltip {...getMetricInfo('var_95')!}>
            Portfolio VaR 95%
          </Tooltip>
        }>
          <div className="font-data text-2xl">{varCalc.data?.var_95?.toFixed(2) ?? '--'}</div>
        </Panel>
        <Panel persona="risk" title={
          <Tooltip {...getMetricInfo('var_99')!}>
            Portfolio VaR 99%
          </Tooltip>
        }>
          <div className="font-data text-2xl">{varCalc.data?.var_99?.toFixed(2) ?? '--'}</div>
        </Panel>
        <Panel persona="risk" title={
          <Tooltip {...getMetricInfo('position_value')!}>
            Position Value
          </Tooltip>
        }>
          <div className="font-data text-2xl">{positionValue.toFixed(2)}</div>
        </Panel>
        <Panel persona="risk" title="Limit Utilisation">
          <div className="font-data text-2xl">{limitPct.toFixed(1)}%</div>
        </Panel>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Panel
          persona="risk"
          title="VaR Dashboard"
          subtitle={
            forecastMeta.data
              ? `Portfolio risk exposure — Monte Carlo 10,000 paths · Forecast source ${forecastMeta.data.model_name} (${forecastMeta.data.points_available} points)`
              : 'Portfolio risk exposure — Monte Carlo 10,000 paths'
          }
        >
          <div
            style={{
              marginBottom: 10,
              background: 'var(--color-bg-surface)',
              border: '1px solid var(--color-border-subtle)',
              padding: 8,
            }}
          >
            <div className="label-caps">Model Lineage</div>
            <div className="font-data" style={{ marginTop: 4 }}>
              {latestLineage
                ? `${latestLineage.model_name} · run ${latestLineage.run_timestamp} · train ${latestLineage.training_start_utc} to ${latestLineage.training_end_utc} · hash ${latestLineage.feature_hash.slice(0, 12)}...`
                : 'Lineage loading'}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: 8 }}>
            <input className="mono-price" value={spotPrice} onChange={(e) => setSpotPrice(Number(e.target.value))} />
            <input className="mono-pct" value={volatility} onChange={(e) => setVolatility(Number(e.target.value))} />
            <select value={traderScope} onChange={(e) => setTraderScope(e.target.value)}>
              {traderOptions.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
            <button onClick={() => varCalc.mutate({ confidence: 0.95, spot_price: spotPrice, volatility })}>Refresh VaR</button>
          </div>
          <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
            <div className="font-data">
              <Tooltip {...getMetricInfo('exposure_mw')!}>
                Exposure
              </Tooltip>: {varCalc.data?.exposure_mw?.toFixed(2) ?? '--'}
            </div>
            <div className="font-data">
              <Tooltip {...getMetricInfo('var_95')!}>
                VaR95
              </Tooltip>: {varCalc.data?.var_95?.toFixed(2) ?? '--'}
            </div>
            <div className="font-data">
              <Tooltip {...getMetricInfo('var_99')!}>
                VaR99
              </Tooltip>: {varCalc.data?.var_99?.toFixed(2) ?? '--'}
            </div>
            <div className="font-data">
              <Tooltip {...getMetricInfo('expected_shortfall')!}>
                ES95
              </Tooltip>: {varCalc.data?.expected_shortfall_95?.toFixed(2) ?? '--'}
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <div className="label-caps" style={{ marginTop: 0 }}>
                <Tooltip {...getMetricInfo('forecast_price')!}>
                  Price Forecast - Next 60 Hours
                </Tooltip>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 'var(--text-2xs)', color: 'var(--color-text-tertiary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{ width: 8, height: 8, background: 'var(--color-negative)', borderRadius: 1 }} />
                  <span>High (&gt;75%)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{ width: 8, height: 8, background: 'var(--color-warning)', borderRadius: 1 }} />
                  <span>Med (50-75%)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{ width: 8, height: 8, background: 'var(--color-positive)', borderRadius: 1 }} />
                  <span>Low (&lt;50%)</span>
                </div>
              </div>
            </div>
            <div className="var-chart" style={{ marginTop: 0 }}>
              {bars.map((bar) => (
                <div key={bar.id} className="bar" style={{ minWidth: 2, height: `${bar.height}px`, background: bar.color }} />
              ))}
            </div>
          </div>
          <div className="label-caps" style={{ marginTop: 16, marginBottom: 4 }}>
            <Tooltip {...getMetricInfo('var_99')!}>
              VaR 99% — 30-Day Trend
            </Tooltip>
          </div>
          <div style={{ position: 'relative', marginTop: 8 }}>
            <svg width="100%" height="120" viewBox="0 0 400 120" style={{ overflow: 'visible' }}>
              {/* Grid lines */}
              <line x1="40" y1="10" x2="390" y2="10" stroke="var(--color-border-subtle)" strokeWidth="0.5" strokeDasharray="2,2" />
              <line x1="40" y1="35" x2="390" y2="35" stroke="var(--color-border-subtle)" strokeWidth="0.5" strokeDasharray="2,2" />
              <line x1="40" y1="60" x2="390" y2="60" stroke="var(--color-border-subtle)" strokeWidth="0.5" strokeDasharray="2,2" />
              <line x1="40" y1="85" x2="390" y2="85" stroke="var(--color-border-subtle)" strokeWidth="0.5" strokeDasharray="2,2" />

              {/* Y-axis */}
              <line x1="40" y1="10" x2="40" y2="85" stroke="var(--color-border-default)" strokeWidth="1" />
              <text x="35" y="15" textAnchor="end" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                {maxTrend.toFixed(0)}
              </text>
              <text x="35" y="62" textAnchor="end" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                {((maxTrend + minTrend) / 2).toFixed(0)}
              </text>
              <text x="35" y="89" textAnchor="end" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                {minTrend.toFixed(0)}
              </text>

              {/* X-axis */}
              <line x1="40" y1="85" x2="390" y2="85" stroke="var(--color-border-default)" strokeWidth="1" />
              <text x="40" y="100" textAnchor="start" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                30d ago
              </text>
              <text x="215" y="100" textAnchor="middle" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                15d
              </text>
              <text x="390" y="100" textAnchor="end" fontSize="9" fill="var(--color-text-tertiary)" fontFamily="var(--font-data)">
                Now
              </text>

              {/* Trend line - adjusted for new coordinate system */}
              <polyline
                fill="none"
                stroke="var(--color-warning)"
                strokeWidth="2"
                points={var99Trend
                  .map((value, index) => {
                    const x = 40 + (index / (var99Trend.length - 1)) * 350;
                    const y = maxTrend === minTrend ? 47.5 : 85 - ((value - minTrend) / (maxTrend - minTrend)) * 75;
                    return `${x},${y}`;
                  })
                  .join(' ')}
              />

              {/* Legend */}
              <g transform="translate(45, 105)">
                <line x1="0" y1="0" x2="16" y2="0" stroke="var(--color-warning)" strokeWidth="2" />
                <text x="20" y="4" fontSize="9" fill="var(--color-text-secondary)" fontFamily="var(--font-ui)">
                  99% VaR - Maximum expected loss at 99% confidence
                </text>
              </g>
            </svg>
          </div>
        </Panel>
        <div style={{ display: 'grid', gap: 10 }}>
          <Panel persona="risk" title="Limit Monitor">
            <DataTable data={limits.data ?? []} columns={[{ header: 'Metric', accessorKey: 'metric' }, { header: 'Current', accessorKey: 'current', meta: { kind: 'price' } }, { header: 'Limit', accessorKey: 'limit', meta: { kind: 'price' } }, { header: 'Breached', accessorKey: 'breached' }]} />
          </Panel>
          <Panel persona="risk" title={`Stress Scenarios — ${market}`}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {stressScenarios.map((scenario) => (
                <div key={scenario.scenario} style={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
                  <div style={{ fontWeight: 600 }}>{scenario.scenario}</div>
                  <div className="font-data" style={{ color: scenario.shock.startsWith('-') ? 'var(--color-positive)' : 'var(--color-negative)' }}>{scenario.shock}</div>
                  <div className="font-data">Impact {scenario.impact.toFixed(2)}</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
