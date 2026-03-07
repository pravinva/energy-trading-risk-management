import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export const useEuropePricesCurrent = () => useQuery({ queryKey: ['europe', 'prices', 'current'], queryFn: () => apiClient.get('/europe/prices/current'), refetchInterval: 60000 });
export const useEuropePriceHistory = (biddingZone: string, hours = 168) => useQuery({ queryKey: ['europe', 'prices', 'history', biddingZone, hours], queryFn: () => apiClient.get('/europe/prices/history', { params: { bidding_zone: biddingZone, hours } }) });
export const useEuropeGenerationMix = (biddingZone: string) => useQuery({ queryKey: ['europe', 'mix', biddingZone], queryFn: () => apiClient.get('/europe/generation/mix', { params: { bidding_zone: biddingZone } }), refetchInterval: 300000 });
export const useEuropeSparkSpreads = (biddingZone: string) => useQuery({ queryKey: ['europe', 'spark', biddingZone], queryFn: () => apiClient.get('/europe/spreads/spark', { params: { bidding_zone: biddingZone } }), refetchInterval: 300000 });
export const useEuropeOpenLinkAssets = () => useQuery({ queryKey: ['europe', 'openlink-assets'], queryFn: () => apiClient.get('/europe/assets/openlink-incumbent'), staleTime: 600000 });
export const useEuropeCrossBorderFlows = () => useQuery({ queryKey: ['europe', 'flows'], queryFn: () => apiClient.get('/europe/flows/cross-border'), refetchInterval: 60000 });
export const useEuropeREMITAudit = (biddingZone: string, date: string) => useQuery({ queryKey: ['europe', 'audit', biddingZone, date], queryFn: () => apiClient.get('/europe/audit/remit', { params: { bidding_zone: biddingZone, audit_date: date } }), enabled: Boolean(biddingZone && date) });
