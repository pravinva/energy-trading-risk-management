/**
 * Weather Impact Component
 * Displays weather forecast data and correlations with energy prices
 */
import { useMemo } from 'react';
import { Panel, DataTable, Metric } from '@/components/primitives';
import { useWeatherForecast, useWeatherImpact } from '@/api/hooks/apex';

interface WeatherImpactProps {
  regionId: string;
  days?: number;
}

export function WeatherImpact({ regionId, days = 7 }: WeatherImpactProps): JSX.Element {
  const weatherForecast = useWeatherForecast(regionId, days);
  const weatherImpact = useWeatherImpact(regionId);

  // Calculate summary metrics from forecast data
  const summary = useMemo(() => {
    const data = weatherForecast.data?.data ?? [];
    if (data.length === 0) {
      return { avgTemp: 0, avgWind: 0, avgSolar: 0, maxTemp: 0, minTemp: 0 };
    }

    const temps = data.map((d) => d.temperature_celsius);
    const winds = data.map((d) => d.wind_speed_ms);
    const solars = data.map((d) => d.solar_irradiance_wm2);

    return {
      avgTemp: temps.reduce((a, b) => a + b, 0) / temps.length,
      avgWind: winds.reduce((a, b) => a + b, 0) / winds.length,
      avgSolar: solars.reduce((a, b) => a + b, 0) / solars.length,
      maxTemp: Math.max(...temps),
      minTemp: Math.min(...temps),
    };
  }, [weatherForecast.data]);

  // Temperature trend sparkline
  const tempPoints = useMemo(() => {
    const data = weatherForecast.data?.data ?? [];
    if (data.length === 0) return '';

    const temps = data.slice(0, 48).map((d) => d.temperature_celsius);
    const max = Math.max(...temps, 1);
    const min = Math.min(...temps, 0);

    return temps
      .map((value, idx) => {
        const x = temps.length > 1 ? (idx / (temps.length - 1)) * 100 : 0;
        const y = max === min ? 36 : 62 - ((value - min) / (max - min)) * 52;
        return `${x},${y}`;
      })
      .join(' ');
  }, [weatherForecast.data]);

  // Wind speed trend sparkline
  const windPoints = useMemo(() => {
    const data = weatherForecast.data?.data ?? [];
    if (data.length === 0) return '';

    const winds = data.slice(0, 48).map((d) => d.wind_speed_ms);
    const max = Math.max(...winds, 1);
    const min = Math.min(...winds, 0);

    return winds
      .map((value, idx) => {
        const x = winds.length > 1 ? (idx / (winds.length - 1)) * 100 : 0;
        const y = max === min ? 36 : 62 - ((value - min) / (max - min)) * 52;
        return `${x},${y}`;
      })
      .join(' ');
  }, [weatherForecast.data]);

  // Solar irradiance trend sparkline
  const solarPoints = useMemo(() => {
    const data = weatherForecast.data?.data ?? [];
    if (data.length === 0) return '';

    const solars = data.slice(0, 48).map((d) => d.solar_irradiance_wm2);
    const max = Math.max(...solars, 1);
    const min = Math.min(...solars, 0);

    return solars
      .map((value, idx) => {
        const x = solars.length > 1 ? (idx / (solars.length - 1)) * 100 : 0;
        const y = max === min ? 36 : 62 - ((value - min) / (max - min)) * 52;
        return `${x},${y}`;
      })
      .join(' ');
  }, [weatherForecast.data]);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      {/* Weather Metrics */}
      <Panel persona="quant" title="Weather Forecast" subtitle={`${days}-day forecast · ${regionId}`}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
          <Metric label="Avg Temperature" value={summary.avgTemp.toFixed(1)} unit="°C" size="md" />
          <Metric label="Avg Wind Speed" value={summary.avgWind.toFixed(1)} unit="m/s" size="md" />
          <Metric label="Avg Solar" value={summary.avgSolar.toFixed(0)} unit="W/m²" size="md" />
        </div>

        {/* Temperature Trend */}
        <div style={{ marginBottom: 'var(--space-2)' }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Temperature — Next 48h
          </div>
          <svg width="100%" height="86" viewBox="0 0 100 72" style={{ marginBottom: 8 }}>
            <polyline fill="none" stroke="var(--color-persona-quant)" strokeWidth="1.4" points={tempPoints} />
          </svg>
        </div>

        {/* Wind Speed Trend */}
        <div style={{ marginBottom: 'var(--space-2)' }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Wind Speed — Next 48h
          </div>
          <svg width="100%" height="86" viewBox="0 0 100 72" style={{ marginBottom: 8 }}>
            <polyline fill="none" stroke="var(--color-positive)" strokeWidth="1.4" points={windPoints} />
          </svg>
        </div>

        {/* Solar Irradiance Trend */}
        <div>
          <div className="label-caps" style={{ marginBottom: 6 }}>
            Solar Irradiance — Next 48h
          </div>
          <svg width="100%" height="86" viewBox="0 0 100 72" style={{ marginBottom: 8 }}>
            <polyline fill="none" stroke="var(--color-warning)" strokeWidth="1.4" points={solarPoints} />
          </svg>
        </div>
      </Panel>

      {/* Weather Impact Correlation */}
      <Panel persona="quant" title="Weather Impact Analysis" subtitle="Correlation with energy prices">
        <DataTable
          data={weatherImpact.data?.data ?? []}
          columns={[
            { header: 'Parameter', accessorKey: 'weather_parameter' },
            {
              header: 'Price Correlation',
              accessorKey: 'price_correlation',
              meta: { kind: 'pct' },
              cell: (info) => {
                const value = info.getValue() as number;
                const color = value > 0 ? 'var(--color-positive)' : 'var(--color-negative)';
                return <span style={{ color }}>{(value * 100).toFixed(1)}%</span>;
              },
            },
            {
              header: 'Impact per Unit',
              accessorKey: 'price_impact_per_unit',
              meta: { kind: 'price' },
            },
            {
              header: 'Volatility Impact',
              accessorKey: 'volatility_impact',
              meta: { kind: 'pct' },
            },
            {
              header: 'Sample Size',
              accessorKey: 'sample_size',
            },
          ]}
        />
      </Panel>
    </div>
  );
}
