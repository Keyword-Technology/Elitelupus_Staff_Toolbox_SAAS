import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const api = axios.create({
  baseURL: API_URL ? `${API_URL}/api` : '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = Cookies.get('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/token/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;
          Cookies.set('access_token', access, { expires: 1 });

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// API helpers
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/token/', { username, password }),
  register: (data: { username: string; email: string; password: string; password_confirm: string }) =>
    api.post('/auth/register/', data),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
  profile: () => api.get('/auth/profile/'),
  updateProfile: (data: any) => api.patch('/auth/profile/', data),
  changePassword: (data: { old_password: string; new_password: string; new_password_confirm: string }) =>
    api.post('/auth/password/change/', data),
  timezones: () => api.get('/auth/timezones/'),
  socialStatus: () => api.get('/auth/social/status/'),
  unlinkSocial: (provider: string) => api.post(`/auth/social/unlink/${provider}/`),
};

export const staffAPI = {
  roster: (params?: string) => api.get(`/staff/roster/${params || ''}`),
  sync: () => api.post('/staff/sync/'),
  syncLogs: () => api.get('/staff/sync/logs/'),
  roles: () => api.get('/staff/roles/'),
  myProfile: () => api.get('/staff/me/'),
  details: (id: number) => api.get(`/staff/roster/${id}/details/`),
  sessions: (id: number, params?: string) => api.get(`/staff/roster/${id}/sessions/${params || ''}`),
  stats: (id: number, params?: string) => api.get(`/staff/roster/${id}/stats/${params || ''}`),
};

export const counterAPI = {
  get: () => api.get('/counters/'),
  update: (type: string, action: string, value?: number, note?: string) =>
    api.post(`/counters/update/${type}/`, { action, value, note }),
  stats: () => api.get('/counters/stats/'),
  history: (type?: string) =>
    api.get('/counters/history/', { params: { type } }),
  leaderboard: (period?: string, type?: string) =>
    api.get('/counters/leaderboard/', { params: { period, type } }),
};

export const serverAPI = {
  list: () => api.get('/servers/'),
  status: () => api.get('/servers/status/'),
  refresh: () => api.post('/servers/refresh/'),
  distribution: () => api.get('/servers/distribution/'),
  players: (id: number) => api.get(`/servers/${id}/players/`),
  history: (id: number) => api.get(`/servers/${id}/history/`),
  stats: (id: number) => api.get(`/servers/${id}/stats/`),
  playerLookup: (steam_id: string, player_names?: string[]) => 
    api.get('/servers/player-lookup/', { 
      params: { 
        steam_id,
        player_names: player_names?.join(',') || ''
      } 
    }),
};

export const templateAPI = {
  refunds: (status?: string) =>
    api.get('/templates/refunds/', { params: { status } }),
  createRefund: (data: any) => api.post('/templates/refunds/', data),
  updateRefund: (id: number, data: any) =>
    api.patch(`/templates/refunds/${id}/`, data),
  deleteRefund: (id: number) => api.delete(`/templates/refunds/${id}/`),
  categories: () => api.get('/templates/categories/'),
  responses: (category?: number) =>
    api.get('/templates/responses/', { params: { category } }),
  steamLookup: (steam_id: string) =>
    api.post('/templates/steam-lookup/', { steam_id }),
  refundQuestion: () => api.get('/templates/refund-question/'),
  
  // Steam Profile Notes
  steamNotes: (steam_id_64: string) =>
    api.get('/templates/steam-notes/', { params: { steam_id_64 } }),
  createSteamNote: (data: any) => api.post('/templates/steam-notes/', data),
  updateSteamNote: (id: number, data: any) =>
    api.patch(`/templates/steam-notes/${id}/`, data),
  deleteSteamNote: (id: number) => api.delete(`/templates/steam-notes/${id}/`),
  
  // Steam Profile Bookmarks
  steamBookmarks: () => api.get('/templates/steam-bookmarks/'),
  createSteamBookmark: (data: any) => api.post('/templates/steam-bookmarks/', data),
  updateSteamBookmark: (id: number, data: any) =>
    api.patch(`/templates/steam-bookmarks/${id}/`, data),
  deleteSteamBookmark: (id: number) => api.delete(`/templates/steam-bookmarks/${id}/`),
  
  // Get servers list
  getServers: () => api.get('/servers/'),
};

export const rulesAPI = {
  all: () => api.get('/rules/'),
  categories: () => api.get('/rules/categories/'),
  category: (id: number) => api.get(`/rules/categories/${id}/`),
  search: (q: string) => api.get('/rules/search/', { params: { q } }),
  jobs: () => api.get('/rules/jobs/'),
  jobSearch: (q: string) => api.get('/rules/jobs/search/', { params: { q } }),
};

export const systemAPI = {
  // Environment Variables
  envList: () => api.get('/system/env/'),
  envUpdate: (key: string, value: string) => api.post(`/system/env/${key}/`, { value }),
  
  // System Settings
  settings: () => api.get('/system/settings/'),
  createSetting: (data: any) => api.post('/system/settings/', data),
  updateSetting: (id: number, data: any) => api.patch(`/system/settings/${id}/`, data),
  deleteSetting: (id: number) => api.delete(`/system/settings/${id}/`),
  
  // Counter Quotas
  quotas: () => api.get('/system-settings/quotas/'),
  
  // Managed Servers
  servers: () => api.get('/system/servers/'),
  createServer: (data: any) => api.post('/system/servers/', data),
  updateServer: (id: number, data: any) => api.patch(`/system/servers/${id}/`, data),
  deleteServer: (id: number) => api.delete(`/system/servers/${id}/`),
  syncServers: () => api.post('/system/servers/sync/'),
  
  // Audit Logs
  auditLogs: () => api.get('/system/audit-logs/'),
};
