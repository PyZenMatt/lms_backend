import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

// Notification types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  // Generate unique ID for notifications
  const generateId = () => {
    return Date.now() + Math.random().toString(36).substr(2, 9);
  };

  // Show notification
  const showNotification = useCallback((message, type = NOTIFICATION_TYPES.INFO, duration = 5000, options = {}) => {
    const id = generateId();
    
    const notification = {
      id,
      message,
      type,
      timestamp: Date.now(),
      duration,
      ...options
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification after duration (unless persistent)
    if (duration > 0 && !options.persistent) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }

    return id;
  }, []);

  // Remove notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Convenience methods for different notification types
  const showSuccess = useCallback((message, duration = 4000, options = {}) => {
    return showNotification(message, NOTIFICATION_TYPES.SUCCESS, duration, options);
  }, [showNotification]);

  const showError = useCallback((message, duration = 6000, options = {}) => {
    return showNotification(message, NOTIFICATION_TYPES.ERROR, duration, options);
  }, [showNotification]);

  const showWarning = useCallback((message, duration = 5000, options = {}) => {
    return showNotification(message, NOTIFICATION_TYPES.WARNING, duration, options);
  }, [showNotification]);

  const showInfo = useCallback((message, duration = 4000, options = {}) => {
    return showNotification(message, NOTIFICATION_TYPES.INFO, duration, options);
  }, [showNotification]);

  // Show transaction notifications with special handling
  const showTransactionNotification = useCallback((txHash, type = 'pending', message = '') => {
    const baseMessage = message || 'Transaction submitted';
    const explorerUrl = `https://amoy.polygonscan.com/tx/${txHash}`;
    
    const notificationMessage = (
      <div>
        <div>{baseMessage}</div>
        <div style={{ fontSize: '0.8em', marginTop: '4px' }}>
          <a 
            href={explorerUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: 'inherit', textDecoration: 'underline' }}
          >
            View on PolygonScan
          </a>
        </div>
      </div>
    );

    if (type === 'pending') {
      return showNotification(
        notificationMessage,
        NOTIFICATION_TYPES.INFO,
        0, // Persistent until updated
        { 
          persistent: true,
          txHash,
          transactionId: txHash // For updating later
        }
      );
    } else if (type === 'success') {
      return showSuccess(notificationMessage, 6000, { txHash });
    } else if (type === 'error') {
      return showError(notificationMessage, 8000, { txHash });
    }
  }, [showNotification, showSuccess, showError]);

  // Update existing transaction notification
  const updateTransactionNotification = useCallback((txHash, status, newMessage = '') => {
    setNotifications(prev => {
      return prev.map(notification => {
        if (notification.txHash === txHash || notification.transactionId === txHash) {
          let updatedType = notification.type;
          let updatedMessage = notification.message;
          let updatedDuration = notification.duration;

          if (status === 'success') {
            updatedType = NOTIFICATION_TYPES.SUCCESS;
            updatedMessage = newMessage || 'Transaction confirmed!';
            updatedDuration = 6000;
          } else if (status === 'error') {
            updatedType = NOTIFICATION_TYPES.ERROR;
            updatedMessage = newMessage || 'Transaction failed!';
            updatedDuration = 8000;
          }

          return {
            ...notification,
            type: updatedType,
            message: updatedMessage,
            duration: updatedDuration,
            persistent: false
          };
        }
        return notification;
      });
    });
  }, []);

  const value = {
    notifications,
    showNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showTransactionNotification,
    updateTransactionNotification,
    NOTIFICATION_TYPES
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
