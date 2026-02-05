import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const unitsAPI = {
  create: (data) => api.post('/units', data),
  getAll: () => api.get('/units'),
};

export const registrationAPI = {
  verifyToken: (token) => api.get(`/register/verify-token/${token}`),
  start: (data) => api.post('/register/start', data),
  checkLiveness: (data) => api.post('/register/liveness-check', data),
  complete: (data) => api.post('/register/complete', data),
};

export const attendanceAPI = {
  create: (data) => api.post('/attendance', data),
  getStatus: (id) => api.get(`/attendance/sessions/${id}/status`),
  getSessionDetails: (id) => api.get(`/attendance/sessions/${id}`),
  listSessions: (unitId) =>
    unitId ? api.get(`/attendance/sessions?unit_id=${unitId}`) : api.get('/attendance/sessions'),
};
