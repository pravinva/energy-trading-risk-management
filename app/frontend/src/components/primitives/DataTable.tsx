import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table';
import { useMemo } from 'react';

type ColumnKind = 'price' | 'mw' | 'pct' | 'text' | 'badge' | 'action';

export type TradingColumnDef<T extends object> = ColumnDef<T> & {
  meta?: {
    kind?: ColumnKind;
  };
};

export function DataTable<T extends object>({
  data,
  columns,
  onRowClick,
  onRowDoubleClick,
  selectedRowId,
  highlightRowFn,
  loading,
  emptyMessage = 'No data',
}: {
  data: T[];
  columns: TradingColumnDef<T>[];
  onRowClick?: (row: T) => void;
  onRowDoubleClick?: (row: T) => void;
  selectedRowId?: string;
  highlightRowFn?: (row: T) => 'long' | 'short' | 'flat' | null;
  loading?: boolean;
  emptyMessage?: string;
}): JSX.Element {
  const stableData = useMemo(() => data, [data]);
  const table = useReactTable({ data: stableData, columns, getCoreRowModel: getCoreRowModel() });
  if (loading) {
    return <div>{[0, 1, 2].map((i) => <div key={i} style={{ height: 28, marginBottom: 6, background: 'var(--color-bg-raised)', opacity: 0.5 }} />)}</div>;
  }
  if (data.length === 0) {
    return <div className="text-tertiary" style={{ textAlign: 'center', padding: 'var(--space-4)' }}>{emptyMessage}</div>;
  }
  return (
    <table style={{ borderRadius: 0 }}>
      <thead style={{ background: 'var(--color-bg-elevated)' }}>
        {table.getHeaderGroups().map((hg) => (
          <tr key={hg.id}>{hg.headers.map((h) => <th key={h.id}>{h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}</th>)}</tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row, idx) => (
          <tr
            key={row.id}
            onClick={() => onRowClick?.(row.original)}
            onDoubleClick={() => onRowDoubleClick?.(row.original)}
            className={highlightRowFn?.(row.original) === 'long' ? 'row-long' : highlightRowFn?.(row.original) === 'short' ? 'row-short' : undefined}
            style={{
              background: selectedRowId && selectedRowId === row.id ? 'var(--color-bg-overlay)' : idx % 2 === 0 ? 'var(--color-bg-base)' : 'var(--color-bg-raised)',
              cursor: onRowClick ? 'pointer' : 'default',
            }}
          >
            {row.getVisibleCells().map((cell) => {
              const raw = cell.getValue() as unknown;
              const kind = (cell.column.columnDef as TradingColumnDef<T>).meta?.kind;
              const isNumeric = typeof raw === 'number';
              const cls = kind === 'price' ? 'mono-price' : kind === 'mw' ? 'mono-mw' : kind === 'pct' ? 'mono-pct' : isNumeric ? 'text-right font-data text-tabular' : '';
              const color = isNumeric && Number(raw) > 0 ? 'var(--color-positive)' : isNumeric && Number(raw) < 0 ? 'var(--color-negative)' : 'var(--color-text-primary)';
              return <td key={cell.id} className={cls} style={{ color }}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
