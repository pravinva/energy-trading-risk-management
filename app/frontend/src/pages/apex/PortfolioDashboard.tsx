import { useEffect, useMemo, useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useAssetBenchmark, usePPABook, usePortfolioSimulation, usePortfolioSimulationDefaults, useRevenueStacking } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

export function PortfolioDashboard(): JSX.Element {
  const market = useTradingStore((s) => s.market);
  const revenue = useRevenueStacking(market);
  const ppa = usePPABook(market);
  const benchmark = useAssetBenchmark(market);
  const defaults = usePortfolioSimulationDefaults(market);
  const [durationHours, setDurationHours] = useState(2);
  const [ancillaryPct, setAncillaryPct] = useState(40);
  const [ppaMw, setPpaMw] = useState(50);
  const simulation = usePortfolioSimulation(market, durationHours, ancillaryPct, ppaMw);
  const revenueParts = useMemo(() => {
    const rows = simulation.data ?? [];
    const total = rows.reduce((sum, row) => sum + row.annual_value, 0) || 1;
    return rows.map((row) => ({
      component: row.component,
      value: row.annual_value,
      pct: (row.annual_value / total) * 100,
    }));
  }, [simulation.data]);
  const totalRevenue = (revenue.data ?? []).reduce((sum, row) => sum + row.annual_value, 0);
  const ppaFactor = defaults.data?.ppa_mtm_factor ?? 1;
  const ppaMtm = (ppa.data ?? []).reduce((sum, row) => sum + row.volume_mw * row.strike_price * ppaFactor, 0);

  useEffect(() => {
    if (!defaults.data) return;
    setDurationHours(defaults.data.duration_hours_default);
    setAncillaryPct(defaults.data.ancillary_pct_default);
    setPpaMw(defaults.data.ppa_mw_default);
  }, [defaults.data?.market]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <Panel persona="portfolio" title="Total Annual Revenue">
          <div className="font-data text-2xl">{totalRevenue.toFixed(2)}</div>
        </Panel>
        <Panel persona="portfolio" title="PPA MTM">
          <div className="font-data text-2xl">{ppaMtm.toFixed(2)}</div>
        </Panel>
        <Panel persona="portfolio" title="Active Contracts">
          <div className="font-data text-2xl">{(ppa.data ?? []).length}</div>
        </Panel>
        <Panel persona="portfolio" title="Simulation Market">
          <div className="font-data text-2xl">{market}</div>
        </Panel>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Panel persona="portfolio" title="Revenue Stacking Simulator" subtitle={`${market} portfolio composition`}>
          <div style={{ display: 'grid', gap: 8 }}>
            <div>
              <div className="label-caps">Duration (hours)</div>
              <input type="range" min={1} max={defaults.data?.duration_hours_max ?? 8} value={durationHours} onChange={(e) => setDurationHours(Number(e.target.value))} />
              <div className="font-data">{durationHours}hr</div>
            </div>
            <div>
              <div className="label-caps">{market === 'NEM' ? 'FCAS Participation' : market === 'ERCOT' ? 'Ancillary Participation' : 'Reserve Participation'}</div>
              <input type="range" min={0} max={defaults.data?.ancillary_pct_max ?? 100} value={ancillaryPct} onChange={(e) => setAncillaryPct(Number(e.target.value))} />
              <div className="font-data">{ancillaryPct}%</div>
            </div>
            <div>
              <div className="label-caps">PPA Contracted MW</div>
              <input type="range" min={0} max={defaults.data?.ppa_mw_max ?? 300} value={ppaMw} onChange={(e) => setPpaMw(Number(e.target.value))} />
              <div className="font-data">{ppaMw} MW</div>
            </div>
          </div>
          <div style={{ marginTop: 8 }} className="label-caps">Annual Revenue Breakdown</div>
          <div style={{ display: 'flex', height: 24, borderRadius: 3, overflow: 'hidden', marginTop: 8 }}>
            {revenueParts.map((part, idx) => (
              <div key={part.component} style={{ flex: Math.max(1, part.pct), background: idx % 2 === 0 ? 'var(--color-persona-portfolio)' : 'var(--color-persona-dispatch)', opacity: 0.75, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10 }}>
                {part.component}
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 8, marginTop: 8 }}>
            {revenueParts.map((part) => (
              <div key={`${part.component}-kv`}>
                <div className="label-caps">{part.component}</div>
                <div className="font-data">{part.value.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </Panel>
        <div style={{ display: 'grid', gap: 10 }}>
          <Panel persona="portfolio" title="PPA Book" subtitle={`Contract portfolio exposure (${market})`}>
            <DataTable data={ppa.data ?? []} columns={[{ header: 'PPA ID', accessorKey: 'ppa_id' }, { header: 'Counterparty', accessorKey: 'counterparty' }, { header: 'MW', accessorKey: 'volume_mw', meta: { kind: 'mw' } }, { header: 'Strike', accessorKey: 'strike_price', meta: { kind: 'price' } }, { header: 'Tenor', accessorKey: 'tenor_years', meta: { kind: 'mw' } }]} />
          </Panel>
          <Panel persona="portfolio" title="Asset Benchmarking">
            <DataTable
              data={benchmark.data ?? []}
              columns={[
                { header: 'Rank', accessorKey: 'rank' },
                { header: 'Asset', accessorKey: 'asset' },
                { header: 'Rev/MW', accessorKey: 'rev_per_mw', meta: { kind: 'price' } },
                { header: 'vs Benchmark', accessorKey: 'vs_benchmark_pct', meta: { kind: 'pct' } },
              ]}
            />
          </Panel>
        </div>
      </div>
    </div>
  );
}
