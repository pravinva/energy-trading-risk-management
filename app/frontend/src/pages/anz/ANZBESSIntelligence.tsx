import { createColumnHelper } from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import { Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useANZBESSFleet, useANZBESSRevenue, useANZBESSTelemetry } from '@/api/hooks/anz';
import { DataTable, Metric, Panel } from '@/components/primitives';
const helper = createColumnHelper<Record<string, any>>();

export function ANZBESSIntelligence(): JSX.Element {
  const fleet = useANZBESSFleet();
  const [selected, setSelected] = useState('HORNSDALE_1');
  const telemetry = useANZBESSTelemetry(selected, 24);
  const revenue = useANZBESSRevenue(selected, 7);
  const assets = fleet.data?.assets ?? [];
  const totalMw = useMemo(() => assets.reduce((acc: number, a: any) => acc + a.capacity_mw, 0), [assets]);
  const discharging = useMemo(() => assets.filter((a: any) => a.current_output_mw > 0).reduce((acc: number, a: any) => acc + a.current_output_mw, 0), [assets]);
  const charging = useMemo(() => assets.filter((a: any) => a.current_output_mw < 0).reduce((acc: number, a: any) => acc + Math.abs(a.current_output_mw), 0), [assets]);
  const avgSoc = useMemo(() => assets.length ? assets.reduce((acc: number, a: any) => acc + a.current_soc_pct, 0) / assets.length : 0, [assets]);
  return <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
    <Panel title="BESS FLEET OVERVIEW" region="anz"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}><Metric label="TOTAL FLEET CAPACITY" value={totalMw.toFixed(2)} unit="MW" /><Metric label="CURRENTLY DISCHARGING" value={discharging.toFixed(2)} unit="MW" /><Metric label="CURRENTLY CHARGING" value={charging.toFixed(2)} unit="MW" /><Metric label="FLEET AVG SOC" value={avgSoc.toFixed(2)} unit="%" /></div></Panel>
    <Panel title="BESS ASSETS" region="anz"><DataTable data={assets} onRowClick={(r) => setSelected(r.duid)} columns={[helper.accessor('duid', { header: 'DUID' }), helper.accessor('asset_name', { header: 'ASSET NAME' }), helper.accessor('region_id', { header: 'REGION' }), helper.accessor('capacity_mw', { header: 'CAPACITY MW' }), helper.accessor('duration_hours', { header: 'DURATION' }), helper.accessor('current_soc_pct', { header: 'SOC %' }), helper.accessor('current_output_mw', { header: 'OUTPUT MW' }), helper.accessor('today_revenue', { header: 'TODAY REV' }), helper.accessor('annual_revenue_ytd', { header: 'YTD REV' })]} /></Panel>
    <Panel title={`BESS DETAIL - ${selected}`} region="anz"><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}><div style={{ height: 220 }}><ResponsiveContainer><AreaChart data={telemetry.data ?? []}><XAxis dataKey="recorded_at" hide /><YAxis /><Tooltip /><Area dataKey="state_of_charge_pct" stroke="var(--color-neutral)" fill="var(--color-neutral-dim)" /></AreaChart></ResponsiveContainer></div><div style={{ height: 220 }}><ResponsiveContainer><BarChart data={revenue.data ?? []}><XAxis dataKey="settlement_date" hide /><YAxis /><Tooltip /><Bar dataKey="energy_revenue" stackId="a" fill="var(--color-neutral)" /><Bar dataKey="fcas_total_revenue" stackId="a" fill="var(--color-positive)" /></BarChart></ResponsiveContainer></div></div></Panel>
  </div>;
}
