import { useEffect, useMemo } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { DataTable, Panel } from '@/components/primitives';
import { PriceTicker } from '@/components/trading';
import { useExposureHeatmap, useInstrumentQuote, useMarketInstruments, useMarketTradeBlotter, usePositions } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

type BlotterRow = {
  trade_id: string;
  instrument: string;
  direction: string;
  volume_mw: number;
  price: number;
  mtm_pnl: number;
  trade_time: string;
};

export function TradingBlotter(): JSX.Element {
  const market = useTradingStore((s) => s.market);
  const selectedInstrument = useTradingStore((s) => s.selectedInstrument);
  const setSelectedInstrument = useTradingStore((s) => s.setSelectedInstrument);
  const blotter = useMarketTradeBlotter(market);
  const positions = usePositions();
  const heatmap = useExposureHeatmap(market);
  const instrumentsQuery = useMarketInstruments(market);
  const quote = useInstrumentQuote(market, selectedInstrument);

  const columns = useMemo<ColumnDef<BlotterRow>[]>(
    () => [
      { header: 'Trade ID', accessorKey: 'trade_id' },
      { header: 'Instrument', accessorKey: 'instrument' },
      { header: 'Direction', accessorKey: 'direction' },
      { header: 'MW', accessorKey: 'volume_mw', meta: { kind: 'mw' } },
      { header: 'Price', accessorKey: 'price', meta: { kind: 'price' } },
      { header: 'MTM', accessorKey: 'mtm_pnl', meta: { kind: 'price' } },
    ],
    [],
  );

  const instruments = (instrumentsQuery.data ?? []).map((r) => r.instrument);
  const heatmapRows = useMemo(() => (heatmap.data ?? []).filter((r) => instruments.includes(r.instrument)), [heatmap.data, instruments]);
  const blotterRows: BlotterRow[] = useMemo(
    () =>
      (blotter.data ?? []).map((row) => ({
        trade_id: row.trade_id,
        instrument: row.instrument,
        direction: row.side === 'BUY' ? 'Long Flow' : row.side === 'SELL' ? 'Short Flow' : row.side,
        volume_mw: row.volume_mw,
        price: row.price,
        mtm_pnl: row.mtm_pnl,
        trade_time: row.trade_time,
      })),
    [blotter.data],
  );
  const totalMtm = blotterRows.reduce((sum, row) => sum + row.mtm_pnl, 0);
  const tradeCount = blotterRows.length;
  const grossMw = blotterRows.reduce((sum, row) => sum + Math.abs(row.volume_mw), 0);
  const avgPrintPx = tradeCount > 0 ? blotterRows.reduce((sum, row) => sum + row.price, 0) / tradeCount : 0;

  useEffect(() => {
    if (instruments.length > 0 && !instruments.includes(selectedInstrument)) {
      setSelectedInstrument(instruments[0]);
    }
  }, [instruments, selectedInstrument, setSelectedInstrument]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '292px 1fr', gridTemplateRows: 'auto auto', gap: 10, minHeight: 540 }}>
      <Panel persona="trader" title="Flow Summary" subtitle={`${market} trading analytics`}>
        <div className="font-data" style={{ marginBottom: 6 }}>Prints: {tradeCount}</div>
        <div className="font-data" style={{ marginBottom: 6 }}>Gross MW: {grossMw.toFixed(2)}</div>
        <div className="font-data" style={{ marginBottom: 6 }}>Avg Print Px: {avgPrintPx.toFixed(2)}</div>
        <div className="font-data" style={{ color: totalMtm >= 0 ? 'var(--color-positive)' : 'var(--color-negative)' }}>
          Total Unrealised MTM: {totalMtm.toFixed(2)}
        </div>
      </Panel>
      <Panel persona="trader" title="Market Snapshot" subtitle={`${market} selected instrument`}>
        <div style={{ marginBottom: 8 }}>
          <select value={selectedInstrument} onChange={(e) => setSelectedInstrument(e.target.value)}>
            {instruments.map((v) => <option key={v}>{v}</option>)}
          </select>
        </div>
        {quote.data ? (
          <PriceTicker
            instrument={quote.data.instrument}
            lastPrice={quote.data.last_price}
            change={(quote.data.last_price * quote.data.change_pct) / 100}
            changePct={quote.data.change_pct}
            bid={quote.data.bid}
            offer={quote.data.offer}
            volume={quote.data.volume}
            status={quote.data.status}
          />
        ) : null}
      </Panel>
      <Panel persona="trader" title="Position Exposure" subtitle={`${market} position book`}>
        <DataTable data={positions.data ?? []} columns={[{ header: 'Instrument', accessorKey: 'instrument' }, { header: 'Net MW', accessorKey: 'net_position_mw', meta: { kind: 'mw' } }, { header: 'Avg Px', accessorKey: 'avg_trade_price', meta: { kind: 'price' } }]} />
      </Panel>
      <Panel persona="trader" title="Net Exposure Heatmap" subtitle={`${market} period risk`}>
        <DataTable
          data={heatmapRows}
          columns={[
            { header: 'Instrument', accessorKey: 'instrument' },
            { header: 'Q1', accessorKey: 'q1' },
            { header: 'Q2', accessorKey: 'q2' },
            { header: 'Q3', accessorKey: 'q3' },
            { header: 'Q4', accessorKey: 'q4' },
          ]}
        />
      </Panel>
      <Panel persona="trader" title="Trading Flow Tape" subtitle={`${market} ingestion analytics`}>
        <DataTable data={blotterRows} columns={columns} />
      </Panel>
    </div>
  );
}
