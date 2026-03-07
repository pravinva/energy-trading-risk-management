import { createColumnHelper } from '@tanstack/react-table';
import { useState } from 'react';
import { Area, AreaChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useERCOTRTCBComparison } from '@/api/hooks/americas';
import { DataTable, Panel, StatusBadge } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();
const assets = ['ERCOT_BESS_001', 'ERCOT_BESS_002', 'ERCOT_BESS_003', 'ERCOT_BESS_004', 'ERCOT_BESS_005', 'ERCOT_BESS_006', 'ERCOT_BESS_007', 'ERCOT_BESS_008', 'ERCOT_BESS_009', 'ERCOT_BESS_010'];

export function AmericasBESSIntelligence(): JSX.Element {
  const [asset, setAsset] = useState(assets[0]);
  const comparison = useERCOTRTCBComparison(asset);

  const cols = [
    helper.accessor('period', { header: 'PERIOD' }),
    helper.accessor('avg_tb4_spread', { header: 'AVG TB4' }),
    helper.accessor('avg_drrs_mw', { header: 'AVG DRRS MW', cell: (i) => (i.row.original.period === 'pre_rtcb' ? '--' : i.getValue()) }),
    helper.accessor('avg_output_mw', { header: 'AVG OUTPUT' }),
    helper.accessor('avg_soc_pct', { header: 'AVG SOC %' }),
  ];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="ERCOT BESS DISPATCH INTELLIGENCE - RTC+B ERA" region="americas">
        <div className="font-data text-md">ERCOT Real-Time Co-optimization + Batteries (RTC+B) launched December 5, 2025</div>
        <div className="text-sm text-secondary" style={{ marginTop: 6 }}>Pre-December 2025 dispatch models require retraining.</div>
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <StatusBadge status="critical" label="PRE-RTC+B MODELS: STALE" />
          <StatusBadge status="active" label="NEXUS SIGNAL CAPTURE: ACTIVE" />
        </div>
      </Panel>

      <Panel title="ASSET SELECTOR" region="americas">
        <select value={asset} onChange={(e) => setAsset(e.target.value)}>{assets.map((a) => <option key={a}>{a}</option>)}</select>
      </Panel>

      <Panel title="RTCB COMPARISON" region="americas">
        <DataTable data={comparison.data ?? []} columns={cols} />
      </Panel>

      <Panel title="TB SPREAD TIMESERIES" region="americas">
        <div style={{ height: 220 }}>
          <ResponsiveContainer>
            <AreaChart data={(comparison.data ?? []).map((r: any, idx: number) => ({ idx, value: r.avg_tb4_spread }))}>
              <XAxis dataKey="idx" />
              <YAxis />
              <Tooltip />
              <ReferenceLine x={1} label="2025-12-05" stroke="var(--color-warning)" />
              <Area dataKey="value" stroke="var(--color-warning)" fill="var(--color-warning-dim)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
