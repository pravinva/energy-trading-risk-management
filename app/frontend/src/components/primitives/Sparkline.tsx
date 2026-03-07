export function Sparkline({ data, width = 80, height = 24, positive, strokeWidth = 1.5 }: { data: number[]; width?: number; height?: number; positive: boolean; strokeWidth?: number }): JSX.Element {
  if (data.length === 0) return <svg width={width} height={height} />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const points = data.map((d, i) => `${(i / Math.max(1, data.length - 1)) * width},${height - ((d - min) / span) * height}`).join(' ');
  return <svg width={width} height={height}><polyline fill="none" stroke={positive ? 'var(--color-positive)' : 'var(--color-negative)'} strokeWidth={strokeWidth} points={points} /></svg>;
}
