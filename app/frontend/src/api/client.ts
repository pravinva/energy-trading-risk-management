import axios from 'axios';

export const apiClient = axios.create({ baseURL: '/api/v1', timeout: 30000 });

apiClient.interceptors.request.use((config) => {
  const path = window.location.pathname;
  const region = path.split('/')[1] || 'global';
  config.headers['X-Region'] = region;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response.data.data,
  (error) => Promise.reject({ message: error?.response?.data?.detail ?? 'Request failed', status: error?.response?.status ?? 500 }),
);
