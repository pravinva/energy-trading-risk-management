import { DataTable, Panel } from '@/components/primitives';
import { useBacktests, useModelPerformance } from '@/api/hooks/apex';

export function QuantConsole(): JSX.Element {
  const models = useModelPerformance();
  const backtests = useBacktests();

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="quant" title="Model Performance" subtitle="Champion vs challenger">
        <DataTable data={models.data ?? []} columns={[{ header: 'Model', accessorKey: 'model_name' }, { header: 'MAPE', accessorKey: 'mape', meta: { kind: 'pct' } }, { header: 'RMSE', accessorKey: 'rmse', meta: { kind: 'price' } }, { header: 'R2', accessorKey: 'r2', meta: { kind: 'pct' } }]} />
      </Panel>
      <Panel persona="quant" title="Backtest Console" subtitle="Strategy benchmarking">
        <DataTable data={backtests.data ?? []} columns={[{ header: 'Strategy', accessorKey: 'strategy' }, { header: 'Trades', accessorKey: 'trades', meta: { kind: 'mw' } }, { header: 'Win Rate', accessorKey: 'win_rate', meta: { kind: 'pct' } }, { header: 'Total PnL', accessorKey: 'total_pnl', meta: { kind: 'price' } }, { header: 'Sharpe', accessorKey: 'sharpe', meta: { kind: 'pct' } }]} />
      </Panel>
    </div>
  );
}
