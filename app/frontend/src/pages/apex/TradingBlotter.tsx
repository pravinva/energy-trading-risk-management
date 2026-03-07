import { useMemo, useState } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import toast, { Toaster } from 'react-hot-toast';
import { DataTable, Panel } from '@/components/primitives';
import { ConfirmationToast, PriceTicker } from '@/components/trading';
import { useCreateTrade, useCurrentPrices, usePositions, useTradeBlotter } from '@/api/hooks/apex';
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
  const [volume, setVolume] = useState(10);
  const [price, setPrice] = useState(95);
  const [counterparty, setCounterparty] = useState('GridRetail');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const traderName = useTradingStore((s) => s.traderName);
  const selectedInstrument = useTradingStore((s) => s.selectedInstrument);
  const setSelectedInstrument = useTradingStore((s) => s.setSelectedInstrument);
  const trade = useCreateTrade();
  const blotter = useTradeBlotter();
  const positions = usePositions();
  const prices = useCurrentPrices();

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

  const ticker = prices.data?.find((p) => p.instrument === selectedInstrument) ?? prices.data?.[0];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Toaster position="top-right" />
      <Panel persona="trader" title="Trade Entry" subtitle="Deal capture and confirmation">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(0, 1fr))', gap: 8 }}>
          <select value={selectedInstrument} onChange={(e) => setSelectedInstrument(e.target.value)}>
            {['NSW_BASE', 'VIC_PEAK', 'FCAS_RAISE6SEC', 'ERCOT_HOUSTON', 'DE-LU_BASE'].map((v) => <option key={v}>{v}</option>)}
          </select>
          <select value={side} onChange={(e) => setSide(e.target.value as 'BUY' | 'SELL')}>
            <option>BUY</option>
            <option>SELL</option>
          </select>
          <input className="mono-mw" value={volume} onChange={(e) => setVolume(Number(e.target.value))} />
          <input className="mono-price" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
          <input value={counterparty} onChange={(e) => setCounterparty(e.target.value)} />
          <button
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
      </Panel>
      {ticker ? (
        <PriceTicker
          instrument={ticker.instrument}
          lastPrice={ticker.price}
          change={(ticker.price * ticker.change_pct) / 100}
          changePct={ticker.change_pct}
          bid={ticker.price - 0.25}
          offer={ticker.price + 0.25}
          volume={245.2}
          status="OPEN"
        />
      ) : null}
      <Panel persona="trader" title="Trading Blotter">
        <DataTable data={blotter.data ?? []} columns={columns} />
      </Panel>
      <Panel persona="trader" title="Position Book">
        <DataTable data={positions.data ?? []} columns={[{ header: 'Instrument', accessorKey: 'instrument' }, { header: 'Net MW', accessorKey: 'net_position_mw', meta: { kind: 'mw' } }, { header: 'Avg Px', accessorKey: 'avg_trade_price', meta: { kind: 'price' } }]} />
      </Panel>
    </div>
  );
}
