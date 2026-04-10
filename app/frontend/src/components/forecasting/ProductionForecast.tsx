/**
 * Production Forecast Component
 * Shows energy generation forecast by asset type and plant status timeline (Gantt chart)
 */
import { useMemo } from 'react';
import { Panel, DataTable, Metric } from '@/components/primitives';
import { useProductionForecast, usePlantStatus } from '@/api/hooks/apex';

interface ProductionForecastProps {
  regionId: string;
  days?: number;
}

export function ProductionForecast({ regionId, days = 7 }: ProductionForecastProps): JSX.Element {
  const production = useProductionForecast(regionId, null, days);
  const plantStatus = usePlantStatus(regionId, null, 14);

  const productionData = production.data?.data ?? [];
  const plantStatusData = plantStatus.data?.data ?? [];

  // Aggregate generation by asset type (average over forecast period)
  const assetSummary = useMemo(() => {
    if (productionData.length === 0) return [];

    const grouped = productionData.reduce((acc, row) => {
      if (!acc[row.asset_type]) {
        acc[row.asset_type] = {
          asset_type: row.asset_type,
          total_generation: 0,
          total_capacity: 0,
          count: 0,
        };
      }
      acc[row.asset_type].total_generation += row.generation_mw;
      acc[row.asset_type].total_capacity += row.capacity_mw;
      acc[row.asset_type].count += 1;
      return acc;
    }, {} as Record<string, { asset_type: string; total_generation: number; total_capacity: number; count: number }>);

    return Object.values(grouped).map((item) => ({
      asset_type: item.asset_type,
      avg_generation_mw: item.total_generation / item.count,
      avg_capacity_mw: item.total_capacity / item.count,
      capacity_factor: (item.total_generation / item.total_capacity) * 100,
    }));
  }, [productionData]);

  // Total generation across all asset types
  const totalGeneration = useMemo(() => {
    return assetSummary.reduce((sum, item) => sum + item.avg_generation_mw, 0);
  }, [assetSummary]);

  // Generation mix chart (pie/donut representation)
  const generationMixChart = useMemo(() => {
    if (assetSummary.length === 0) return [];

    const colors: Record<string, string> = {
      RENEWABLES: 'var(--color-positive)',
      COAL: '#424242',
      GAS: '#FF9800',
      NUCLEAR: '#9C27B0',
      BIOMASS: '#8BC34A',
    };

    let cumulative = 0;
    return assetSummary.map((item) => {
      const percentage = (item.avg_generation_mw / totalGeneration) * 100;
      const startAngle = (cumulative / 100) * 360;
      const endAngle = ((cumulative + percentage) / 100) * 360;
      cumulative += percentage;

      return {
        asset_type: item.asset_type,
        percentage,
        startAngle,
        endAngle,
        color: colors[item.asset_type] || 'var(--color-text-secondary)',
      };
    });
  }, [assetSummary, totalGeneration]);

  // Plant status Gantt chart visualization
  const ganttChart = useMemo(() => {
    if (plantStatusData.length === 0) return { plants: [], events: [] };

    // Get unique plant names
    const plantNames = Array.from(new Set(plantStatusData.map((e) => e.plant_name)));

    // Map events to chart coordinates
    const now = new Date();
    const endDate = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);
    const timeRange = endDate.getTime() - now.getTime();

    const events = plantStatusData.map((event) => {
      const start = new Date(event.start_datetime);
      const end = new Date(event.end_datetime);
      const plantIndex = plantNames.indexOf(event.plant_name);

      const xStart = ((start.getTime() - now.getTime()) / timeRange) * 100;
      const xEnd = ((end.getTime() - now.getTime()) / timeRange) * 100;
      const y = plantIndex * 8 + 4;

      const color =
        event.event_type === 'OUTAGE'
          ? 'var(--color-negative)'
          : event.event_type === 'MAINTENANCE'
          ? 'var(--color-warning)'
          : event.event_type === 'RAMP_UP'
          ? 'var(--color-positive)'
          : 'var(--color-text-tertiary)';

      return {
        ...event,
        xStart: Math.max(0, xStart),
        xEnd: Math.min(100, xEnd),
        y,
        color,
      };
    });

    return { plants: plantNames, events };
  }, [plantStatusData]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      {/* Generation Mix Summary */}
      <Panel persona="quant" title="Generation Forecast" subtitle={`${days}-day average by asset type · ${regionId}`}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
          <div>
            <div className="label-caps" style={{ marginBottom: 12 }}>
              Generation Mix
            </div>

            {/* Simple stacked bar representation */}
            <div style={{ display: 'flex', height: 40, borderRadius: 4, overflow: 'hidden', marginBottom: 12 }}>
              {generationMixChart.map((item) => (
                <div
                  key={item.asset_type}
                  style={{
                    flex: item.percentage,
                    backgroundColor: item.color,
                  }}
                  title={`${item.asset_type}: ${item.percentage.toFixed(1)}%`}
                />
              ))}
            </div>

            {/* Legend */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 11 }}>
              {generationMixChart.map((item) => (
                <div key={item.asset_type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 12, height: 12, borderRadius: 2, backgroundColor: item.color }} />
                  <span>
                    {item.asset_type} ({item.percentage.toFixed(1)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Metric label="Total Generation" value={totalGeneration.toFixed(0)} unit="MW" size="lg" />
            <div style={{ marginTop: 'var(--space-2)' }}>
              <div className="label-caps">Asset Count</div>
              <div className="font-data" style={{ fontSize: 'var(--text-xl)' }}>
                {assetSummary.length}
              </div>
            </div>
          </div>
        </div>

        {/* Asset Type Summary Table */}
        <DataTable
          data={assetSummary}
          columns={[
            { header: 'Asset Type', accessorKey: 'asset_type' },
            {
              header: 'Avg Generation (MW)',
              accessorKey: 'avg_generation_mw',
              cell: (info) => (info.getValue() as number).toFixed(0),
            },
            {
              header: 'Avg Capacity (MW)',
              accessorKey: 'avg_capacity_mw',
              cell: (info) => (info.getValue() as number).toFixed(0),
            },
            {
              header: 'Capacity Factor',
              accessorKey: 'capacity_factor',
              cell: (info) => {
                const value = info.getValue() as number;
                const color =
                  value > 80
                    ? 'var(--color-positive)'
                    : value > 50
                    ? 'var(--color-warning)'
                    : 'var(--color-negative)';
                return <span style={{ color }}>{value.toFixed(1)}%</span>;
              },
            },
          ]}
        />
      </Panel>

      {/* Plant Status Timeline (Gantt Chart) */}
      <Panel persona="quant" title="Plant Status Timeline" subtitle="Outages, maintenance, and ramp events · Next 14 days">
        <div className="label-caps" style={{ marginBottom: 12 }}>
          Event Timeline
        </div>

        {ganttChart.plants.length > 0 ? (
          <>
            <svg width="100%" height={Math.max(120, ganttChart.plants.length * 8 + 20)} viewBox={`0 0 100 ${ganttChart.plants.length * 8 + 10}`} style={{ marginBottom: 16 }}>
              {/* Timeline grid */}
              <line x1="0" y1="0" x2="100" y2="0" stroke="var(--color-border-subtle)" strokeWidth="0.2" />
              <line x1="0" y1={ganttChart.plants.length * 8} x2="100" y2={ganttChart.plants.length * 8} stroke="var(--color-border-subtle)" strokeWidth="0.2" />

              {/* Plant rows */}
              {ganttChart.plants.map((plant, idx) => (
                <g key={plant}>
                  <text x="-1" y={idx * 8 + 4.5} fontSize="2.5" textAnchor="end" fill="var(--color-text-secondary)">
                    {plant.substring(0, 20)}
                  </text>
                  <line x1="0" y1={idx * 8} x2="100" y2={idx * 8} stroke="var(--color-border-subtle)" strokeWidth="0.1" />
                </g>
              ))}

              {/* Event bars */}
              {ganttChart.events.map((event, idx) => (
                <g key={`event-${idx}`}>
                  <rect
                    x={event.xStart}
                    y={event.y - 2}
                    width={event.xEnd - event.xStart}
                    height="4"
                    fill={event.color}
                    opacity="0.8"
                    rx="0.5"
                  >
                    <title>
                      {event.plant_name} - {event.event_type}
                      {'\n'}
                      {event.description}
                      {'\n'}
                      Impact: {event.capacity_impact_mw.toFixed(0)} MW
                    </title>
                  </rect>
                </g>
              ))}
            </svg>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-3)', fontSize: 11 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 16, height: 8, borderRadius: 2, backgroundColor: 'var(--color-negative)' }} />
                <span>OUTAGE</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 16, height: 8, borderRadius: 2, backgroundColor: 'var(--color-warning)' }} />
                <span>MAINTENANCE</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 16, height: 8, borderRadius: 2, backgroundColor: 'var(--color-positive)' }} />
                <span>RAMP UP</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 16, height: 8, borderRadius: 2, backgroundColor: 'var(--color-text-tertiary)' }} />
                <span>RAMP DOWN</span>
              </div>
            </div>
          </>
        ) : (
          <div style={{ padding: 'var(--space-3)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
            No plant events scheduled
          </div>
        )}

        {/* Plant Events Table */}
        <DataTable
          data={plantStatusData.slice(0, 10)}
          columns={[
            { header: 'Plant', accessorKey: 'plant_name' },
            {
              header: 'Event Type',
              accessorKey: 'event_type',
              cell: (info) => {
                const type = info.getValue() as string;
                const colors: Record<string, string> = {
                  OUTAGE: 'var(--color-negative)',
                  MAINTENANCE: 'var(--color-warning)',
                  RAMP_UP: 'var(--color-positive)',
                  RAMP_DOWN: 'var(--color-text-tertiary)',
                };
                return <span style={{ color: colors[type] }}>{type}</span>;
              },
            },
            {
              header: 'Start',
              accessorKey: 'start_datetime',
              cell: (info) => new Date(info.getValue() as string).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            },
            {
              header: 'End',
              accessorKey: 'end_datetime',
              cell: (info) => new Date(info.getValue() as string).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            },
            {
              header: 'Impact (MW)',
              accessorKey: 'capacity_impact_mw',
              cell: (info) => (info.getValue() as number).toFixed(0),
            },
            {
              header: 'Grid Impact',
              accessorKey: 'grid_impact',
              cell: (info) => {
                const impact = info.getValue() as string;
                const color =
                  impact === 'HIGH'
                    ? 'var(--color-negative)'
                    : impact === 'MEDIUM'
                    ? 'var(--color-warning)'
                    : 'var(--color-text-tertiary)';
                return <span style={{ color }}>{impact}</span>;
              },
            },
          ]}
        />
      </Panel>
    </div>
  );
}
