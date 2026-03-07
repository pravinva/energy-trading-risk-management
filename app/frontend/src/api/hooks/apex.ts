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

export function usePredispatch(hours = 12, market: 'NEM' | 'EPEX' | 'ERCOT' = 'NEM') {
  return useQuery({
    queryKey: ['apex', 'market', 'predispatch', market, hours],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ interval_start: string; region: string; forecast_price: number; forecast_demand_mw: number }>>>('/market/predispatch', { params: { market, hours } }),
    refetchInterval: 15000,
  });
}

export function useForecastMetadata(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'market', 'forecast-metadata', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<{ market: string; model_name: string; last_run_utc: string | null; points_available: number; first_forecast_utc: string | null; last_forecast_utc: string | null }>>('/market/forecast-metadata', {
        params: { market },
      }),
    refetchInterval: 20000,
  });
}

export function useMarketInstruments(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'market', 'instruments', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ market: string; instrument: string }>>>('/market/instruments', {
        params: { market },
      }),
    refetchInterval: 30000,
  });
}

export function useMarketSpotPrice(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'market', 'spot-price', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<{ market: string; spot_price: number; as_of_utc: string }>>('/market/spot-price', {
        params: { market },
      }),
    refetchInterval: 15000,
  });
}

export function useCurrentPrices() {
  return useQuery({
    queryKey: ['apex', 'prices'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ market: string; instrument: string; price: number; change_pct: number }>>>('/market/current-prices'),
    refetchInterval: 15000,
  });
}

export function useInstrumentQuote(market: 'NEM' | 'EPEX' | 'ERCOT', instrument: string) {
  return useQuery({
    queryKey: ['apex', 'market', 'instrument-quote', market, instrument],
    queryFn: () =>
      apiClient.get<never, ApiResponse<{ market: string; instrument: string; last_price: number; change_pct: number; bid: number; offer: number; volume: number; status: string }>>('/market/instrument-quote', {
        params: { market, instrument },
      }),
    enabled: Boolean(instrument),
    refetchInterval: 8000,
  });
}

export function useTradeBlotter() {
  return useQuery({
    queryKey: ['apex', 'trades', 'blotter'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ trade_id: string; instrument: string; side: string; volume_mw: number; price: number; mtm_pnl: number; trade_time: string }>>>('/trades/blotter'),
    refetchInterval: 5000,
  });
}

export function useMarketTradeBlotter(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'trades', 'blotter', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ trade_id: string; instrument: string; side: string; volume_mw: number; price: number; mtm_pnl: number; trade_time: string }>>>('/trades/blotter', {
        params: { market },
      }),
    refetchInterval: 5000,
  });
}

export function useExposureHeatmap(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'trades', 'exposure-heatmap', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ instrument: string; q1: number; q2: number; q3: number; q4: number }>>>('/trades/exposure-heatmap', {
        params: { market },
      }),
    refetchInterval: 5000,
  });
}

export function useMarketPnlDaily(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'trades', 'pnl-daily', market],
    queryFn: () => apiClient.get<never, ApiResponse<{ market: string; pnl_daily: number }>>('/trades/pnl-daily', { params: { market } }),
    refetchInterval: 10000,
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

export function useLatestOfferStack(assetId: string) {
  return useQuery({
    queryKey: ['apex', 'dispatch', 'offer-stack', 'latest', assetId],
    queryFn: () =>
      apiClient.get<never, ApiResponse<{ asset_id: string; scenario: string; created_at: string; bands: Array<{ band_index: number; price: number; volume_mw: number }> } | null>>('/dispatch/offer-stack/latest', {
        params: { asset_id: assetId },
      }),
    enabled: Boolean(assetId),
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

export function useAcceptDispatchRecommendation() {
  return useMutation({
    mutationFn: (payload: { asset_id: string; action: string; target_mw: number; confidence: number }) =>
      apiClient.post<typeof payload, ApiResponse<{ asset_id: string; action: string; target_mw: number; confidence: number; accepted_at: string }>>('/dispatch/recommendations/accept', payload),
  });
}

export function useDispatchAssets(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'dispatch', 'assets', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ asset_id: string }>>>('/dispatch/assets', {
        params: { market },
      }),
  });
}

export function useDispatchServiceTypes(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'dispatch', 'service-types', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ service_type: string }>>>('/dispatch/service-types', {
        params: { market },
      }),
  });
}

export function useDispatchStackHistory(assetId: string, limit = 30) {
  return useQuery({
    queryKey: ['apex', 'dispatch', 'stack-history', assetId, limit],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ scenario: string; band_index: number; price: number; volume_mw: number; created_at: string; status: string }>>>('/dispatch/stack-history', {
        params: { asset_id: assetId, limit },
      }),
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

export function useStressScenarios(market: 'NEM' | 'EPEX' | 'ERCOT', spotPrice: number, volatility: number) {
  return useQuery({
    queryKey: ['apex', 'risk', 'stress-scenarios', market, spotPrice, volatility],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ scenario: string; shock: string; impact: number }>>>('/risk/stress-scenarios', {
        params: { market, spot_price: spotPrice, volatility },
      }),
    refetchInterval: 10000,
  });
}

export function useStressRunset(market: 'NEM' | 'EPEX' | 'ERCOT', spotPrice: number) {
  return useQuery({
    queryKey: ['apex', 'risk', 'stress-runset', market, spotPrice],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ scenario: string; confidence: number; volatility: number; var95: number; var99: number; es95: number }>>>('/risk/stress-runset', {
        params: { market, spot_price: spotPrice },
      }),
    enabled: spotPrice > 0,
  });
}

export function useLimitStatus() {
  return useQuery({
    queryKey: ['apex', 'risk', 'limits'],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ metric: string; current: number; limit: number; breached: boolean }>>>('/risk/limits/status'),
    refetchInterval: 8000,
  });
}

export function useCreditExposure(market: 'NEM' | 'EPEX' | 'ERCOT' | 'GLOBAL' = 'GLOBAL') {
  return useQuery({
    queryKey: ['apex', 'risk', 'credit-exposure', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ counterparty: string; trades: number; gross_mw: number; mtm_pnl: number }>>>('/risk/credit-exposure', {
        params: { market },
      }),
    refetchInterval: 10000,
  });
}

export function useRevenueStacking(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'revenue', market],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ component: string; annual_value: number; contribution_pct: number }>>>('/portfolio/revenue-stacking', { params: { market } }),
  });
}

export function usePPABook(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'ppa', market],
    queryFn: () => apiClient.get<never, ApiResponse<Array<{ ppa_id: string; counterparty: string; volume_mw: number; strike_price: number; tenor_years: number }>>>('/portfolio/ppa-book', { params: { market } }),
  });
}

export function useAssetBenchmark(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'benchmark', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ rank: number; asset: string; rev_per_mw: number; vs_benchmark_pct: number }>>>('/portfolio/asset-benchmark', {
        params: { market },
      }),
  });
}

export function usePortfolioSimulation(market: 'NEM' | 'EPEX' | 'ERCOT', durationHours: number, ancillaryPct: number, ppaMw: number) {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'simulation', market, durationHours, ancillaryPct, ppaMw],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ component: string; annual_value: number; contribution_pct: number }>>>('/portfolio/simulation', {
        params: { market, duration_hours: durationHours, ancillary_pct: ancillaryPct, ppa_mw: ppaMw },
      }),
  });
}

export function usePortfolioSimulationDefaults(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'portfolio', 'simulation-defaults', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<{ market: string; duration_hours_default: number; duration_hours_max: number; ancillary_pct_default: number; ancillary_pct_max: number; ppa_mw_default: number; ppa_mw_max: number; ppa_mtm_factor: number }>>('/portfolio/simulation-defaults', {
        params: { market },
      }),
    refetchInterval: 60000,
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

export function useBacktestStrategies(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'analytics', 'strategies', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ market: string; strategy: string; available: boolean }>>>('/analytics/strategies', {
        params: { market },
      }),
    refetchInterval: 60000,
  });
}

export function useModelLineage(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'analytics', 'model-lineage', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ market: string; model_name: string; run_timestamp: string; training_start_utc: string; training_end_utc: string; feature_set: string; feature_hash: string }>>>('/analytics/model-lineage', {
        params: { market },
      }),
    refetchInterval: 20000,
  });
}

export function useTradeCounterparties(market: 'NEM' | 'EPEX' | 'ERCOT') {
  return useQuery({
    queryKey: ['apex', 'trades', 'counterparties', market],
    queryFn: () =>
      apiClient.get<never, ApiResponse<Array<{ counterparty: string }>>>('/trades/counterparties', {
        params: { market },
      }),
    refetchInterval: 30000,
  });
}
