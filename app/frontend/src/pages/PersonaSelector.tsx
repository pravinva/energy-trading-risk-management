import { Link } from '@tanstack/react-router';
import { Panel } from '@/components/primitives';
import { useTradingStore } from '@/store/tradingStore';

const personas = [
  { key: 'dispatch', label: 'Dispatch Operator', desc: 'Build offer stacks and execute dispatch actions.' },
  { key: 'trader', label: 'Power Trader', desc: 'Enter trades, monitor blotter and live P&L.' },
  { key: 'risk', label: 'Risk Manager', desc: 'Run VaR, monitor limits and stress outcomes.' },
  { key: 'quant', label: 'Quant Developer', desc: 'Inspect model metrics and backtests.' },
  { key: 'portfolio', label: 'Portfolio Manager', desc: 'Track revenue stacking and PPA exposure.' },
] as const;

export function PersonaSelector(): JSX.Element {
  const setPersona = useTradingStore((s) => s.setPersona);
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 'var(--space-6)' }}>
      <div style={{ width: 'min(1000px, 95vw)', display: 'grid', gap: 'var(--space-4)' }}>
        <h1 style={{ fontSize: 'var(--text-xl)' }}>APEX Persona Workspace</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 'var(--space-3)' }}>
          {personas.map((p) => (
            <Link key={p.key} to={`/workspace/${p.key === 'trader' ? 'trading' : p.key}`} onClick={() => setPersona(p.key)}>
              <Panel persona={p.key} title={p.label} subtitle={p.desc}>
                <div className="label-caps">Enter Workspace</div>
              </Panel>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
