import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export const useAmericasCurrentPrices = (isoId?: string) => useQuery({ queryKey: ['americas', 'prices', 'current', isoId], queryFn: () => apiClient.get('/americas/prices/current', { params: { iso_id: isoId } }), refetchInterval: 30000 });
export const useAmericasLMPHistory = (isoId: string, hours = 24) => useQuery({ queryKey: ['americas', 'history', isoId, hours], queryFn: () => apiClient.get('/americas/prices/history', { params: { iso_id: isoId, hours } }), refetchInterval: 60000 });
export const useERCOTRTCBComparison = (resourceId: string) => useQuery({ queryKey: ['americas', 'rtcb', resourceId], queryFn: () => apiClient.get(`/americas/ercot/rtcb-comparison/${resourceId}`), staleTime: 300000, enabled: Boolean(resourceId) });
export const usePJMCapacityAuctions = () => useQuery({ queryKey: ['americas', 'pjm-auctions'], queryFn: () => apiClient.get('/americas/pjm/capacity-auctions'), staleTime: 86400000 });
export const useIESONodalBasis = () => useQuery({ queryKey: ['americas', 'ieso-basis'], queryFn: () => apiClient.get('/americas/ieso/nodal-basis'), staleTime: 300000 });
export const useMultiISORowCount = () => useQuery({ queryKey: ['americas', 'row-count'], queryFn: async () => {
  const rows = await apiClient.get('/americas/prices/current');
  return rows.length;
}, staleTime: 300000 });
