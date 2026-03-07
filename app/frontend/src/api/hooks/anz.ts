import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export const useANZCurrentPrices = () => useQuery({ queryKey: ['anz', 'prices', 'current'], queryFn: () => apiClient.get('/anz/prices/current'), refetchInterval: 15000 });
export const useANZPriceHistory = (hours = 24, regionId?: string) => useQuery({ queryKey: ['anz', 'prices', 'history', hours, regionId], queryFn: () => apiClient.get('/anz/prices/history', { params: { hours, region_id: regionId } }) });
export const useANZBESSFleet = () => useQuery({ queryKey: ['anz', 'bess', 'fleet'], queryFn: () => apiClient.get('/anz/bess/fleet'), refetchInterval: 30000 });
export const useANZBESSTelemetry = (duid: string, hours = 24) => useQuery({ queryKey: ['anz', 'bess', duid, 'telemetry', hours], queryFn: () => apiClient.get(`/anz/bess/${duid}/telemetry`, { params: { hours } }), enabled: Boolean(duid) });
export const useANZBESSRevenue = (duid: string, days = 30) => useQuery({ queryKey: ['anz', 'bess', duid, 'revenue', days], queryFn: () => apiClient.get(`/anz/bess/${duid}/revenue`, { params: { days } }), enabled: Boolean(duid) });
export const useANZFCASSummary = () => useQuery({ queryKey: ['anz', 'fcas'], queryFn: () => apiClient.get('/anz/fcas/summary'), refetchInterval: 30000 });
export const useANZSpikes = (days = 30) => useQuery({ queryKey: ['anz', 'spikes', days], queryFn: () => apiClient.get('/anz/spikes', { params: { days } }) });
