import { create } from 'zustand';

type TradingSessionState = {
  persona: 'dispatch' | 'trader' | 'quant' | 'risk' | 'portfolio';
  selectedInstrument: string;
  traderName: string;
  setPersona: (persona: TradingSessionState['persona']) => void;
  setSelectedInstrument: (instrument: string) => void;
  setTraderName: (name: string) => void;
};

export const useTradingStore = create<TradingSessionState>((set) => ({
  persona: 'trader',
  selectedInstrument: 'NSW_BASE',
  traderName: 'APEX Trader',
  setPersona: (persona) => set({ persona }),
  setSelectedInstrument: (selectedInstrument) => set({ selectedInstrument }),
  setTraderName: (traderName) => set({ traderName }),
}));
