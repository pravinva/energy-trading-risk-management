import { useState } from 'react';
import { Panel } from '@/components/primitives';
import { OfferBand } from '@/components/trading';
import { useDispatchRecommendation, useSubmitOfferStack } from '@/api/hooks/apex';
import { useDispatchStore } from '@/store/dispatchStore';

export function DispatchConsole(): JSX.Element {
  const { assetId, scenario, bands, setBand } = useDispatchStore();
  const submit = useSubmitOfferStack();
  const recommendation = useDispatchRecommendation(assetId);
  const [selected, setSelected] = useState(0);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <Panel persona="dispatch" title="Dispatch Offer Stack" subtitle="Create and submit bid bands" badge={assetId}>
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
          <button onClick={() => submit.mutate({ asset_id: assetId, scenario, bands })}>Submit Offer Stack</button>
        </div>
      </Panel>
      <Panel persona="dispatch" title="Dispatch Recommendation">
        <div className="font-data">Action: {recommendation.data?.action ?? '--'}</div>
        <div className="font-data">Target MW: {recommendation.data?.target_mw?.toFixed(2) ?? '--'}</div>
        <div className="font-data">Confidence: {recommendation.data?.confidence?.toFixed(2) ?? '--'}</div>
      </Panel>
    </div>
  );
}
