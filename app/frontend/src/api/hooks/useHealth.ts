import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
export const useHealth = () => useQuery({ queryKey: ['health'], queryFn: () => apiClient.get('/health/'), refetchInterval: 60000 });
