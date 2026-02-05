import { create } from 'zustand';
import { authAPI } from '../utils/api.js';

const getToken = () => localStorage.getItem('token');

export const useAuthStore = create((set) => ({
  user: null,
  token: getToken(),
  isAuthenticated: !!getToken(),
  isLoading: false,
  error: null,
  login: (token) => {
    localStorage.setItem('token', token);
    set({ token, isAuthenticated: true, error: null });
  },
  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await authAPI.register(data);
      set({ isLoading: false });
      return true;
    } catch (err) {
      set({ isLoading: false, error: err });
      return false;
    }
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, isAuthenticated: false, user: null });
  },
  fetchUser: async () => {
    set({ isLoading: true });
    try {
      const res = await authAPI.getMe();
      set({ user: res.data, isLoading: false });
    } catch (err) {
      localStorage.removeItem('token');
      set({ user: null, token: null, isAuthenticated: false, isLoading: false, error: err });
    }
  },
}));
