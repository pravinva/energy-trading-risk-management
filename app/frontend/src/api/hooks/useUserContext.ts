import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
export const useUserContext = () => useQuery({ queryKey: ['user-context'], queryFn: () => apiClient.get('/user/me'), staleTime: 300000 });
