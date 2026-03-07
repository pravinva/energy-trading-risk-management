import { Link } from '@tanstack/react-router';
import { useTradingStore } from '@/store/tradingStore';

const personas = ['dispatch', 'trader', 'risk', 'quant', 'portfolio'] as const;

const personaConfig: Record<'NEM' | 'EPEX' | 'ERCOT', Record<(typeof personas)[number], { label: string; desc: string; features: string[] }>> = {
  NEM: {
    dispatch: {
      label: 'Dispatch Analyst',
      desc: 'Monitor NEM BESS fleet and analyze stack outcomes across FCAS and energy services.',
      features: ['FCAS stack analytics - 7 services', 'AEMO 5-min dispatch intervals', 'Forecast-backed recommendation insights'],
    },
    trader: {
      label: 'Trading Analyst',
      desc: 'Track live positions, blotter, and mark-to-market across NEM regions.',
      features: ['NSW/VIC/QLD/SA strip', 'ALIGNE_SIM ingestion', 'P&L attribution'],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Analyze VaR Monte Carlo and monitor portfolio limits with NEM event stress tests.',
      features: ['Monte Carlo 10,000 paths', 'Spike scenario testing', 'Credit + limit surveillance'],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Evaluate forecast quality and backtest signal strategies for NEM markets.',
      features: ['Forecast error analysis', 'Feature importance', 'Backtest strategy tabs'],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Model revenue stacking and evaluate PPA book exposure across the NEM portfolio.',
      features: ['Revenue simulator', 'PPA MTM view', 'Fleet benchmark'],
    },
  },
  EPEX: {
    dispatch: {
      label: 'Dispatch Analyst',
      desc: 'Analyze EPEX battery dispatch with energy and balancing reserve services.',
      features: ['15-min MTU context', 'Balancing reserve focus', 'ENDUR_SIM provenance'],
    },
    trader: {
      label: 'Trading Analyst',
      desc: 'Analyze EPEX positions and blotter exposure across core bidding zones.',
      features: ['DE-LU/FR/BE spread view', 'EPEX price strip', 'Source-aligned position book'],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Analyze EUR VaR and stress outcomes for cold snap and renewable flood events.',
      features: ['EUR portfolio VaR', 'Scenario impact cards', 'Limit and breach monitor'],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Evaluate EPEX model behavior and backtests with MTU transition awareness.',
      features: ['Post-MTU model drift', 'Signal comparison', 'FCAS strategy disabled (NEM only)'],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Review EPEX revenue drivers and PPA contracts with European counterparties.',
      features: ['Equinor/RWE/EDF PPA book', 'EUR revenue stack', 'Portfolio benchmarking'],
    },
  },
  ERCOT: {
    dispatch: {
      label: 'Dispatch Analyst',
      desc: 'Analyze ERCOT dispatch with RTC+B-aware offer stack behavior.',
      features: ['RTC+B context', 'ENERGY/REG/ECRS services', 'Texas fleet controls'],
    },
    trader: {
      label: 'Trading Analyst',
      desc: 'Track nodal exposure and trade flow for ERCOT hubs and basis dynamics.',
      features: ['Houston/West/North nodes', 'TRIPLE_POINT_SIM source', 'USD mark-to-market'],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Analyze USD VaR and stress against summer scarcity and wind-drop scenarios.',
      features: ['USD VaR metrics', 'Scarcity stress set', 'Credit concentration tracking'],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Assess model behavior with RTC+B regime changes and strategy performance.',
      features: ['RTC+B-aware signals', 'Backtest comparison', 'Forecast accuracy tracking'],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Simulate ERCOT revenue composition and review Texas PPA hedge exposure.',
      features: ['Vistra/NRG/Calpine PPAs', 'ECRS + ancillary stack', 'Fleet revenue ranking'],
    },
  },
};

export function PersonaSelector(): JSX.Element {
  const setPersona = useTradingStore((s) => s.setPersona);
  const market = useTradingStore((s) => s.market);
  return (
    <div className="persona-wrap">
      <div style={{ padding: '10px 4px 14px', fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)' }}>
        Persona Selector · {market}
      </div>
      <div className="persona-grid">
          {personas.map((p) => (
            <Link
              key={p}
              to={`/workspace/${p === 'trader' ? 'trading' : p}`}
              onClick={() => setPersona(p)}
              className={`persona-card ${p}`}
            >
              <div className="persona-role">{personaConfig[market][p].label}</div>
              <div className="persona-fn">{p === 'trader' ? 'Trading Analytics' : p === 'risk' ? 'Risk Dashboard' : p === 'dispatch' ? 'Dispatch Console' : p === 'quant' ? 'Quant Console' : 'Portfolio Dashboard'}</div>
              <div className="persona-desc">{personaConfig[market][p].desc}</div>
              <div style={{ display: 'grid', gap: 2, marginBottom: 10 }}>
                {personaConfig[market][p].features.map((feature) => (
                  <div key={feature} className="text-xs" style={{ color: 'var(--color-text-primary)' }}>{feature}</div>
                ))}
              </div>
              <div className="persona-enter">Enter Workspace</div>
            </Link>
          ))}
      </div>
    </div>
  );
}
