import { DataTable, Panel } from '@/components/primitives';
import { usePPABook, useRevenueStacking } from '@/api/hooks/apex';

export function PortfolioDashboard(): JSX.Element {
  const revenue = useRevenueStacking();
  const ppa = usePPABook();

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="portfolio" title="Revenue Stacking" subtitle="Energy, FCAS, capacity, hedge value">
        <DataTable data={revenue.data ?? []} columns={[{ header: 'Component', accessorKey: 'component' }, { header: 'Annual Value', accessorKey: 'annual_value', meta: { kind: 'price' } }, { header: 'Contribution %', accessorKey: 'contribution_pct', meta: { kind: 'pct' } }]} />
      </Panel>
      <Panel persona="portfolio" title="PPA Book" subtitle="Contract portfolio exposure">
        <DataTable data={ppa.data ?? []} columns={[{ header: 'PPA ID', accessorKey: 'ppa_id' }, { header: 'Counterparty', accessorKey: 'counterparty' }, { header: 'MW', accessorKey: 'volume_mw', meta: { kind: 'mw' } }, { header: 'Strike', accessorKey: 'strike_price', meta: { kind: 'price' } }, { header: 'Tenor', accessorKey: 'tenor_years', meta: { kind: 'mw' } }]} />
      </Panel>
    </div>
  );
}
