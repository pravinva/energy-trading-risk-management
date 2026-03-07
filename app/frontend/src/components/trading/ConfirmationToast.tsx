export function ConfirmationToast({
  side,
  instrument,
  volumeMw,
  price,
}: {
  side: 'BUY' | 'SELL';
  instrument: string;
  volumeMw: number;
  price: number;
}): JSX.Element {
  return (
    <div style={{ border: '1px solid var(--color-border-default)', background: 'var(--color-bg-raised)', padding: 'var(--space-3)', minWidth: 280 }}>
      <div className="label-caps" style={{ marginBottom: 6 }}>Trade Confirmed</div>
      <div style={{ display: 'grid', gap: 2 }}>
        <div><span className={side === 'BUY' ? 'bid' : 'offer'}>{side}</span> {instrument}</div>
        <div className="font-data">{volumeMw.toFixed(2)} MW @ {price.toFixed(2)} $/MWh</div>
      </div>
    </div>
  );
}
