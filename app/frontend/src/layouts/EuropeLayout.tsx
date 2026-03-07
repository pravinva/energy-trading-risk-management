import { Outlet } from '@tanstack/react-router';
import { RegionalLayout } from './RegionalLayout';
export function EuropeLayout(): JSX.Element { return <RegionalLayout region="europe" regionLabel="EUROPE / EPEX" navItems={[{ path: '/europe/market', label: 'Market' }, { path: '/europe/portfolio', label: 'Portfolio' }, { path: '/europe/etrm', label: 'ETRM' }]}><Outlet /></RegionalLayout>; }
