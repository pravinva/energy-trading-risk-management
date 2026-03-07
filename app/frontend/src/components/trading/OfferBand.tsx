import Decimal from 'decimal.js';

export function OfferBand({
  bandIndex,
  price,
  volume,
  isSelected,
  onPriceChange,
  onVolumeChange,
  onSelect,
}: {
  bandIndex: number;
  price: number;
  volume: number;
  isSelected: boolean;
  onPriceChange: (v: number) => void;
  onVolumeChange: (v: number) => void;
  onSelect: () => void;
}): JSX.Element {
  const validateDecimal = (value: string, fallback: number): number => {
    try {
      const parsed = new Decimal(value);
      return Number(parsed.toFixed(2));
    } catch {
      return fallback;
    }
  };

  return (
    <div onClick={onSelect} style={{ display: 'grid', gridTemplateColumns: '60px 1fr 1fr', gap: 8, padding: 'var(--space-2)', border: '1px solid var(--color-border-subtle)', background: isSelected ? 'var(--color-bg-raised)' : 'var(--color-bg-base)', cursor: 'pointer' }}>
      <div className="label-caps">Band {bandIndex}</div>
      <input
        className="mono-price"
        value={price}
        onChange={(e) => onPriceChange(validateDecimal(e.target.value, price))}
      />
      <input
        className="mono-mw"
        value={volume}
        onChange={(e) => onVolumeChange(Math.max(0, validateDecimal(e.target.value, volume)))}
      />
    </div>
  );
}
