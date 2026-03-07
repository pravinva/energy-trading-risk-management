import { createColumnHelper } from '@tanstack/react-table';
import { useGTMSignals, useGTMStatus } from '@/api/hooks/useGTMSignals';
import { DataTable, Panel, StatusBadge } from '@/components/primitives';

const helper = createColumnHelper<Record<string, string | number>>();
const columns = [
  helper.accessor('account', { header: 'ACCOUNT' }),
  helper.accessor('arr', { header: 'ARR/MO' }),
  helper.accessor('signal', { header: 'SIGNAL TYPE' }),
  helper.accessor('play', { header: 'RECOMMENDED PLAY' }),
  helper.accessor('urgency', { header: 'URGENCY', cell: (i) => {
    const value = String(i.getValue());
    const status = value === 'HIGH' ? 'critical' : value === 'MED' ? 'warning' : 'inactive';
    return <StatusBadge status={status} label={value} />;
  } }),
  helper.accessor('owner', { header: 'ACCOUNT OWNER' }),
];

export function GTMSignalBoard({ region, isEmployee }: { region: string; isEmployee: boolean }): JSX.Element | null {
  const status = useGTMStatus();
  const available = Boolean(status.data?.available);
  const signals = useGTMSignals(region, isEmployee && available);
  if (!isEmployee || !available) return null;
  return (
    <Panel title={`GTM SIGNAL BOARD - ${region.toUpperCase()}`}>
      <div className="label-caps" style={{ color: 'var(--color-warning)', marginBottom: 8 }}>INTERNAL - NOT VISIBLE TO CUSTOMERS</div>
      <DataTable data={signals.data ?? []} columns={columns} />
    </Panel>
  );
}
