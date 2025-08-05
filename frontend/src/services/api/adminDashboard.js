import api from '../core/axiosClient';

export const fetchAdminDashboard = async () => {
  return api.get('dashboard/admin/');
};
