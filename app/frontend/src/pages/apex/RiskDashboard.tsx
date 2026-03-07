import { useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useLimitStatus, useVaR } from '@/api/hooks/apex';

export function RiskDashboard(): JSX.Element {
  const [spotPrice, setSpotPrice] = useState(96);
  const [volatility, setVolatility] = useState(0.12);
  const varCalc = useVaR();
  const limits = useLimitStatus();

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="risk" title="VaR Calculator" subtitle="Monte Carlo 10,000 scenarios">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8 }}>
          <input className="mono-price" value={spotPrice} onChange={(e) => setSpotPrice(Number(e.target.value))} />
          <input className="mono-pct" value={volatility} onChange={(e) => setVolatility(Number(e.target.value))} />
          <button onClick={() => varCalc.mutate({ confidence: 0.95, spot_price: spotPrice, volatility })}>Run VaR</button>
        </div>
        <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="font-data">Exposure: {varCalc.data?.exposure_mw?.toFixed(2) ?? '--'}</div>
          <div className="font-data">VaR95: {varCalc.data?.var_95?.toFixed(2) ?? '--'}</div>
          <div className="font-data">VaR99: {varCalc.data?.var_99?.toFixed(2) ?? '--'}</div>
          <div className="font-data">ES95: {varCalc.data?.expected_shortfall_95?.toFixed(2) ?? '--'}</div>
        </div>
      </Panel>
      <Panel persona="risk" title="Limit Monitor">
        <DataTable data={limits.data ?? []} columns={[{ header: 'Metric', accessorKey: 'metric' }, { header: 'Current', accessorKey: 'current', meta: { kind: 'price' } }, { header: 'Limit', accessorKey: 'limit', meta: { kind: 'price' } }, { header: 'Breached', accessorKey: 'breached' }]} />
      </Panel>
    </div>
  );
}
