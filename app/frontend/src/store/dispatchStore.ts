import { create } from 'zustand';

type OfferBand = { band_index: number; price: number; volume_mw: number };

type DispatchState = {
  assetId: string;
  scenario: string;
  bands: OfferBand[];
  setBand: (index: number, value: Partial<OfferBand>) => void;
};

const initialBands: OfferBand[] = Array.from({ length: 5 }, (_, i) => ({
  band_index: i + 1,
  price: 80 + i * 10,
  volume_mw: 20 + i * 5,
}));

export const useDispatchStore = create<DispatchState>((set) => ({
  assetId: 'HORNSDALE_1',
  scenario: 'BASE',
  bands: initialBands,
  setBand: (index, value) =>
    set((state) => ({
      bands: state.bands.map((b, idx) => (idx === index ? { ...b, ...value } : b)),
    })),
}));
