import { createColumnHelper } from '@tanstack/react-table';
import { useState } from 'react';
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useAmericasCurrentPrices, useAmericasLMPHistory } from '@/api/hooks/americas';
import { DataTable, Panel } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();
const ISOS = ['ERCOT', 'PJM', 'CAISO', 'MISO', 'SPP', 'NYISO', 'ISONE', 'IESO', 'AESO'];

export function AmericasMarketDashboard(): JSX.Element {
  const [iso, setIso] = useState<string | undefined>(undefined);
  const prices = useAmericasCurrentPrices(iso);
  const history = useAmericasLMPHistory(iso ?? 'ERCOT', 24);
  const historyPoints = history.data ?? [];

  const columns = [
    helper.accessor('iso_id', { header: 'ISO' }),
    helper.accessor('node_name', { header: 'HUB / ZONE' }),
    helper.accessor('lmp', { header: 'LMP' }),
    helper.accessor('energy_component', { header: 'ENERGY' }),
    helper.accessor('congestion_component', {
      header: 'CONGESTION',
      cell: (i) => (i.row.original.iso_id === 'ERCOT' ? 'N/A' : i.getValue()),
    }),
    helper.accessor('loss_component', { header: 'LOSS' }),
    helper.accessor('interval_datetime', { header: 'TIMESTAMP' }),
  ];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="ISO SELECTOR" region="americas">
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button onClick={() => setIso(undefined)}>ALL</button>
          {ISOS.map((c) => (<button key={c} onClick={() => setIso(c)}>{c}</button>))}
        </div>
      </Panel>

      <Panel title="MULTI-ISO PRICE TABLE" region="americas">
        <DataTable data={prices.data ?? []} columns={columns} />
      </Panel>

      <Panel title="LMP HISTORY" region="americas">
        <div style={{ height: 250 }}>
          <ResponsiveContainer>
            <LineChart data={historyPoints}>
              <XAxis dataKey="interval_datetime" hide />
              <YAxis />
              <Tooltip />
              <ReferenceLine x={'2025-12-05T00:00:00.000Z'} label="RTC+B LIVE" stroke="var(--color-warning)" />
              <Line dataKey="lmp" stroke="var(--color-neutral)" dot={historyPoints.length <= 2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
