import { createColumnHelper } from '@tanstack/react-table';

import { useIESONodalBasis, useMultiISORowCount, usePJMCapacityAuctions } from '@/api/hooks/americas';
import { DataTable, Metric, Panel, StatusBadge } from '@/components/primitives';

const helper = createColumnHelper<Record<string, any>>();

export function AmericasETRMPositioning(): JSX.Element {
  const auctions = usePJMCapacityAuctions();
  const ieso = useIESONodalBasis();
  const rows = useMultiISORowCount();

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="PJM CAPACITY AUCTIONS" region="americas">
        <DataTable
          data={auctions.data ?? []}
          columns={[
            helper.accessor('delivery_year', { header: 'DELIVERY YEAR' }),
            helper.accessor('clearing_price_mw_day', { header: 'PRICE MW-DAY' }),
            helper.accessor('total_cost_billions', { header: 'TOTAL COST B' }),
            helper.accessor('data_center_cost_pct', { header: 'DATA CENTER %' }),
            helper.accessor('price_cap_hit', {
              header: 'CAP HIT',
              cell: (i) => <StatusBadge status={i.getValue() ? 'critical' : 'active'} label={i.getValue() ? 'TRUE' : 'FALSE'} />,
            }),
            helper.accessor('reliability_shortfall_mw', { header: 'SHORTFALL MW' }),
          ]}
        />
      </Panel>

      <Panel title="IESO ONTARIO - GREENFIELD NODAL MARKET" region="americas">
        <Metric label="NODAL MARKET AGE" value="< 12 MONTHS" unit="SINCE MRP LAUNCH" />
        <div className="label-caps" style={{ marginTop: 8 }}>DATA AVAILABLE FROM</div>
        <div className="font-data text-xl">2025-05-01</div>
        <DataTable
          data={(ieso.data ?? []).slice(0, 5)}
          columns={[
            helper.accessor('node_name', { header: 'NODE' }),
            helper.accessor('avg_basis_spread', { header: 'AVG BASIS' }),
            helper.accessor('max_basis_spread', { header: 'MAX BASIS' }),
            helper.accessor('pct_hours_positive', { header: 'PCT POSITIVE' }),
          ]}
        />
      </Panel>

      <Panel title="MULTI-ISO NORMALISATION DEMO" region="americas">
        <pre className="font-data text-xs">PJM DataMiner2 {'->'}
ERCOT MIS {'->'} NEXUS UNIFIED LMP TABLE {'->'} GENIE SPACE
CAISO OASIS {'->'} {'                        '} {'->'} TRADING API</pre>
        <div className="font-data text-xs">Total rows: {rows.data ?? 0}</div>
      </Panel>
    </div>
  );
}
