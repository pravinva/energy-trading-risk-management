import { useEffect, useMemo } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { useDispatchAssets, useDispatchRecommendation, useDispatchServiceTypes, useDispatchStackHistory, useForecastMetadata, useLatestOfferStack, useMarketSummary, useModelLineage, usePredispatch } from '@/api/hooks/apex';
import { useDispatchStore } from '@/store/dispatchStore';
import { useTradingStore } from '@/store/tradingStore';

export function DispatchConsole(): JSX.Element {
  const { assetId, serviceType, setBands, setAssetId, setServiceType } = useDispatchStore();
  const market = useTradingStore((s) => s.market);
  const prices = useMarketSummary();
  const predispatch = usePredispatch(12, market);
  const forecastMeta = useForecastMetadata(market);
  const lineage = useModelLineage(market);
  const assetsQuery = useDispatchAssets(market);
  const serviceTypesQuery = useDispatchServiceTypes(market);
  const recommendation = useDispatchRecommendation(assetId);
  const history = useDispatchStackHistory(assetId, 40);
  const latestStack = useLatestOfferStack(assetId);
  const assets = (assetsQuery.data ?? []).map((r) => r.asset_id);
  const serviceTypes = (serviceTypesQuery.data ?? []).map((r) => r.service_type);
  const strip = (predispatch.data ?? []).slice(0, 12);
  const latestBands = latestStack.data?.bands ?? [];
  const totalVolume = useMemo(() => latestBands.reduce((sum, band) => sum + band.volume_mw, 0), [latestBands]);
  const weighted = useMemo(() => {
    const numerator = latestBands.reduce((sum, band) => sum + band.volume_mw * band.price, 0);
    return totalVolume > 0 ? numerator / totalVolume : 0;
  }, [latestBands, totalVolume]);
  const latestLineage = lineage.data?.[0];

  useEffect(() => {
    if (assets.length > 0 && !assets.includes(assetId)) {
      setAssetId(assets[0]);
    }
    if (serviceTypes.length > 0 && !serviceTypes.includes(serviceType)) {
      setServiceType(serviceTypes[0]);
    }
  }, [assetId, assets, serviceType, serviceTypes, setAssetId, setServiceType]);

  useEffect(() => {
    const live = latestStack.data;
    if (live?.bands?.length) {
      setBands(live.bands);
    }
  }, [latestStack.data, setBands]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '244px 1fr 240px', gap: 10, minHeight: 540 }}>
      <Panel persona="dispatch" title="Fleet Monitor" subtitle={`${market} dispatch assets`}>
        <div style={{ display: 'grid', gap: 6 }}>
          {assets.map((asset) => (
            <button
              key={asset}
              style={{ textAlign: 'left', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onClick={() => setAssetId(asset)}
            >
              <span>{asset}</span>
              <span className="font-data">{asset === assetId ? 'SELECTED' : 'READY'}</span>
            </button>
          ))}
        </div>
        <div style={{ marginTop: 10 }}>
          <div className="label-caps">Pre-Dispatch Strip</div>
          <div className="text-secondary" style={{ fontSize: 11 }}>
            {forecastMeta.data ? `${forecastMeta.data.model_name} · ${forecastMeta.data.points_available} points` : 'Forecast metadata loading'}
          </div>
          <div style={{ display: 'flex', alignItems: 'end', gap: 2, height: 40, marginTop: 6 }}>
            {strip.map((point, idx) => {
              const bar = Math.max(5, Math.min(40, point.forecast_price / 4));
              return <div key={`${point.interval_start}-${idx}`} style={{ flex: 1, height: bar, background: idx < 3 ? 'var(--color-negative)' : idx < 5 ? 'var(--color-warning)' : 'var(--color-border-strong)', borderRadius: '2px 2px 0 0' }} />;
            })}
          </div>
        </div>
      </Panel>

      <Panel persona="dispatch" title="Offer Stack Analytics" subtitle={`${assetId} · ${serviceType}`}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
          <select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
            {assets.map((asset) => <option key={asset}>{asset}</option>)}
          </select>
          <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
            {serviceTypes.map((service) => <option key={service}>{service}</option>)}
          </select>
        </div>
        <div style={{ display: 'grid', gap: 8 }}>
          <DataTable
            data={latestBands.map((band) => ({ band: `Band ${band.band_index}`, price: band.price, volume: band.volume_mw }))}
            columns={[
              { header: 'Band', accessorKey: 'band' },
              { header: 'Price', accessorKey: 'price', meta: { kind: 'price' } },
              { header: 'Volume', accessorKey: 'volume', meta: { kind: 'mw' } },
            ]}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <span className="label-caps">Total Volume</span>
            <span className="font-data">{totalVolume.toFixed(2)} MW</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <span className="label-caps">Weighted Price</span>
            <span className="font-data">{weighted.toFixed(2)}</span>
          </div>
        </div>
      </Panel>

      <div style={{ display: 'grid', gap: 10 }}>
        <Panel persona="dispatch" title="ML Recommendation Insights">
          <div className="font-data">Suggested Action: {recommendation.data?.action ?? '--'}</div>
          <div className="font-data">Suggested Target MW: {recommendation.data?.target_mw?.toFixed(2) ?? '--'}</div>
          <div className="font-data">Confidence Score: {recommendation.data?.confidence?.toFixed(2) ?? '--'}</div>
          <div style={{ marginTop: 8, background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <div className="label-caps">Model Lineage</div>
            <div className="font-data" style={{ marginTop: 4 }}>
              {latestLineage
                ? `${latestLineage.model_name} · run ${latestLineage.run_timestamp} · hash ${latestLineage.feature_hash.slice(0, 12)}...`
                : 'Lineage loading'}
            </div>
          </div>
        </Panel>
        <Panel persona="dispatch" title="Stack History">
          <DataTable
            data={(history.data ?? []).map((row) => ({ band: `Band ${row.band_index}`, price: row.price, volume: row.volume_mw, status: row.status, scenario: row.scenario }))}
            columns={[
              { header: 'Band', accessorKey: 'band' },
              { header: 'Scenario', accessorKey: 'scenario' },
              { header: 'Price', accessorKey: 'price', meta: { kind: 'price' } },
              { header: 'Vol', accessorKey: 'volume', meta: { kind: 'mw' } },
              { header: 'Status', accessorKey: 'status' },
            ]}
          />
        </Panel>
        <Panel persona="dispatch" title="Source">
          <div className="font-data">{market} · avg price {prices.data?.average_price?.toFixed(2) ?? '--'}</div>
        </Panel>
      </div>
    </div>
  );
}
