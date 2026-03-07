import { useEffect, useMemo, useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useForecastMetadata, useLimitStatus, useMarketSpotPrice, useModelLineage, usePredispatch, useStressScenarios, useVaR } from '@/api/hooks/apex';
import { useTraders } from '@/api/hooks/useUserContext';
import { useTradingStore } from '@/store/tradingStore';

export function RiskDashboard(): JSX.Element {
  const [spotPrice, setSpotPrice] = useState(96);
  const [volatility, setVolatility] = useState(0.12);
  const [traderScope, setTraderScope] = useState('');
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

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <Panel persona="risk" title="Portfolio VaR 95%">
          <div className="font-data text-2xl">{varCalc.data?.var_95?.toFixed(2) ?? '--'}</div>
        </Panel>
        <Panel persona="risk" title="Portfolio VaR 99%">
          <div className="font-data text-2xl">{varCalc.data?.var_99?.toFixed(2) ?? '--'}</div>
        </Panel>
        <Panel persona="risk" title="Position Value">
          <div className="font-data text-2xl">{positionValue.toFixed(2)}</div>
        </Panel>
        <Panel persona="risk" title="Limit Utilisation">
          <div className="font-data text-2xl">{limitPct.toFixed(1)}%</div>
        </Panel>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Panel
          persona="risk"
          title="VaR Analysis"
          subtitle={forecastMeta.data ? `Forecast source: ${forecastMeta.data.model_name} (${forecastMeta.data.points_available} points)` : 'Forecast source loading'}
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
          <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="font-data">Exposure: {varCalc.data?.exposure_mw?.toFixed(2) ?? '--'}</div>
            <div className="font-data">VaR95: {varCalc.data?.var_95?.toFixed(2) ?? '--'}</div>
            <div className="font-data">VaR99: {varCalc.data?.var_99?.toFixed(2) ?? '--'}</div>
            <div className="font-data">ES95: {varCalc.data?.expected_shortfall_95?.toFixed(2) ?? '--'}</div>
          </div>
          <div className="var-chart" style={{ marginTop: 12 }}>
            {bars.map((bar) => (
              <div key={bar.id} className="bar" style={{ minWidth: 2, height: `${bar.height}px`, background: bar.color }} />
            ))}
          </div>
          <div className="label-caps" style={{ marginTop: 8 }}>VaR 99% - 30 day trend</div>
          <svg width="100%" height="62" viewBox="0 0 100 62">
            <polyline fill="none" stroke="var(--color-warning)" strokeWidth="1.5" points={trendPoints} />
          </svg>
        </Panel>
        <div style={{ display: 'grid', gap: 10 }}>
          <Panel persona="risk" title="Limit Monitor">
            <DataTable data={limits.data ?? []} columns={[{ header: 'Metric', accessorKey: 'metric' }, { header: 'Current', accessorKey: 'current', meta: { kind: 'price' } }, { header: 'Limit', accessorKey: 'limit', meta: { kind: 'price' } }, { header: 'Breached', accessorKey: 'breached' }]} />
          </Panel>
          <Panel persona="risk" title={`Stress Scenarios - ${market}`}>
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
