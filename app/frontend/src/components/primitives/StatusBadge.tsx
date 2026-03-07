const statusMap = {
  active: { color: 'var(--color-positive)', bg: 'var(--color-positive-dim)' },
  warning: { color: 'var(--color-warning)', bg: 'var(--color-warning-dim)' },
  critical: { color: 'var(--color-negative)', bg: 'var(--color-negative-dim)' },
  inactive: { color: 'var(--color-text-tertiary)', bg: 'var(--color-bg-elevated)' },
  neutral: { color: 'var(--color-text-secondary)', bg: 'var(--color-bg-elevated)' },
} as const;

export function StatusBadge({ status, label }: { status: 'active' | 'warning' | 'critical' | 'inactive' | 'neutral'; label: string }): JSX.Element {
  const m = statusMap[status];
  return <span className="label-caps" style={{ color: m.color, background: m.bg, border: '1px solid var(--color-border-subtle)', padding: '2px 6px' }}>{label.toUpperCase()}</span>;
}
