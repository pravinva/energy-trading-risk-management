import { Link } from '@tanstack/react-router';
import { useTradingStore } from '@/store/tradingStore';

const personas = ['dispatch', 'trader', 'risk', 'quant', 'portfolio'] as const;

const personaConfig: Record<'NEM' | 'EPEX' | 'ERCOT', Record<(typeof personas)[number], { label: string; desc: string; features: string[] }>> = {
  NEM: {
    dispatch: {
      label: 'Dispatch Operator',
      desc: 'Monitor your NEM BESS fleet, build and submit offer stacks across FCAS and energy services, review ML dispatch recommendations.',
      features: [
        'FCAS offer stacks — 7 services',
        'AEMO 5-min dispatch intervals',
        'SOC monitoring — all NEM assets',
        'NEL good-faith rebid compliance',
      ],
    },
    trader: {
      label: 'Power Trader',
      desc: 'Position book with live AUD MTM P&L, regional exposure heatmap, trade blotter ingested from Aligne ETRM.',
      features: [
        'Net exposure heatmap — 5 NEM regions',
        'Live MTM — AUD mark-to-market',
        'Aligne ingestion via DLT pipeline',
        'ASX futures position tracking',
      ],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Run VaR Monte Carlo, stress test against NEM events including June 2025 SA spike, monitor AUD limit utilisation.',
      features: [
        'VaR Monte Carlo — 10,000 paths AUD',
        '5 NEM historical stress scenarios',
        'SA1 spike limit monitoring',
        'Counterparty credit — NEM participants',
      ],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Model performance monitoring, strategy backtesting across 24 months of NEM 5-min history, FCAS signal analysis.',
      features: [
        'NEM 5-min price forecast — LightGBM',
        'FCAS signal accuracy analysis',
        'Strategy backtesting — 2yr NEM history',
        'Spike event model degradation',
      ],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Revenue stacking model with FCAS and cap contracts, PPA book valuation, BESS asset benchmarking across NEM fleet.',
      features: [
        'BESS revenue stacking — Energy/FCAS/Cap',
        'PPA book AUD MTM marking',
        'ASX benchmarking — A$/MW/yr',
        '12-month NEM fleet revenue history',
      ],
    },
  },
  EPEX: {
    dispatch: {
      label: 'Dispatch Operator',
      desc: 'Monitor your European BESS fleet, build and submit energy and balancing reserve offer stacks, review ML dispatch recommendations.',
      features: [
        'EPEX energy & balancing reserve stacks',
        'Day-ahead & intraday scheduling',
        'SOC monitoring — EU storage fleet',
        'Stack replacement workflow (no rebid)',
      ],
    },
    trader: {
      label: 'Power Trader',
      desc: 'Position book with live EUR MTM P&L, zonal exposure heatmap, trade blotter ingested from Endur ETRM.',
      features: [
        'Net exposure heatmap — 5 EPEX zones',
        'Live MTM — EUR mark-to-market',
        'Endur ingestion via DLT pipeline',
        'EEX futures and EU ETS positions',
      ],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Run VaR Monte Carlo, stress test against EPEX events including cold snaps and renewable floods, monitor EUR limit utilisation.',
      features: [
        'VaR Monte Carlo — 10,000 paths EUR',
        '3 EPEX historical stress scenarios',
        'EU cold snap limit monitoring',
        'Counterparty credit — European participants',
      ],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Model performance monitoring, strategy backtesting across EPEX history, analysis of 15-min MTU change impact on model accuracy.',
      features: [
        'EPEX DA price forecast — LightGBM',
        'EU ETS carbon signal analysis',
        'Strategy backtesting — 2yr EPEX history',
        'MTU 15-min model impact analysis',
      ],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Revenue model for EPEX storage arbitrage, PPA book valuation in EUR, BESS asset benchmarking across European fleet.',
      features: [
        'Storage arbitrage revenue model — EUR',
        'PPA book EUR MTM marking',
        'EEX benchmarking — €/MW/yr',
        'Monthly EPEX fleet revenue history',
      ],
    },
  },
  ERCOT: {
    dispatch: {
      label: 'Dispatch Operator',
      desc: 'Monitor your ERCOT BESS fleet, build and submit nodal offer stacks leveraging RTC+B signal, review real-time dispatch recommendations.',
      features: [
        'RTC+B real-time dispatch signal',
        'Nodal LMP bid stack — 10 hubs',
        'SOC monitoring — West Texas fleet',
        'ECRS and Reg Up/Down services',
      ],
    },
    trader: {
      label: 'Power Trader',
      desc: 'Position book with live USD MTM P&L, nodal exposure heatmap, trade blotter ingested from Triple Point ETRM.',
      features: [
        'Nodal exposure heatmap — 4 ERCOT hubs',
        'Live MTM — USD mark-to-market',
        'Triple Point ingestion via DLT pipeline',
        'Wind basis and congestion analysis',
      ],
    },
    risk: {
      label: 'Risk Manager',
      desc: 'Run VaR Monte Carlo, stress test against ERCOT summer scarcity and wind drop events, monitor USD limit utilisation.',
      features: [
        'VaR Monte Carlo — 10,000 paths USD',
        '2 ERCOT historical stress scenarios',
        'Summer scarcity limit monitoring',
        'Counterparty credit — Texas participants',
      ],
    },
    quant: {
      label: 'Quant Developer',
      desc: 'Model performance monitoring, RTC+B signal quality analysis, strategy backtesting across ERCOT LMP history since Jan 2025.',
      features: [
        'ERCOT real-time LMP forecast — LightGBM',
        'RTC+B signal vs DA forecast comparison',
        'Strategy backtesting — 2025 ERCOT history',
        'Wind basis congestion signal analysis',
      ],
    },
    portfolio: {
      label: 'Portfolio Manager',
      desc: 'Revenue model for ERCOT storage including RTC+B premium, PPA book valuation in USD, BESS asset benchmarking across Texas fleet.',
      features: [
        'BESS revenue — Energy/Ancillary/RTC+B',
        'PPA book USD MTM marking',
        'ERCOT benchmarking — $/MW/yr',
        'RTC+B revenue uplift since Dec 2025',
      ],
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
