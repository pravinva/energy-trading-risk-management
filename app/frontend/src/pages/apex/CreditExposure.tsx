import { DataTable, Panel } from '@/components/primitives';
import { useCreditExposure, usePositions } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

export function CreditExposure(): JSX.Element {
  const market = useTradingStore((s) => s.market);
  const exposure = useCreditExposure(market);
  const positions = usePositions();
  const exposureRows = exposure.data ?? [];
  const totalGrossExposure = exposureRows.reduce((sum, row) => sum + row.gross_mw, 0);
  const netPosition = (positions.data ?? []).reduce((sum, row) => sum + row.net_position_mw, 0);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="risk" title="Credit Exposure" subtitle="Counterparty-style concentration from live deal flow">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          <div className="font-data">Gross Exposure (MW): {totalGrossExposure.toFixed(2)}</div>
          <div className="font-data">Net Position (MW): {netPosition.toFixed(2)}</div>
        </div>
      </Panel>
      <Panel persona="risk" title="Exposure Breakdown">
        <DataTable
          data={exposureRows}
          columns={[
            { header: 'Group', accessorKey: 'counterparty' },
            { header: 'Trades', accessorKey: 'trades' },
            { header: 'Gross MW', accessorKey: 'gross_mw', meta: { kind: 'mw' } },
            { header: 'MTM', accessorKey: 'mtm_pnl', meta: { kind: 'price' } },
          ]}
        />
      </Panel>
    </div>
  );
}
