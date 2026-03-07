import { Link } from '@tanstack/react-router';
import { useCurrentPrices } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';
const cards = [
  { code: 'NEM', market: 'NEM' as const, name: 'Australia / NEM', operators: 'AEMO', path: '/nem', color: 'var(--color-region-anz)', context: ['5-min dispatch intervals', 'BESS fleet: 8 assets', 'FCAS markets active'] },
  { code: 'EPEX', market: 'EPEX' as const, name: 'Europe / EPEX', operators: 'EPEX, ENTSO-E', path: '/epex', color: 'var(--color-region-europe)', context: ['15-min MTU transition', 'Cross-border flow monitoring', 'ETS-linked spark spreads'] },
  { code: 'ERCOT', market: 'ERCOT' as const, name: 'Americas / ERCOT', operators: 'ERCOT, PJM, IESO, CAISO', path: '/ercot', color: 'var(--color-region-americas)', context: ['Multi-ISO normalisation', 'RTC+B market change', 'IESO nodal launch'] },
];

export function RegionSelector(): JSX.Element {
  const setMarket = useTradingStore((s) => s.setMarket);
  const prices = useCurrentPrices();

  const marketLabel = (market: 'NEM' | 'EPEX' | 'ERCOT'): string => {
    if (market === 'NEM') {
      return 'ANZ';
    }
    if (market === 'EPEX') {
      return 'EU';
    }
    return 'US';
  };

  const marketPrice = (market: 'NEM' | 'EPEX' | 'ERCOT'): string => {
    const rows = (prices.data ?? []).filter((row) => row.market === marketLabel(market));
    if (!rows.length) {
      return '--';
    }
    const avg = rows.reduce((sum, row) => sum + row.price, 0) / rows.length;
    return avg.toFixed(2);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 'var(--space-8)', background: 'var(--color-bg-void)' }}>
      <div style={{ width: '100%', maxWidth: 1240 }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
          <div className="font-data" style={{ letterSpacing: '0.22em', fontWeight: 600, color: 'var(--color-accent)', fontSize: 'var(--text-3xl)' }}>APEX</div>
          <div className="text-xs" style={{ color: 'var(--color-text-primary)', marginTop: 6, letterSpacing: 'var(--tracking-wider)', textTransform: 'uppercase', fontWeight: 600 }}>Select Market Workspace</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)' }}>
          {cards.map((c) => (
            <Link
              key={c.code}
              to={c.path}
              onClick={() => setMarket(c.market)}
              style={{
                border: '1px solid var(--color-border-default)',
                background: 'var(--color-bg-panel)',
                borderRadius: '6px',
                padding: 'var(--space-5)',
                display: 'block',
                textDecoration: 'none',
              }}
            >
              <div className="font-data" style={{ color: c.color, fontSize: 'var(--text-3xl)', fontWeight: 600 }}>{c.code}</div>
              <div className="text-md" style={{ marginTop: 8, color: 'var(--color-text-primary)', fontWeight: 600 }}>{c.name}</div>
              <div className="text-sm" style={{ marginTop: 4, color: 'var(--color-text-primary)' }}>{c.operators}</div>
              <ul style={{ marginTop: 12, paddingLeft: 16, color: 'var(--color-text-primary)' }}>
                {c.context.map((it) => <li key={it} className="text-xs" style={{ marginBottom: 4 }}>{it}</li>)}
              </ul>
              <div style={{ borderTop: '1px solid var(--color-border-subtle)', marginTop: 14, paddingTop: 10 }}>
                <span className="label-caps" style={{ color: 'var(--color-text-primary)' }}>Enter Market</span>
              </div>
            </Link>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 18, marginTop: 18 }}>
          {cards.map((card) => (
            <div key={`${card.code}-status`} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-primary)', fontSize: 12 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-positive)', display: 'inline-block' }} />
              <span>{card.code}</span>
              <span className="font-data">{marketPrice(card.market)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
