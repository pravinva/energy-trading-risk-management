/**
 * Volume Forecast Component
 * 15-Day BUY/SELL Volume Forecast - KEY FEATURE from Sahil's demo
 * Shows daily trading volume recommendations based on weather, maintenance, and market factors
 */
import { useMemo } from 'react';
import { Panel, DataTable, Metric } from '@/components/primitives';
import { useVolumeForecast, useVolumeForecastSummary } from '@/api/hooks/apex';

interface VolumeForecastProps {
  regionId: string;
  days?: number;
}

export function VolumeForecast({ regionId, days = 15 }: VolumeForecastProps): JSX.Element {
  const volumeForecast = useVolumeForecast(regionId, days);
  const summary = useVolumeForecastSummary(regionId, days);

  const forecastData = volumeForecast.data?.data ?? [];
  const summaryData = summary.data?.data;

  // Calculate visualization points for the forecast chart
  const forecastChart = useMemo(() => {
    if (forecastData.length === 0) return { buyPoints: '', sellPoints: '', xLabels: [] };

    const volumes = forecastData.map((d) => d.volume_mwh);
    const max = Math.max(...volumes, 1);
    const min = Math.min(...volumes, 0);

    const buyPoints = forecastData
      .filter((d) => d.forecast_type === 'BUY')
      .map((d, idx) => {
        const dayIndex = forecastData.indexOf(d);
        const x = forecastData.length > 1 ? (dayIndex / (forecastData.length - 1)) * 100 : 0;
        const y = max === min ? 36 : 62 - ((d.volume_mwh - min) / (max - min)) * 52;
        return { x, y, dayIndex };
      });

    const sellPoints = forecastData
      .filter((d) => d.forecast_type === 'SELL')
      .map((d) => {
        const dayIndex = forecastData.indexOf(d);
        const x = forecastData.length > 1 ? (dayIndex / (forecastData.length - 1)) * 100 : 0;
        const y = max === min ? 36 : 62 - ((d.volume_mwh - min) / (max - min)) * 52;
        return { x, y, dayIndex };
      });

    return {
      buyPoints: buyPoints.map((p) => `${p.x},${p.y}`).join(' '),
      sellPoints: sellPoints.map((p) => `${p.x},${p.y}`).join(' '),
      xLabels: forecastData.map((d, idx) => ({
        x: forecastData.length > 1 ? (idx / (forecastData.length - 1)) * 100 : 0,
        label: new Date(d.forecast_date).getDate().toString(),
      })),
    };
  }, [forecastData]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      {/* Summary Cards */}
      <Panel persona="quant" title="Volume Forecast Summary" subtitle={`${days}-day outlook · ${regionId}`}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--space-3)' }}>
          <Metric
            label="BUY Days"
            value={summaryData?.buy_days ?? 0}
            unit={`of ${summaryData?.total_days ?? 0}`}
            size="lg"
          />
          <Metric
            label="SELL Days"
            value={summaryData?.sell_days ?? 0}
            unit={`of ${summaryData?.total_days ?? 0}`}
            size="lg"
          />
          <Metric
            label="Avg Volume"
            value={summaryData?.avg_volume_mwh.toFixed(0) ?? '0'}
            unit="MWh"
            size="lg"
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
          <Metric
            label="Total BUY Volume"
            value={summaryData?.total_buy_volume_mwh.toFixed(0) ?? '0'}
            unit="MWh"
            size="md"
          />
          <Metric
            label="Total SELL Volume"
            value={summaryData?.total_sell_volume_mwh.toFixed(0) ?? '0'}
            unit="MWh"
            size="md"
          />
        </div>
      </Panel>

      {/* Forecast Chart */}
      <Panel persona="quant" title="15-Day BUY/SELL Forecast" subtitle="Daily trading volume recommendations">
        <div className="label-caps" style={{ marginBottom: 6 }}>
          Volume Forecast — Next {days} Days
        </div>

        <svg width="100%" height="140" viewBox="0 0 100 110" style={{ marginBottom: 16 }}>
          {/* Grid lines */}
          <line x1="0" y1="10" x2="100" y2="10" stroke="var(--color-border-subtle)" strokeWidth="0.3" />
          <line x1="0" y1="36" x2="100" y2="36" stroke="var(--color-border-subtle)" strokeWidth="0.3" />
          <line x1="0" y1="62" x2="100" y2="62" stroke="var(--color-border-subtle)" strokeWidth="0.3" />

          {/* BUY points (red) */}
          {forecastData
            .filter((d) => d.forecast_type === 'BUY')
            .map((d, idx) => {
              const dayIndex = forecastData.indexOf(d);
              const x = forecastData.length > 1 ? (dayIndex / (forecastData.length - 1)) * 100 : 0;
              const volumes = forecastData.map((v) => v.volume_mwh);
              const max = Math.max(...volumes, 1);
              const min = Math.min(...volumes, 0);
              const y = max === min ? 36 : 62 - ((d.volume_mwh - min) / (max - min)) * 52;
              return <circle key={`buy-${idx}`} cx={x} cy={y} r="1.8" fill="var(--color-negative)" />;
            })}

          {/* SELL points (green) */}
          {forecastData
            .filter((d) => d.forecast_type === 'SELL')
            .map((d, idx) => {
              const dayIndex = forecastData.indexOf(d);
              const x = forecastData.length > 1 ? (dayIndex / (forecastData.length - 1)) * 100 : 0;
              const volumes = forecastData.map((v) => v.volume_mwh);
              const max = Math.max(...volumes, 1);
              const min = Math.min(...volumes, 0);
              const y = max === min ? 36 : 62 - ((d.volume_mwh - min) / (max - min)) * 52;
              return <circle key={`sell-${idx}`} cx={x} cy={y} r="1.8" fill="var(--color-positive)" />;
            })}

          {/* X-axis labels (day numbers) */}
          {forecastChart.xLabels.map((label, idx) => (
            <text
              key={`label-${idx}`}
              x={label.x}
              y="75"
              fontSize="5"
              textAnchor="middle"
              fill="var(--color-text-tertiary)"
            >
              {label.label}
            </text>
          ))}
        </svg>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-3)', fontSize: 11 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: 'var(--color-negative)' }} />
            <span>BUY</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: 'var(--color-positive)' }} />
            <span>SELL</span>
          </div>
        </div>

        {/* Forecast Table */}
        <DataTable
          data={forecastData}
          columns={[
            {
              header: 'Date',
              accessorKey: 'forecast_date',
              cell: (info) => {
                const date = new Date(info.getValue() as string);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
              },
            },
            {
              header: 'Type',
              accessorKey: 'forecast_type',
              cell: (info) => {
                const type = info.getValue() as string;
                const color = type === 'BUY' ? 'var(--color-negative)' : 'var(--color-positive)';
                return (
                  <span
                    style={{
                      color,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 4,
                      backgroundColor: type === 'BUY' ? 'rgba(244, 67, 54, 0.1)' : 'rgba(76, 175, 80, 0.1)',
                    }}
                  >
                    {type}
                  </span>
                );
              },
            },
            {
              header: 'Volume (MWh)',
              accessorKey: 'volume_mwh',
              meta: { kind: 'mw' },
              cell: (info) => (info.getValue() as number).toFixed(0),
            },
            {
              header: 'Weather Impact',
              accessorKey: 'weather_impact_pct',
              cell: (info) => {
                const value = info.getValue() as number;
                const color = value > 0 ? 'var(--color-positive)' : value < 0 ? 'var(--color-negative)' : 'var(--color-text-secondary)';
                return <span style={{ color }}>{value > 0 ? '+' : ''}{value.toFixed(1)}%</span>;
              },
            },
            {
              header: 'Maintenance Impact',
              accessorKey: 'maintenance_impact_pct',
              cell: (info) => {
                const value = info.getValue() as number;
                const color = value < 0 ? 'var(--color-negative)' : 'var(--color-text-secondary)';
                return <span style={{ color }}>{value.toFixed(1)}%</span>;
              },
            },
            {
              header: 'Confidence',
              accessorKey: 'confidence_level',
              cell: (info) => {
                const level = info.getValue() as string;
                const color =
                  level === 'HIGH'
                    ? 'var(--color-positive)'
                    : level === 'MEDIUM'
                    ? 'var(--color-warning)'
                    : 'var(--color-text-tertiary)';
                return <span style={{ color }}>{level}</span>;
              },
            },
          ]}
        />
      </Panel>
    </div>
  );
}
