import { Link, Outlet, useLocation } from '@tanstack/react-router';
import { useEffect } from 'react';
import { useCurrentPrices, useMarketPnlDaily, useMarketSummary } from '@/api/hooks/apex';
import { useTradingStore } from '@/store/tradingStore';

const riskItemsPrimary = [
  { to: '/workspace/risk', label: 'VaR Dashboard' },
  { to: '/workspace/risk/stress-testing', label: 'Stress Testing' },
  { to: '/workspace/risk/limit-monitor', label: 'Limit Monitor' },
  { to: '/workspace/risk/credit-exposure', label: 'Credit Exposure' },
];

const navByPersona = {
  dispatch: {
    sectionA: 'Dispatch',
    itemsA: [{ to: '/workspace/dispatch', label: 'Console' }, { to: '/workspace/dispatch', label: 'Fleet Overview' }],
    sectionB: 'Assets',
    itemsB: [{ to: '/workspace/dispatch', label: 'Fleet' }, { to: '/workspace/dispatch', label: 'Stack History' }],
  },
  trader: {
    sectionA: 'Analytics',
    itemsA: [{ to: '/workspace/trading', label: 'Overview' }, { to: '/workspace/trading', label: 'Position Book' }, { to: '/workspace/trading', label: 'Trade Blotter' }],
    sectionB: 'Views',
    itemsB: [{ to: '/workspace/trading', label: 'By Region' }, { to: '/workspace/trading', label: 'P&L Attribution' }],
  },
  risk: {
    sectionA: 'Risk',
    itemsA: riskItemsPrimary,
    sectionB: 'Portfolio',
    itemsB: [{ to: '/workspace/risk', label: 'All Positions' }, { to: '/workspace/risk', label: 'P&L Attribution' }],
  },
  quant: {
    sectionA: 'Research',
    itemsA: [{ to: '/workspace/quant', label: 'Model Performance' }, { to: '/workspace/quant', label: 'Backtest Console' }, { to: '/workspace/quant', label: 'Signal Scanner' }],
    sectionB: 'Data',
    itemsB: [{ to: '/workspace/quant', label: 'Price History' }, { to: '/workspace/quant', label: 'FCAS Analysis' }],
  },
  portfolio: {
    sectionA: 'Revenue',
    itemsA: [{ to: '/workspace/portfolio', label: 'Revenue Dashboard' }, { to: '/workspace/portfolio', label: 'Revenue Forecast' }, { to: '/workspace/portfolio', label: 'Components' }],
    sectionB: 'PPA',
    itemsB: [{ to: '/workspace/portfolio', label: 'PPA Book' }, { to: '/workspace/portfolio', label: 'Payoff Analysis' }],
  },
};

const marketLabel = {
  NEM: 'ANZ',
  EPEX: 'EU',
  ERCOT: 'US',
} as const;

const personaLabel = {
  dispatch: 'Dispatch Operator',
  trader: 'Power Trader',
  risk: 'Risk Manager',
  quant: 'Quant Developer',
  portfolio: 'Portfolio Manager',
} as const;

export function ApexWorkspaceLayout(): JSX.Element {
  const location = useLocation();
  const summary = useMarketSummary();
  const prices = useCurrentPrices();
  const setPersona = useTradingStore((s) => s.setPersona);
  const persona = useTradingStore((s) => s.persona);
  const market = useTradingStore((s) => s.market);
  const setMarket = useTradingStore((s) => s.setMarket);
  const sessionPnl = useTradingStore((s) => s.sessionPnl);
  const setSessionPnl = useTradingStore((s) => s.setSessionPnl);
  const pnlDaily = useMarketPnlDaily(market);

  useEffect(() => {
    if (typeof pnlDaily.data?.pnl_daily === 'number') {
      setSessionPnl(pnlDaily.data.pnl_daily);
    }
  }, [pnlDaily.data?.pnl_daily, setSessionPnl]);

  useEffect(() => {
    if (location.pathname.startsWith('/workspace/dispatch')) {
      setPersona('dispatch');
    } else if (location.pathname.startsWith('/workspace/trading')) {
      setPersona('trader');
    } else if (location.pathname.startsWith('/workspace/risk')) {
      setPersona('risk');
    } else if (location.pathname.startsWith('/workspace/quant')) {
      setPersona('quant');
    } else if (location.pathname.startsWith('/workspace/portfolio')) {
      setPersona('portfolio');
    }
  }, [location.pathname, setPersona]);

  const tickerRows = (prices.data ?? []).filter((row) => row.market === marketLabel[market]).slice(0, 4);
  const navConfig = navByPersona[persona];

  return (
    <div className="page-shell">
      <header className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link to="/" className="wordmark">APEX</Link>
          <span style={{ color: 'var(--color-border-strong)', fontSize: 14 }}>|</span>
          <span className="label-caps" style={{ color: 'var(--color-accent)' }}>{market}</span>
          <span className="label-caps" style={{ color: 'var(--color-text-primary)' }}>{personaLabel[persona]}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {tickerRows.map((row) => (
            <div key={row.instrument} className="font-data" style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
              {row.instrument} <span style={{ color: 'var(--color-text-primary)' }}>${row.price.toFixed(2)}</span>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <select value={market} onChange={(e) => setMarket(e.target.value as 'NEM' | 'EPEX' | 'ERCOT')}>
            <option value="NEM">NEM</option>
            <option value="EPEX">EPEX</option>
            <option value="ERCOT">ERCOT</option>
          </select>
          <div className="font-data" style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
            AVG <span style={{ color: 'var(--color-text-primary)' }}>${summary.data?.average_price?.toFixed(2) ?? '--'}</span>
          </div>
          <span className="font-data" style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{new Date().toLocaleTimeString()}</span>
          <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-secondary)' }}>Alex Thompson</span>
        </div>
      </header>
      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-section">{navConfig.sectionA}</div>
          {navConfig.itemsA.map((item) => (
            <Link
              key={`${item.label}-${item.to}`}
              to={item.to}
              className={`nav-item ${location.pathname === item.to ? 'active' : ''}`}
            >
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor', opacity: 0.6 }} />
              {item.label}
            </Link>
          ))}
          <div className="sidebar-section" style={{ marginTop: 10 }}>{navConfig.sectionB}</div>
          {navConfig.itemsB.map((item) => (
            <Link
              key={`${item.label}-${item.to}`}
              to={item.to}
              className={`nav-item ${location.pathname === item.to ? 'active' : ''}`}
            >
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor', opacity: 0.6 }} />
              {item.label}
            </Link>
          ))}
        </aside>
        <main className="main">
          <Outlet />
        </main>
      </div>
      <footer className="statusbar">
        <span className="status-item"><span className="status-live">● CONNECTED</span> · Lakebase · Latency 12ms</span>
        <span className="status-item">Last refresh: {new Date().toLocaleTimeString()}</span>
        <span className="session-pnl">SESSION P&L {sessionPnl >= 0 ? '+' : '-'}${Math.abs(sessionPnl).toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
      </footer>
    </div>
  );
}
