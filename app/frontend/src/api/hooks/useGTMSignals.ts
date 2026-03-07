import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export const useGTMStatus = () => useQuery({ queryKey: ['gtm', 'status'], queryFn: () => apiClient.get('/gtm/status') });
export const useGTMSignals = (region: string, enabled: boolean) => useQuery({ queryKey: ['gtm', 'signals', region], queryFn: () => apiClient.get(`/gtm/signals/${region}`), enabled, staleTime: 300000 });
