import { Link } from '@tanstack/react-router';
const cards = [
  { code: 'ANZ', name: 'Australia / NEM', operators: 'AEMO', path: '/anz', color: 'var(--color-region-anz)', context: ['5-min dispatch intervals', 'BESS fleet: 8 assets', 'FCAS markets active'] },
  { code: 'EUR', name: 'Europe / EPEX', operators: 'EPEX, ENTSO-E', path: '/europe', color: 'var(--color-region-europe)', context: ['15-min MTU transition', 'Cross-border flow monitoring', 'ETS-linked spark spreads'] },
  { code: 'AMER', name: 'Americas / ISO-RTO', operators: 'ERCOT, PJM, IESO, CAISO', path: '/americas', color: 'var(--color-region-americas)', context: ['Multi-ISO normalisation', 'RTC+B market change', 'IESO nodal launch'] },
];

export function RegionSelector(): JSX.Element {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 'var(--space-8)' }}>
      <div style={{ width: '100%', maxWidth: 1200 }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
          <div className="font-data" style={{ letterSpacing: '0.3em', fontWeight: 300, color: 'var(--color-text-secondary)', fontSize: 'var(--text-3xl)' }}>NEXUS</div>
          <div className="text-xs" style={{ color: 'var(--color-text-tertiary)', marginTop: 4, letterSpacing: 'var(--tracking-wider)' }}>ENERGY TRADING INTELLIGENCE PLATFORM</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)' }}>
          {cards.map((c) => (
            <Link key={c.code} to={c.path} style={{ border: '1px solid var(--color-border-default)', background: 'var(--color-bg-base)', padding: 'var(--space-4)', display: 'block' }}>
              <div className="font-data" style={{ color: c.color, fontSize: 'var(--text-3xl)' }}>{c.code}</div>
              <div className="text-md" style={{ marginTop: 8 }}>{c.name}</div>
              <div className="text-sm text-secondary" style={{ marginTop: 4 }}>{c.operators}</div>
              <ul style={{ marginTop: 10, paddingLeft: 16 }}>{c.context.map((it) => <li key={it} className="text-xs text-tertiary">{it}</li>)}</ul>
              <div style={{ borderTop: '1px solid var(--color-border-subtle)', marginTop: 12, paddingTop: 8 }}><span className="label-caps">MARKET DATA: SIMULATED</span></div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
