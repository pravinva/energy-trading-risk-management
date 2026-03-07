import { DataTable, Panel } from '@/components/primitives';
import { useLimitStatus } from '@/api/hooks/apex';

export function LimitMonitor(): JSX.Element {
  const limits = useLimitStatus();
  const total = limits.data?.length ?? 0;
  const breached = (limits.data ?? []).filter((row) => row.breached).length;

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="risk" title="Limit Monitor" subtitle="Desk-level surveillance and breach tracking">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          <div className="font-data">Limits Evaluated: {total}</div>
          <div className="font-data">Breaches: {breached}</div>
        </div>
      </Panel>
      <Panel persona="risk" title="Limit Detail">
        <DataTable
          data={limits.data ?? []}
          columns={[
            { header: 'Metric', accessorKey: 'metric' },
            { header: 'Current', accessorKey: 'current', meta: { kind: 'price' } },
            { header: 'Limit', accessorKey: 'limit', meta: { kind: 'price' } },
            { header: 'Breached', accessorKey: 'breached' },
          ]}
        />
      </Panel>
    </div>
  );
}
