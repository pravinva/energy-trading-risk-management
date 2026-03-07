import { useEffect } from 'react';
import { PersonaSelector } from '@/pages/PersonaSelector';
import { useTradingStore, type Market } from '@/store/tradingStore';

function MarketPersonaEntry({ market }: { market: Market }): JSX.Element {
  const setMarket = useTradingStore((s) => s.setMarket);
  useEffect(() => {
    setMarket(market);
  }, [market, setMarket]);
  return <PersonaSelector />;
}

export function NEMPersonaEntry(): JSX.Element {
  return <MarketPersonaEntry market="NEM" />;
}

export function EPEXPersonaEntry(): JSX.Element {
  return <MarketPersonaEntry market="EPEX" />;
}

export function ERCOTPersonaEntry(): JSX.Element {
  return <MarketPersonaEntry market="ERCOT" />;
}
