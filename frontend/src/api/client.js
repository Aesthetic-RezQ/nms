import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
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

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        const res = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        });
        localStorage.setItem('token', res.data.access_token);
        if (res.data.refresh_token) {
          localStorage.setItem('refresh_token', res.data.refresh_token);
        }
        return client(originalRequest);
      } catch (err) {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
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
