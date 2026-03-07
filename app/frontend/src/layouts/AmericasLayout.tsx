import { Outlet } from '@tanstack/react-router';
import { RegionalLayout } from './RegionalLayout';
export function AmericasLayout(): JSX.Element { return <RegionalLayout region="americas" regionLabel="AMERICAS / ISO-RTO" navItems={[{ path: '/americas/market', label: 'Market' }, { path: '/americas/bess', label: 'BESS' }, { path: '/americas/etrm', label: 'ETRM' }]}><Outlet /></RegionalLayout>; }
