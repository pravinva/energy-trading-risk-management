import { useEffect, useMemo, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import toast, { Toaster } from 'react-hot-toast';
import { DataTable, Panel } from '@/components/primitives';
import { ConfirmationToast, PriceTicker } from '@/components/trading';
import { useCreateTrade, useExposureHeatmap, useInstrumentQuote, useMarketInstruments, useMarketTradeBlotter, usePositions, useTradeCounterparties } from '@/api/hooks/apex';
import { useUserContext } from '@/api/hooks/useUserContext';
import { useTradingStore } from '@/store/tradingStore';

type BlotterRow = {
  trade_id: string;
  instrument: string;
  side: string;
  volume_mw: number;
  price: number;
  mtm_pnl: number;
  trade_time: string;
};

export function TradingBlotter(): JSX.Element {
  const [volume, setVolume] = useState(0);
  const [price, setPrice] = useState(0);
  const [counterparty, setCounterparty] = useState('');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const traderName = useTradingStore((s) => s.traderName);
  const market = useTradingStore((s) => s.market);
  const selectedInstrument = useTradingStore((s) => s.selectedInstrument);
  const setSelectedInstrument = useTradingStore((s) => s.setSelectedInstrument);
  const setTraderName = useTradingStore((s) => s.setTraderName);
  const user = useUserContext();
  const trade = useCreateTrade();
  const blotter = useMarketTradeBlotter(market);
  const positions = usePositions();
  const heatmap = useExposureHeatmap(market);
  const instrumentsQuery = useMarketInstruments(market);
  const counterpartiesQuery = useTradeCounterparties(market);
  const quote = useInstrumentQuote(market, selectedInstrument);

  const columns = useMemo<ColumnDef<BlotterRow>[]>(
    () => [
      { header: 'Trade ID', accessorKey: 'trade_id' },
      { header: 'Instrument', accessorKey: 'instrument' },
      { header: 'Side', accessorKey: 'side' },
      { header: 'MW', accessorKey: 'volume_mw', meta: { kind: 'mw' } },
      { header: 'Price', accessorKey: 'price', meta: { kind: 'price' } },
      { header: 'MTM', accessorKey: 'mtm_pnl', meta: { kind: 'price' } },
    ],
    [],
  );

  const instruments = (instrumentsQuery.data ?? []).map((r) => r.instrument);
  const heatmapRows = useMemo(() => (heatmap.data ?? []).filter((r) => instruments.includes(r.instrument)), [heatmap.data, instruments]);
  const totalMtm = (blotter.data ?? []).reduce((sum, row) => sum + row.mtm_pnl, 0);
  const counterparties = (counterpartiesQuery.data ?? []).map((r) => r.counterparty);

  useEffect(() => {
    if (instruments.length > 0 && !instruments.includes(selectedInstrument)) {
      setSelectedInstrument(instruments[0]);
    }
  }, [instruments, selectedInstrument, setSelectedInstrument]);

  useEffect(() => {
    if (quote.data?.last_price) {
      setPrice(Number(quote.data.last_price.toFixed(2)));
    }
  }, [quote.data?.last_price]);

  useEffect(() => {
    if (!counterparty && counterparties.length > 0) {
      setCounterparty(counterparties[0]);
    }
  }, [counterparty, counterparties]);

  useEffect(() => {
    const email = (user.data as { data?: { email?: string } } | undefined)?.data?.email ?? '';
    const inferred = email.split('@')[0];
    if (!traderName && inferred.length >= 2) {
      setTraderName(inferred);
    }
  }, [setTraderName, traderName, user.data]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '292px 1fr', gridTemplateRows: '1fr 1fr', gap: 10, minHeight: 540 }}>
      <Toaster position="top-right" />
      <Panel persona="trader" title="Net Exposure Heatmap" subtitle={`${market} region-period risk`}>
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
        <div style={{ marginTop: 10, fontSize: 11, color: 'var(--color-text-secondary)' }}>Derived from live position book and market-selected instruments.</div>
      </Panel>

      <Panel persona="trader" title="Position Book" subtitle={`${market} positions with MTM`}>
        <div style={{ display: 'grid', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(0, 1fr))', gap: 8 }}>
            <select value={selectedInstrument} onChange={(e) => setSelectedInstrument(e.target.value)}>
              {instruments.map((v) => <option key={v}>{v}</option>)}
            </select>
            <select value={side} onChange={(e) => setSide(e.target.value as 'BUY' | 'SELL')}>
              <option>BUY</option>
              <option>SELL</option>
            </select>
            <input className="mono-mw" value={volume} onChange={(e) => setVolume(Number(e.target.value))} />
            <input className="mono-price" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
            <select value={counterparty} onChange={(e) => setCounterparty(e.target.value)}>
              {counterparties.map((v) => <option key={v}>{v}</option>)}
            </select>
            <button
              disabled={!selectedInstrument || !counterparty || !traderName || volume <= 0 || price <= 0}
              onClick={() => {
                trade.mutate(
                  { trader: traderName, instrument: selectedInstrument, side, volume_mw: volume, price, counterparty },
                  {
                    onSuccess: () => {
                      toast.custom(() => <ConfirmationToast side={side} instrument={selectedInstrument} volumeMw={volume} price={price} />);
                    },
                  },
                );
              }}
            >
              Submit Trade
            </button>
          </div>
          <DataTable data={positions.data ?? []} columns={[{ header: 'Instrument', accessorKey: 'instrument' }, { header: 'Net MW', accessorKey: 'net_position_mw', meta: { kind: 'mw' } }, { header: 'Avg Px', accessorKey: 'avg_trade_price', meta: { kind: 'price' } }]} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <span className="label-caps">Total Unrealised MTM</span>
            <span className="font-data" style={{ color: totalMtm >= 0 ? 'var(--color-positive)' : 'var(--color-negative)' }}>{totalMtm.toFixed(2)}</span>
          </div>
        </div>
      </Panel>
      {quote.data ? (
        <div style={{ gridColumn: '2 / 3' }}>
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
        </div>
      ) : null}
      <Panel persona="trader" title="Trade Blotter" subtitle={`${market} trade ingestion view`}>
        <DataTable data={blotter.data ?? []} columns={columns} />
      </Panel>
    </div>
  );
}
