export function Metric({ label, value, unit, change, changeLabel, size = 'md' }: { label: string; value: string | number; unit?: string; change?: number; changeLabel?: string; size?: 'sm' | 'md' | 'lg' }): JSX.Element {
  const sizeMap = { sm: 'var(--text-lg)', md: 'var(--text-2xl)', lg: 'var(--text-3xl)' };
  const changeColor = typeof change === 'number' && change < 0 ? 'var(--color-negative)' : 'var(--color-positive)';
  return (
    <div>
      <div className="label-caps">{label}</div>
      <div className="font-data text-tabular" style={{ fontSize: sizeMap[size], fontWeight: 600 }}>{value} {unit ?? ''}</div>
      {typeof change === 'number' && <div style={{ color: changeColor }}>{changeLabel ?? 'Change'}: {change}</div>}
    </div>
  );
}
