import { Outlet } from '@tanstack/react-router';
import { RegionalLayout } from './RegionalLayout';
export function ANZLayout(): JSX.Element { return <RegionalLayout region="anz" regionLabel="ANZ / NEM" navItems={[{ path: '/anz/market', label: 'Market' }, { path: '/anz/bess', label: 'BESS' }, { path: '/anz/etrm', label: 'ETRM' }]}><Outlet /></RegionalLayout>; }
