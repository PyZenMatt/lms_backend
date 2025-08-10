import api from '../core/axiosClient';

export const signup = (data) => api.post('register/', data);
export const login = (data) => api.post('login/', data);
export const logout = (refreshToken = null) => {
  const payload = {};
  if (refreshToken) {
    payload.refresh = refreshToken;
  }
  return api.post('logout/', payload, { withCredentials: true });
};
export const fetchUserRole = async () => {
  const res = await api.get('profile/');
  return res.data.role;
};
