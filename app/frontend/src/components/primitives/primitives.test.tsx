import { render } from '@testing-library/react';
import { createColumnHelper } from '@tanstack/react-table';
import { DataTable, Metric, Panel, Sparkline, StatusBadge } from '@/components/primitives';
const helper = createColumnHelper<{ value: number }>();

describe('primitives', () => {
  test('Panel renders', () => { const { container } = render(<Panel title="Test">A</Panel>); expect(container).toMatchSnapshot(); });
  test('DataTable renders', () => { const columns = [helper.accessor('value', { header: 'VALUE' })]; const { container } = render(<DataTable data={[{ value: 1 }]} columns={columns} />); expect(container).toMatchSnapshot(); });
  test('Metric renders', () => { const { container } = render(<Metric label="X" value={10} unit="MW" change={2} />); expect(container).toMatchSnapshot(); });
  test('StatusBadge renders', () => { const { container } = render(<StatusBadge status="active" label="ok" />); expect(container).toMatchSnapshot(); });
  test('Sparkline renders', () => { const { container } = render(<Sparkline data={[1,2,1,3]} positive />); expect(container).toMatchSnapshot(); });
});
