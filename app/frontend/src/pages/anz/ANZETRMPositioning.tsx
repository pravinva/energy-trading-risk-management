import { createColumnHelper } from '@tanstack/react-table';
import { DataTable, Panel, StatusBadge } from '@/components/primitives';
const rows = [['Real-time 5-min dispatch ingestion','critical','active'],['ML price forecasting (MLflow)','warning','active'],['BESS dispatch optimisation model','critical','active'],['SCADA integration','warning','active'],['Self-serve analytics','critical','active'],['Operational state store','warning','active'],['Regulatory audit trail','warning','active'],['Multi-asset revenue stacking','critical','active']];
const helper = createColumnHelper<{ capability: string; legacy: string; dbx: string }>();
export function ANZETRMPositioning(): JSX.Element {
  const data = rows.map((r) => ({ capability: r[0], legacy: r[1], dbx: r[2] }));
  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="ETRM GAP MATRIX" region="anz">
        <DataTable
          data={data}
          columns={[
            helper.accessor('capability', { header: 'CAPABILITY' }),
            helper.accessor('legacy', {
              header: 'LEGACY',
              cell: (i) => <StatusBadge status={i.getValue() as any} label={String(i.getValue()).toUpperCase()} />,
            }),
            helper.accessor('dbx', {
              header: 'DATABRICKS',
              cell: (i) => <StatusBadge status={i.getValue() as any} label={String(i.getValue()).toUpperCase()} />,
            }),
          ]}
        />
      </Panel>
      <Panel title="COST DISPLACEMENT OPPORTUNITY" region="anz">
        <div className="font-data text-3xl">A$200,000 - A$500,000 AUD / yr</div>
      </Panel>
      <Panel title="REFERENCE ARCHITECTURE" region="anz">
        <pre className="font-data text-xs text-secondary">
          PI HISTORIAN {'->'} UNIVERSAL OT CONNECTOR {'->'} DELTA LIVE TABLES {'->'} LAKEBASE {'->'} MLFLOW {'->'} GENIE SPACE
        </pre>
      </Panel>
    </div>
  );
}
