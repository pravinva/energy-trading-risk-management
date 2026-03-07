import { createColumnHelper } from '@tanstack/react-table';
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useEuropeCrossBorderFlows, useEuropePriceHistory, useEuropePricesCurrent } from '@/api/hooks/europe';
import { DataTable, Panel, Sparkline, StatusBadge } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();

export function EuropeMarketDashboard(): JSX.Element {
  const current = useEuropePricesCurrent();
  const history = useEuropePriceHistory('DE-LU', 168);
  const flows = useEuropeCrossBorderFlows();

  const columns = [
    helper.accessor((r) => `${r.from_zone}-${r.to_zone}`, { id: 'corridor', header: 'CORRIDOR' }),
    helper.accessor('flow_mw', { header: 'FLOW MW' }),
    helper.accessor('atc_mw', { header: 'ATC MW' }),
    helper.accessor('utilisation_pct', { header: 'UTIL %' }),
    helper.accessor('utilisation_pct', {
      id: 'status',
      header: 'STATUS',
      cell: (i) => {
        const value = Number(i.getValue());
        if (value > 90) return <StatusBadge status="critical" label="CRITICAL" />;
        if (value > 70) return <StatusBadge status="warning" label="WARNING" />;
        return <StatusBadge status="active" label="ACTIVE" />;
      },
    }),
  ];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="EPEX PRICE GRID" region="europe">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          {(current.data ?? []).map((row: any) => (
            <div key={row.bidding_zone} style={{ border: '1px solid var(--color-border-subtle)', padding: 8 }}>
              <div className="label-caps">{row.bidding_zone}</div>
              <div className="font-data text-2xl">{Number(row.price_eur_mwh).toFixed(2)}</div>
              <Sparkline data={[40, 60, 70, 50, Number(row.price_eur_mwh)]} positive={Number(row.price_eur_mwh) > 60} />
              <StatusBadge status={row.mtu_minutes === 15 ? 'active' : 'inactive'} label={row.mtu_minutes === 15 ? '15 MIN' : '60 MIN'} />
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="CROSS-BORDER FLOW TABLE" region="europe">
        <DataTable data={flows.data ?? []} columns={columns} />
      </Panel>

      <Panel title="EPEX PRICE HISTORY" region="europe">
        <div style={{ height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={history.data ?? []}>
              <XAxis dataKey="delivery_datetime" hide />
              <YAxis />
              <Tooltip />
              <ReferenceLine x={'2025-09-01T00:00:00.000Z'} label="15-MIN MTU" stroke="var(--color-warning)" />
              <Line dataKey="price_eur_mwh" stroke="var(--color-neutral)" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
