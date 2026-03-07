import { createColumnHelper } from '@tanstack/react-table';
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useEuropeOpenLinkAssets, useEuropeSparkSpreads } from '@/api/hooks/europe';
import { DataTable, Panel, Sparkline, StatusBadge } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();

export function EuropePortfolioIntelligence(): JSX.Element {
  const assets = useEuropeOpenLinkAssets();
  const spreads = useEuropeSparkSpreads('DE-LU');

  const cols = [
    helper.accessor('asset_name', { header: 'ASSET' }),
    helper.accessor('operator', { header: 'OPERATOR' }),
    helper.accessor('country', { header: 'COUNTRY' }),
    helper.accessor('fuel_type', { header: 'FUEL' }),
    helper.accessor('capacity_mw', { header: 'CAPACITY MW' }),
    helper.accessor('openlink_incumbent', {
      header: 'STATUS',
      cell: (i) =>
        i.getValue() ? <StatusBadge status="warning" label="OPENLINK" /> : <StatusBadge status="active" label="DATABRICKS READY" />,
    }),
  ];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="GENERATION PORTFOLIO" region="europe">
        <DataTable data={assets.data ?? []} columns={cols} />
      </Panel>

      <Panel title="ETS CARBON PRICE STRIP" region="europe">
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div className="font-data text-xl">EUA 68.42</div>
          <div className="text-secondary">30D CHANGE +2.1</div>
          <Sparkline data={[60, 61, 58, 62, 67, 68]} positive />
        </div>
      </Panel>

      <Panel title="SPARK SPREAD HISTORY" region="europe">
        <div style={{ height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={spreads.data ?? []}>
              <XAxis dataKey="calculation_datetime" hide />
              <YAxis />
              <Tooltip />
              <ReferenceLine y={0} stroke="var(--color-border-default)" />
              <Line dataKey="spark_spread" stroke="var(--color-neutral)" dot={false} />
              <Line dataKey="clean_spark_spread" stroke="var(--color-positive)" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
