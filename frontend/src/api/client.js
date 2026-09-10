import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

// Add trailing slashes only to collection endpoints (single-segment paths
// like /categories, /groups) to prevent FastAPI 301 redirects that break
// cross-port CORS. Sub-routes like /devices/123 are left unchanged.
client.interceptors.request.use((config) => {
  if (config.url) {
    const qIndex = config.url.indexOf('?');
    const path = qIndex >= 0 ? config.url.substring(0, qIndex) : config.url;
    const segments = path.split('/').filter(Boolean);
    if (segments.length === 1 && !path.endsWith('/')) {
      config.url = path + '/' + (qIndex >= 0 ? config.url.substring(qIndex) : '');
    }
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthRequest = originalRequest?.url?.includes('/auth/');
    if (error.response?.status === 401 && !isAuthRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await axios.post('/api/auth/refresh', null, { withCredentials: true });
        return client(originalRequest);
      } catch (err) {
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  }
);

export const get = (url, config) => client.get(url, config);
export const post = (url, data, config) => client.post(url, data, config);
export const put = (url, data, config) => client.put(url, data, config);
export const del = (url, config) => client.delete(url, config);

export default client;
