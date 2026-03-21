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

// ============================================================================
// Forecasting & Predictive Analytics Hooks
// ============================================================================

export function useWeatherForecast(regionId: string = 'NSW1', days: number = 7) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'weather', regionId, days],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            forecast_id: string;
            region_id: string;
            forecast_datetime: string;
            temperature_celsius: number;
            wind_speed_ms: number;
            solar_irradiance_wm2: number;
            precipitation_mm: number;
            humidity_percent: number;
            confidence_level: string;
            forecast_horizon_hours: number;
          }>
        >
      >('/forecasting/weather', {
        params: { region_id: regionId, days },
      }),
    refetchInterval: 30000,
  });
}

export function useWeatherImpact(regionId: string = 'NSW1') {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'weather-impact', regionId],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            region_id: string;
            weather_parameter: string;
            price_correlation: number;
            price_impact_per_unit: number;
            volatility_impact: number;
            sample_size: number;
            last_updated: string | null;
          }>
        >
      >('/forecasting/weather/impact', {
        params: { region_id: regionId },
      }),
    refetchInterval: 60000,
  });
}

export function useVolumeForecast(regionId: string = 'NSW1', days: number = 15) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'volume', regionId, days],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            forecast_id: string;
            region_id: string;
            forecast_date: string;
            forecast_type: string;
            volume_mwh: number;
            base_volume_mwh: number;
            weather_impact_pct: number;
            maintenance_impact_pct: number;
            outage_impact_pct: number;
            market_demand_factor: number;
            confidence_level: string;
          }>
        >
      >('/forecasting/volume', {
        params: { region_id: regionId, days },
      }),
    refetchInterval: 30000,
  });
}

export function useVolumeForecastSummary(regionId: string = 'NSW1', days: number = 15) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'volume-summary', regionId, days],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<{
          region_id: string;
          total_days: number;
          buy_days: number;
          sell_days: number;
          avg_volume_mwh: number;
          total_buy_volume_mwh: number;
          total_sell_volume_mwh: number;
        }>
      >('/forecasting/volume/summary', {
        params: { region_id: regionId, days },
      }),
    refetchInterval: 30000,
  });
}

export function useProductionForecast(regionId: string = 'NSW1', assetType: string | null = null, days: number = 7) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'production', regionId, assetType, days],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            forecast_id: string;
            region_id: string;
            forecast_datetime: string;
            asset_type: string;
            generation_mw: number;
            capacity_mw: number;
            efficiency_percent: number;
            availability_percent: number;
            confidence_level: string;
            forecast_horizon_hours: number;
          }>
        >
      >('/forecasting/production', {
        params: { region_id: regionId, asset_type: assetType, days },
      }),
    refetchInterval: 30000,
  });
}

export function useGenerationMix(regionId: string = 'NSW1', hours: number = 24) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'generation-mix', regionId, hours],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            region_id: string;
            reading_datetime: string;
            asset_type: string;
            generation_mw: number;
            total_generation_mw: number;
            mix_percentage: number;
          }>
        >
      >('/forecasting/generation-mix', {
        params: { region_id: regionId, hours },
      }),
    refetchInterval: 30000,
  });
}

export function usePlantStatus(regionId: string = 'NSW1', eventType: string | null = null, days: number = 14) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'plant-status', regionId, eventType, days],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            event_id: string;
            plant_name: string;
            plant_type: string;
            region_id: string;
            event_type: string;
            start_datetime: string;
            end_datetime: string;
            capacity_impact_mw: number;
            grid_impact: string;
            description: string;
            status: string;
          }>
        >
      >('/forecasting/plant-status', {
        params: { region_id: regionId, event_type: eventType, days },
      }),
    refetchInterval: 30000,
  });
}

export function usePriceForecast(regionId: string = 'NSW1', marketType: string = 'DAY_AHEAD', hours: number = 24) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'price', regionId, marketType, hours],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            forecast_id: string;
            region_id: string;
            instrument: string;
            forecast_datetime: string;
            forecast_price: number;
            actual_price: number | null;
            error: number | null;
            abs_error: number | null;
            mape: number | null;
            market_type: string;
            confidence_level: string;
            forecast_horizon_hours: number;
          }>
        >
      >('/forecasting/price', {
        params: { region_id: regionId, market_type: marketType, hours },
      }),
    refetchInterval: 30000,
  });
}

export function useExtremeEvents(regionId: string = 'NSW1', severity: string | null = null) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'extreme-events', regionId, severity],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            event_id: string;
            region_id: string;
            event_type: string;
            severity: string;
            start_datetime: string;
            end_datetime: string;
            impact_description: string;
            price_impact_pct: number;
            trading_alert_level: string;
            confidence_level: number;
          }>
        >
      >('/forecasting/extreme-events', {
        params: { region_id: regionId, severity },
      }),
    refetchInterval: 30000,
  });
}

export function useForecastingModelPerformance(modelType: string | null = null, regionId: string | null = null) {
  return useQuery({
    queryKey: ['apex', 'forecasting', 'model-performance', modelType, regionId],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            model_id: string;
            model_name: string;
            model_type: string;
            region_id: string;
            mape: number;
            mae: number;
            rmse: number;
            r2_score: number;
            bias: number;
            evaluation_date: string;
            algorithm: string;
            mlflow_run_id: string | null;
          }>
        >
      >('/forecasting/model-performance', {
        params: { model_type: modelType, region_id: regionId },
      }),
    refetchInterval: 60000,
  });
}

// ============================================================================
// Strategy & Agents Hooks
// ============================================================================

export function useStrategies(status: string | null = null) {
  return useQuery({
    queryKey: ['apex', 'strategies', 'list', status],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            strategy_id: string;
            strategy_name: string;
            strategy_type: string;
            description: string;
            region_id: string;
            status: string;
            created_at: string;
          }>
        >
      >('/strategies/list', {
        params: status ? { status } : {},
      }),
    refetchInterval: 10000,
  });
}

export function useBacktestRun() {
  return useMutation({
    mutationFn: (payload: { strategy_type: string; region_id: string; start_date: string; end_date: string; initial_capital: number; parameters?: Record<string, any> }) =>
      apiClient.post<
        typeof payload,
        ApiResponse<{
          backtest_id: string;
          strategy_name: string;
          total_trades: number;
          win_rate: number;
          total_return_pct: number;
          sharpe_ratio: number;
          max_drawdown_pct: number;
          total_pnl: number;
        }>
      >('/strategies/backtest', payload),
  });
}

export function useBacktestResults(strategyType: string | null = null, limit: number = 10) {
  return useQuery({
    queryKey: ['apex', 'strategies', 'backtest-results', strategyType, limit],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            backtest_id: string;
            strategy_name: string;
            total_trades: number;
            win_rate: number;
            total_return_pct: number;
            sharpe_ratio: number;
            max_drawdown_pct: number;
            total_pnl: number;
          }>
        >
      >('/strategies/backtest/results', {
        params: { strategy_type: strategyType, limit },
      }),
    refetchInterval: 15000,
  });
}

export function useStrategySignals(strategyId: string | null = null, hours: number = 24) {
  return useQuery({
    queryKey: ['apex', 'strategies', 'signals', strategyId, hours],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            signal_id: string;
            strategy_id: string;
            timestamp: string;
            signal_type: string;
            action: string;
            instrument: string;
            volume_mw: number;
            confidence: number;
            reasoning: string;
            executed: boolean;
          }>
        >
      >('/strategies/signals', {
        params: { strategy_id: strategyId, hours },
      }),
    refetchInterval: 5000,
  });
}

export function useStrategyPositions(strategyId: string | null = null) {
  return useQuery({
    queryKey: ['apex', 'strategies', 'positions', strategyId],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            position_id: string;
            strategy_id: string;
            instrument: string;
            entry_price: number;
            volume_mw: number;
            unrealized_pnl: number;
            status: string;
          }>
        >
      >('/strategies/positions', {
        params: strategyId ? { strategy_id: strategyId } : {},
      }),
    refetchInterval: 5000,
  });
}

export function useAgents() {
  return useQuery({
    queryKey: ['apex', 'strategies', 'agents'],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            agent_id: string;
            agent_type: string;
            agent_name: string;
            description: string;
            status: string;
          }>
        >
      >('/strategies/agents'),
    refetchInterval: 20000,
  });
}

export function useAgentMessages(sessionId: string | null = null, limit: number = 50) {
  return useQuery({
    queryKey: ['apex', 'strategies', 'agent-messages', sessionId, limit],
    queryFn: () =>
      apiClient.get<
        never,
        ApiResponse<
          Array<{
            message_id: string;
            from_agent_id: string;
            to_agent_id: string;
            message_type: string;
            timestamp: string;
            content: string;
            status: string;
          }>
        >
      >('/strategies/agents/messages', {
        params: { session_id: sessionId, limit },
      }),
    refetchInterval: 5000,
  });
}
