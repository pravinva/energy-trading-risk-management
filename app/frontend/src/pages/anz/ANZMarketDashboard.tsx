import { createColumnHelper } from '@tanstack/react-table';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useANZCurrentPrices, useANZFCASSummary, useANZPriceHistory, useANZSpikes } from '@/api/hooks/anz';
import { DataTable, Panel } from '@/components/primitives';
const helper = createColumnHelper<Record<string, string | number>>();
export function ANZMarketDashboard(): JSX.Element {
  const current = useANZCurrentPrices();
  const history = useANZPriceHistory(24);
  const fcas = useANZFCASSummary();
  const spikes = useANZSpikes(30);
  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <Panel title="CURRENT RRP STRIP" region="anz"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>{(current.data ?? []).map((i: any) => <div key={i.region_id} style={{ border: '1px solid var(--color-border-subtle)', padding: 8 }}><div className="label-caps">{i.region_id}</div><div className="font-data text-2xl">{i.rrp}</div></div>)}</div></Panel>
      <Panel title="RRP HISTORY" region="anz"><div style={{ height: 260 }}><ResponsiveContainer><LineChart data={(history.data ?? []).slice(-96)}><XAxis dataKey="interval_datetime" hide /><YAxis orientation="right" /><Tooltip /><Line dataKey="rrp" stroke="var(--color-neutral)" dot={false} /></LineChart></ResponsiveContainer></div></Panel>
      <Panel title="FCAS MARKET SUMMARY" region="anz"><DataTable data={fcas.data ?? []} columns={[helper.accessor('region_id', { header: 'REGION' }), helper.accessor('raise6sec_avg', { header: 'RAISE 6S' }), helper.accessor('lower6sec_avg', { header: 'LOWER 6S' }), helper.accessor('raisereg_avg', { header: 'RAISE REG' }), helper.accessor('lowerreg_avg', { header: 'LOWER REG' })]} /></Panel>
      <Panel title="SPIKE EVENT FEED" region="anz"><DataTable data={spikes.data ?? []} columns={[helper.accessor('start_datetime', { header: 'START' }), helper.accessor('region_id', { header: 'REGION' }), helper.accessor('peak_rrp', { header: 'PEAK RRP' }), helper.accessor('duration_minutes', { header: 'DURATION MIN' })]} /></Panel>
    </div>
  );
}
