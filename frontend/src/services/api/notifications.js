import api from '../core/axiosClient';

export const fetchUserNotifications = async () => {
  try {
    const response = await api.get('notifications/');
    return response.data;
  } catch (error) {
    console.error('Error fetching notifications:', error);
    throw error;
  }
};

export const markNotificationRead = async (id) => {
  try {
    const response = await api.patch(`notifications/${id}/read/`, { read: true });
    return response.data;
  } catch (error) {
    console.error(`Error marking notification ${id} as read:`, error);
    throw error;
  }
};

export const markAllNotificationsRead = async () => {
  try {
    const response = await api.post('notifications/mark-all-read/');
    return response.data;
  } catch (error) {
    console.error('Error marking all notifications as read:', error);
    throw error;
  }
};

export const clearAllNotifications = async () => {
  try {
    const response = await api.delete('notifications/clear-all/');
    return response.data;
  } catch (error) {
    console.error('Error clearing all notifications:', error);
    throw error;
  }
};

export const deleteNotification = async (id) => {
  try {
    const response = await api.delete(`notifications/${id}/`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting notification ${id}:`, error);
    throw error;
  }
};
