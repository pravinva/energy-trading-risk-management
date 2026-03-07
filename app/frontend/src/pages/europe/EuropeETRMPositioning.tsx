import { createColumnHelper } from '@tanstack/react-table';
import { useState } from 'react';

import { useEuropeREMITAudit } from '@/api/hooks/europe';
import { DataTable, Panel } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();
const columns = [
  helper.accessor('delivery_datetime', { header: 'DELIVERY DATETIME' }),
  helper.accessor('bidding_zone', { header: 'BIDDING ZONE' }),
  helper.accessor('price_eur_mwh', { header: 'PRICE' }),
  helper.accessor('data_source', { header: 'DATA SOURCE' }),
  helper.accessor('recorded_at', { header: 'RECORDED_AT' }),
];

export function EuropeETRMPositioning(): JSX.Element {
  const [zone, setZone] = useState('DE-LU');
  const [auditDate, setAuditDate] = useState(new Date().toISOString().slice(0, 10));
  const audit = useEuropeREMITAudit(zone, auditDate);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="REMIT CAPABILITY DEMO" region="europe">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <div className="label-caps">LEGACY ETRM REMIT</div>
            <ul>
              <li>Compliance module bolt-on</li>
              <li>Manual extraction for reporting</li>
              <li>T+2 audit reconstruction time</li>
              <li>Separate compliance database</li>
            </ul>
          </div>
          <div>
            <div className="label-caps">DATABRICKS UNITY CATALOG</div>
            <ul>
              <li>Delta time-travel replay</li>
              <li>Complete lineage to reported trade</li>
              <li>Real-time audit responses</li>
              <li>REMIT II schema extension pattern</li>
            </ul>
          </div>
        </div>
      </Panel>

      <Panel title="REMIT AUDIT SIMULATION" region="europe">
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <select value={zone} onChange={(e) => setZone(e.target.value)}>
            <option>DE-LU</option><option>FR</option><option>BE</option><option>NL</option><option>ES</option><option>NO1</option><option>NO2</option><option>CH</option>
          </select>
          <input type="date" value={auditDate} onChange={(e) => setAuditDate(e.target.value)} />
        </div>
        <DataTable data={audit.data ?? []} columns={columns} />
      </Panel>

      <Panel title="OPENLINK DISPLACEMENT MAP" region="europe">
        <pre className="font-data text-sm">OPENLINK ENDUR {'->'} NEXUS INTELLIGENCE LAYER {'->'} GENIE / API</pre>
      </Panel>
    </div>
  );
}
