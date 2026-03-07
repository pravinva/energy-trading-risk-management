import { Link } from '@tanstack/react-router';
import { useMemo } from 'react';
import { useHealth } from '@/api/hooks/useHealth';
import { useUserContext } from '@/api/hooks/useUserContext';
import { GTMSignalBoard } from '@/components/GTMSignalBoard';
import { StatusBadge } from '@/components/primitives';

export function RegionalLayout({ region, regionLabel, navItems, children }: { region: 'anz' | 'europe' | 'americas'; regionLabel: string; navItems: { path: string; label: string }[]; children: JSX.Element }): JSX.Element {
  const health = useHealth();
  const user = useUserContext();
  const timeString = useMemo(() => new Date().toLocaleTimeString(), [health.data]);
  const employee = Boolean(user.data?.is_databricks_employee);
  return (
    <div style={{ minHeight: '100vh', display: 'grid', gridTemplateRows: '44px 1fr' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--color-bg-elevated)', borderBottom: '1px solid var(--color-border-subtle)', padding: '0 var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Link to="/" className="font-data">NEXUS</Link><span className="text-secondary">|</span><span className="label-caps" style={{ color: `var(--color-region-${region})` }}>{regionLabel}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <StatusBadge status={health.data?.status === 'ok' ? 'active' : 'warning'} label={health.data?.status === 'ok' ? 'CONNECTED' : 'DEGRADED'} />
          <span className="font-data text-xs">LAST UPDATE: {timeString}</span>
          {employee && <StatusBadge status="warning" label="INTERNAL" />}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr' }}>
        <aside style={{ borderRight: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-base)', paddingTop: 8 }}>
          {navItems.map((item) => <Link key={item.path} to={item.path} style={{ display: 'block', padding: '10px 12px', borderLeft: '2px solid transparent' }} className="label-caps">{item.label}</Link>)}
        </aside>
        <main style={{ padding: 'var(--space-6)', display: 'grid', gap: 'var(--space-4)' }}>
          <GTMSignalBoard region={region} isEmployee={employee} />
          {children}
        </main>
      </div>
    </div>
  );
}
