import { Link, Outlet, useLocation } from '@tanstack/react-router';
import { useMarketSummary } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

const items = [
  { to: '/workspace/dispatch', label: 'Dispatch', persona: 'dispatch' as const },
  { to: '/workspace/trading', label: 'Trading', persona: 'trader' as const },
  { to: '/workspace/risk', label: 'Risk', persona: 'risk' as const },
  { to: '/workspace/quant', label: 'Quant', persona: 'quant' as const },
  { to: '/workspace/portfolio', label: 'Portfolio', persona: 'portfolio' as const },
];

export function ApexWorkspaceLayout(): JSX.Element {
  const location = useLocation();
  const summary = useMarketSummary();
  const setPersona = useTradingStore((s) => s.setPersona);

  return (
    <div style={{ minHeight: '100vh', display: 'grid', gridTemplateRows: '44px 1fr' }}>
      <header style={{ borderBottom: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-elevated)', padding: '0 var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Link to="/" className="font-data">APEX</Link>
          <span className="text-secondary">|</span>
          <span className="label-caps">Energy Trading & Risk Management</span>
        </div>
        <div className="font-data tabular">Avg Px {summary.data?.average_price?.toFixed(2) ?? '--'}</div>
      </header>
      <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr' }}>
        <aside style={{ borderRight: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-base)', paddingTop: 8 }}>
          {items.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setPersona(item.persona)}
              className="label-caps"
              style={{
                display: 'block',
                padding: '10px 12px',
                borderLeft: location.pathname.startsWith(item.to) ? `2px solid var(--color-persona-${item.persona})` : '2px solid transparent',
                color: location.pathname.startsWith(item.to) ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              }}
            >
              {item.label}
            </Link>
          ))}
        </aside>
        <main style={{ padding: 'var(--space-4)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
