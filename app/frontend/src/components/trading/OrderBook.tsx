type Level = { price: number; volume: number; cumulative: number };

export function OrderBook({
  bids,
  offers,
  spread,
  lastTradePrice,
}: {
  bids: Level[];
  offers: Level[];
  spread: number;
  lastTradePrice: number;
}): JSX.Element {
  const depthMax = Math.max(
    1,
    ...bids.map((b) => b.cumulative),
    ...offers.map((o) => o.cumulative),
  );
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 1fr', gap: 'var(--space-2)' }}>
      <div>
        <div className="label-caps" style={{ marginBottom: 'var(--space-2)' }}>Bids</div>
        {bids.map((row) => (
          <div key={`b-${row.price}`} style={{ display: 'grid', gridTemplateColumns: '70px 1fr 50px', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div className="mono-price bid">{row.price.toFixed(2)}</div>
            <div style={{ background: 'var(--color-bid-dim)', height: 12, width: `${Math.max(8, (row.cumulative / depthMax) * 100)}%` }} />
            <div className="mono-mw">{row.volume.toFixed(1)}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'grid', alignContent: 'center', justifyItems: 'center', gap: 4 }}>
        <div className="font-data tabular" style={{ fontSize: 'var(--text-xl)' }}>{lastTradePrice.toFixed(2)}</div>
        <div className="text-secondary" style={{ fontSize: 'var(--text-xs)' }}>Spread {spread.toFixed(2)}</div>
      </div>
      <div>
        <div className="label-caps" style={{ marginBottom: 'var(--space-2)' }}>Offers</div>
        {offers.map((row) => (
          <div key={`o-${row.price}`} style={{ display: 'grid', gridTemplateColumns: '50px 1fr 70px', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div className="mono-mw">{row.volume.toFixed(1)}</div>
            <div style={{ background: 'var(--color-offer-dim)', height: 12, width: `${Math.max(8, (row.cumulative / depthMax) * 100)}%` }} />
            <div className="mono-price offer">{row.price.toFixed(2)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
