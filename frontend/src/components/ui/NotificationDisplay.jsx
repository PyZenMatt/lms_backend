import React from 'react';
import { useNotification, NOTIFICATION_TYPES } from '../../contexts/NotificationContext';
import './NotificationDisplay.css';

const NotificationDisplay = () => {
  const { notifications, removeNotification } = useNotification();

  if (notifications.length === 0) {
    return null;
  }

  const getNotificationClass = (type) => {
    switch (type) {
      case NOTIFICATION_TYPES.SUCCESS:
        return 'notification-success';
      case NOTIFICATION_TYPES.ERROR:
        return 'notification-error';
      case NOTIFICATION_TYPES.WARNING:
        return 'notification-warning';
      case NOTIFICATION_TYPES.INFO:
      default:
        return 'notification-info';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case NOTIFICATION_TYPES.SUCCESS:
        return '✓';
      case NOTIFICATION_TYPES.ERROR:
        return '✕';
      case NOTIFICATION_TYPES.WARNING:
        return '⚠';
      case NOTIFICATION_TYPES.INFO:
      default:
        return 'ℹ';
    }
  };

  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification ${getNotificationClass(notification.type)}`}
          onClick={() => removeNotification(notification.id)}
        >
          <div className="notification-content">
            <span className="notification-icon">
              {getIcon(notification.type)}
            </span>
            <div className="notification-message">
              {typeof notification.message === 'string' ? (
                <span>{notification.message}</span>
              ) : (
                notification.message
              )}
            </div>
            <button 
              className="notification-close"
              onClick={(e) => {
                e.stopPropagation();
                removeNotification(notification.id);
              }}
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationDisplay;
