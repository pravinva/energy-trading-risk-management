import { create } from 'zustand';

export type Market = 'NEM' | 'EPEX' | 'ERCOT';

type TradingSessionState = {
  persona: 'dispatch' | 'trader' | 'quant' | 'risk' | 'portfolio';
  market: Market;
  selectedInstrument: string;
  traderName: string;
  sessionPnl: number;
  setPersona: (persona: TradingSessionState['persona']) => void;
  setMarket: (market: Market) => void;
  setSelectedInstrument: (instrument: string) => void;
  setTraderName: (name: string) => void;
  setSessionPnl: (value: number) => void;
};

export const useTradingStore = create<TradingSessionState>((set) => ({
  persona: 'trader',
  market: 'NEM',
  selectedInstrument: '',
  traderName: '',
  sessionPnl: 0,
  setPersona: (persona) => set({ persona }),
  setMarket: (market) =>
    set({
      market,
      sessionPnl: 0,
    }),
  setSelectedInstrument: (selectedInstrument) => set({ selectedInstrument }),
  setTraderName: (traderName) => set({ traderName }),
  setSessionPnl: (sessionPnl) => set({ sessionPnl }),
}));
