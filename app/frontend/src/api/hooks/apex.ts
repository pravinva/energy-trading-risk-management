import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

type ApiResponse<T> = { data: T; timestamp: string; region?: string };

export function useMarketSummary() {
  return useQuery({
    queryKey: ['apex', 'market-summary'],
    queryFn: () => apiClient.get<never, ApiResponse<{ active_markets: number; instruments_tracked: number; average_price: number }>>('/market/summary'),
    refetchInterval: 30000,
  });
}

export function useCurrentPrices() {
  return useQuery({
    queryKey: ['apex', 'prices'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ market: string; instrument: string; price: number; change_pct: number }>>>('/market/current-prices'),
    refetchInterval: 15000,
  });
}

export function useTradeBlotter() {
  return useQuery({
    queryKey: ['apex', 'trades', 'blotter'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ trade_id: string; instrument: string; side: string; volume_mw: number; price: number; mtm_pnl: number; trade_time: string }>>>('/trades/blotter'),
    refetchInterval: 5000,
  });
}

export function useCreateTrade() {
  return useMutation({
    mutationFn: (payload: { trader: string; instrument: string; side: string; volume_mw: number; price: number; counterparty: string }) =>
      apiClient.post<typeof payload, ApiResponse<{ trade_id: string; status: string }>>('/trades/entry', payload),
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ['apex', 'positions'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ instrument: string; net_position_mw: number; avg_trade_price: number }>>>('/positions/book'),
    refetchInterval: 5000,
  });
}

export function useSubmitOfferStack() {
  return useMutation({
    mutationFn: (payload: { asset_id: string; scenario: string; bands: Array<{ band_index: number; price: number; volume_mw: number }> }) =>
      apiClient.post<typeof payload, ApiResponse<{ weighted_offer_price: number; total_volume_mw: number }>>('/dispatch/offer-stack', payload),
  });
}

export function useDispatchRecommendation(assetId: string) {
  return useQuery({
    queryKey: ['apex', 'dispatch', assetId],
    queryFn: () => apiClient.get<never, ApiResponse<{ action: string; target_mw: number; confidence: number }>>(`/dispatch/recommendations/${assetId}`),
    enabled: Boolean(assetId),
    refetchInterval: 8000,
  });
}

export function useVaR() {
  return useMutation({
    mutationFn: (payload: { confidence: number; volatility: number; spot_price: number }) =>
      apiClient.post<typeof payload, ApiResponse<{ var_95: number; var_99: number; expected_shortfall_95: number; exposure_mw: number }>>('/risk/var/calculate', payload),
  });
}

export function useLimitStatus() {
  return useQuery({
    queryKey: ['apex', 'risk', 'limits'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ metric: string; current: number; limit: number; breached: boolean }>>>('/risk/limits/status'),
    refetchInterval: 8000,
  });
}

export function useRevenueStacking() {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'revenue'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ component: string; annual_value: number; contribution_pct: number }>>>('/portfolio/revenue-stacking'),
  });
}

export function usePPABook() {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'ppa'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ ppa_id: string; counterparty: string; volume_mw: number; strike_price: number; tenor_years: number }>>>('/portfolio/ppa-book'),
  });
}

export function useModelPerformance() {
  return useQuery({
    queryKey: ['apex', 'analytics', 'models'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ model_name: string; mape: number; rmse: number; r2: number }>>>('/analytics/model-performance'),
  });
}

export function useBacktests() {
  return useQuery({
    queryKey: ['apex', 'analytics', 'backtests'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ strategy: string; trades: number; win_rate: number; total_pnl: number; sharpe: number }>>>('/analytics/backtests'),
  });
}
