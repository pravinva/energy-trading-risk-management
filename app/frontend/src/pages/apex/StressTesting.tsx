import { useEffect, useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useMarketSpotPrice, useStressRunset } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

type StressResult = {
  scenario: string;
  confidence: number;
  volatility: number;
  var95: number;
  var99: number;
  es95: number;
};

export function StressTesting(): JSX.Element {
  const market = useTradingStore((s) => s.market);
  const spot = useMarketSpotPrice(market);
  const [spotPrice, setSpotPrice] = useState(96);
  const [submittedSpot, setSubmittedSpot] = useState(96);
  const runset = useStressRunset(market, submittedSpot);

  useEffect(() => {
    if (spot.data?.spot_price) {
      const next = Number(spot.data.spot_price.toFixed(2));
      setSpotPrice(next);
      setSubmittedSpot(next);
    }
  }, [spot.data?.spot_price]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="risk" title="Stress Testing" subtitle="Scenario-based risk impact using VaR engine">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
          <input className="mono-price" value={spotPrice} onChange={(e) => setSpotPrice(Number(e.target.value))} />
          <button onClick={() => setSubmittedSpot(spotPrice)} disabled={runset.isFetching}>{runset.isFetching ? 'Refreshing...' : 'Refresh Stress Set'}</button>
        </div>
      </Panel>
      <Panel persona="risk" title="Scenario Results">
        <DataTable
          data={(runset.data ?? []) as StressResult[]}
          columns={[
            { header: 'Scenario', accessorKey: 'scenario' },
            { header: 'Confidence', accessorKey: 'confidence' },
            { header: 'Volatility', accessorKey: 'volatility' },
            { header: 'VaR95', accessorKey: 'var95', meta: { kind: 'price' } },
            { header: 'VaR99', accessorKey: 'var99', meta: { kind: 'price' } },
            { header: 'ES95', accessorKey: 'es95', meta: { kind: 'price' } },
          ]}
        />
      </Panel>
    </div>
  );
}
