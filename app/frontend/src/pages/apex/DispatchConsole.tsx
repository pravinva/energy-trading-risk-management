import { useEffect, useMemo, useState } from 'react';
import { DataTable, Panel } from '@/components/primitives';
import { OfferBand } from '@/components/trading';
import { useAcceptDispatchRecommendation, useDispatchAssets, useDispatchRecommendation, useDispatchServiceTypes, useDispatchStackHistory, useForecastMetadata, useLatestOfferStack, useMarketSummary, useModelLineage, usePredispatch, useSubmitOfferStack } from '@/api/hooks/apex';
import { useDispatchStore } from '@/store/dispatchStore';
import { useTradingStore } from '@/store/tradingStore';

export function DispatchConsole(): JSX.Element {
  const { assetId, scenario, serviceType, bands, setBand, setBands, resetBands, setAssetId, setServiceType } = useDispatchStore();
  const market = useTradingStore((s) => s.market);
  const prices = useMarketSummary();
  const submit = useSubmitOfferStack();
  const predispatch = usePredispatch(12, market);
  const forecastMeta = useForecastMetadata(market);
  const lineage = useModelLineage(market);
  const assetsQuery = useDispatchAssets(market);
  const serviceTypesQuery = useDispatchServiceTypes(market);
  const recommendation = useDispatchRecommendation(assetId);
  const acceptRecommendation = useAcceptDispatchRecommendation();
  const history = useDispatchStackHistory(assetId, 40);
  const latestStack = useLatestOfferStack(assetId);
  const [selected, setSelected] = useState(0);
  const assets = (assetsQuery.data ?? []).map((r) => r.asset_id);
  const serviceTypes = (serviceTypesQuery.data ?? []).map((r) => r.service_type);
  const strip = (predispatch.data ?? []).slice(0, 12);
  const totalVolume = useMemo(() => bands.reduce((sum, band) => sum + band.volume_mw, 0), [bands]);
  const weighted = useMemo(() => {
    const numerator = bands.reduce((sum, band) => sum + band.volume_mw * band.price, 0);
    return totalVolume > 0 ? numerator / totalVolume : 0;
  }, [bands, totalVolume]);
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
    const allZero = bands.every((b) => b.price <= 0 || b.volume_mw <= 0);
    if (live?.bands?.length && allZero) {
      setBands(live.bands);
    }
  }, [bands, latestStack.data, setBands]);

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

      <Panel persona="dispatch" title="Offer Stack Builder" subtitle={`${assetId} · ${serviceType}`}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
          <select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
            {assets.map((asset) => <option key={asset}>{asset}</option>)}
          </select>
          <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
            {serviceTypes.map((service) => <option key={service}>{service}</option>)}
          </select>
        </div>
        <div style={{ display: 'grid', gap: 8 }}>
          {bands.map((band, idx) => (
            <OfferBand
              key={band.band_index}
              bandIndex={band.band_index}
              price={band.price}
              volume={band.volume_mw}
              isSelected={selected === idx}
              onSelect={() => setSelected(idx)}
              onPriceChange={(value) => setBand(idx, { price: value })}
              onVolumeChange={(value) => setBand(idx, { volume_mw: value })}
            />
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <span className="label-caps">Total Volume</span>
            <span className="font-data">{totalVolume.toFixed(2)} MW</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <span className="label-caps">Weighted Price</span>
            <span className="font-data">{weighted.toFixed(2)}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={{ flex: 1 }} disabled={!assetId || !serviceType || bands.some((b) => b.price <= 0 || b.volume_mw <= 0)} onClick={() => submit.mutate({ asset_id: assetId, scenario: `${scenario}-${serviceType}`, bands })}>Submit Stack</button>
            <button
              onClick={() => {
                const live = latestStack.data;
                if (live?.bands?.length) {
                  setBands(live.bands);
                }
              }}
            >
              Load Rec
            </button>
            <button onClick={resetBands}>Clear</button>
          </div>
        </div>
      </Panel>

      <div style={{ display: 'grid', gap: 10 }}>
        <Panel persona="dispatch" title="ML Recommendations">
          <div className="font-data">Action: {recommendation.data?.action ?? '--'}</div>
          <div className="font-data">Target MW: {recommendation.data?.target_mw?.toFixed(2) ?? '--'}</div>
          <div className="font-data">Confidence: {recommendation.data?.confidence?.toFixed(2) ?? '--'}</div>
          <div style={{ marginTop: 8, background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-subtle)', padding: 8 }}>
            <div className="label-caps">Model Lineage</div>
            <div className="font-data" style={{ marginTop: 4 }}>
              {latestLineage
                ? `${latestLineage.model_name} · run ${latestLineage.run_timestamp} · hash ${latestLineage.feature_hash.slice(0, 12)}...`
                : 'Lineage loading'}
            </div>
          </div>
          <button
            style={{ width: '100%', marginTop: 8 }}
            disabled={!assetId || !recommendation.data}
            onClick={() => {
              if (!recommendation.data) return;
              acceptRecommendation.mutate({
                asset_id: assetId,
                action: recommendation.data.action,
                target_mw: recommendation.data.target_mw,
                confidence: recommendation.data.confidence,
              });
            }}
          >
            Accept
          </button>
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
