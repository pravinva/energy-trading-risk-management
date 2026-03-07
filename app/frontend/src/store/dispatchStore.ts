import { create } from 'zustand';

type OfferBand = { band_index: number; price: number; volume_mw: number };

type DispatchState = {
  assetId: string;
  scenario: string;
  serviceType: string;
  bands: OfferBand[];
  setAssetId: (assetId: string) => void;
  setServiceType: (serviceType: string) => void;
  setBand: (index: number, value: Partial<OfferBand>) => void;
  setBands: (bands: OfferBand[]) => void;
  resetBands: () => void;
};

const initialBands: OfferBand[] = Array.from({ length: 5 }, (_, i) => ({
  band_index: i + 1,
  price: 0,
  volume_mw: 0,
}));

export const useDispatchStore = create<DispatchState>((set) => ({
  assetId: '',
  scenario: 'BASE',
  serviceType: '',
  bands: initialBands,
  setAssetId: (assetId) => set({ assetId }),
  setServiceType: (serviceType) => set({ serviceType }),
  setBand: (index, value) =>
    set((state) => ({
      bands: state.bands.map((b, idx) => (idx === index ? { ...b, ...value } : b)),
    })),
  setBands: (bands) => set({ bands }),
  resetBands: () => set({ bands: initialBands }),
}));
