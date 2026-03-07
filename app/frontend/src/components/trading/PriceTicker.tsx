export function PriceTicker({
  instrument,
  lastPrice,
  change,
  changePct,
  bid,
  offer,
  volume,
  status,
}: {
  instrument: string;
  lastPrice: number;
  change: number;
  changePct: number;
  bid: number;
  offer: number;
  volume: number;
  status: string;
}): JSX.Element {
  const up = change >= 0;
  return (
    <div style={{ border: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-base)', padding: 'var(--space-3)' }}>
      <div className="label-caps" style={{ marginBottom: 6 }}>{instrument}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <div className={`font-data tabular ${up ? 'price-up' : 'price-down'}`} style={{ fontSize: 'var(--text-2xl)' }}>{lastPrice.toFixed(2)}</div>
        <div className={`font-data tabular ${up ? 'price-up' : 'price-down'}`}>{up ? '▲' : '▼'} {change.toFixed(2)} ({changePct.toFixed(2)}%)</div>
      </div>
      <div style={{ marginTop: 'var(--space-2)', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        <div><div className="label-caps">Bid</div><div className="mono-price bid">{bid.toFixed(2)}</div></div>
        <div><div className="label-caps">Offer</div><div className="mono-price offer">{offer.toFixed(2)}</div></div>
        <div><div className="label-caps">Vol</div><div className="mono-mw">{volume.toFixed(1)}</div></div>
        <div><div className="label-caps">Status</div><div className="font-data">{status}</div></div>
      </div>
    </div>
  );
}
