/**
 * 🔥 PHASE 4: Enhanced Notification System
 * 
 * Extends the existing notification system with:
 * - Sound notifications
 * - Vibration support
 * - Progressive Web App features
 * - Advanced notification types
 */

import React, { useEffect, useState } from 'react';
import { Toast, ToastContainer, Badge, Button } from 'react-bootstrap';
import { useNotification, NOTIFICATION_TYPES } from '../../contexts/NotificationContext';
import './EnhancedNotificationSystem.css';

const EnhancedNotificationSystem = () => {
  const { notifications, removeNotification } = useNotification();
  const [notificationPermission, setNotificationPermission] = useState(Notification.permission);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [vibrationEnabled, setVibrationEnabled] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Update unread count
    const unread = notifications.filter(n => !n.read).length;
    setUnreadCount(unread);
    
    // Update document title with unread count
    if (unread > 0) {
      document.title = `(${unread}) SchoolPlatform`;
    } else {
      document.title = 'SchoolPlatform';
    }
  }, [notifications]);

  /**
   * Check if sound can be played
   */
  const canPlaySound = () => {
    return !document.hidden && 'Audio' in window && !isAudioMuted();
  };

  /**
   * Check if audio is muted
   */
  const isAudioMuted = () => {
    // Check if user has interacted with the page (required for autoplay)
    return !document.hasFocus() && !hasUserGesture();
  };

  /**
   * Check if user has made a gesture (required for audio autoplay)
   */
  const hasUserGesture = () => {
    return localStorage.getItem('userGesture') === 'true';
  };

  /**
   * Play notification sound based on type
   */
  const playNotificationSound = (type) => {
    try {
      const soundFile = getSoundFile(type);
      const audio = new Audio(soundFile);
      audio.volume = 0.4;
      audio.play().catch(e => {
        console.log('🔇 Sound play failed (user interaction required):', e.message);
      });
    } catch (error) {
      console.log('🔇 Sound not available:', error);
    }
  };

  /**
   * Get sound file for notification type
   */
  const getSoundFile = (type) => {
    const soundMap = {
      [NOTIFICATION_TYPES.SUCCESS]: '/sounds/success.mp3',
      [NOTIFICATION_TYPES.ERROR]: '/sounds/error.mp3',
      [NOTIFICATION_TYPES.WARNING]: '/sounds/warning.mp3',
      [NOTIFICATION_TYPES.INFO]: '/sounds/info.mp3'
    };
    
    return soundMap[type] || '/sounds/default.mp3';
  };

  /**
   * Get vibration pattern based on type
   */
  const getVibrationPattern = (type) => {
    const patterns = {
      [NOTIFICATION_TYPES.SUCCESS]: [200, 100, 200],
      [NOTIFICATION_TYPES.ERROR]: [300, 100, 300, 100, 300],
      [NOTIFICATION_TYPES.WARNING]: [100, 100, 100, 100, 100],
      [NOTIFICATION_TYPES.INFO]: [200]
    };
    
    return patterns[type] || [200];
  };

  /**
   * Check if browser notifications are available
   */
  const canShowBrowserNotification = () => {
    return 'Notification' in window && notificationPermission === 'granted';
  };

  /**
   * Show browser notification
   */
  const showBrowserNotification = (message, type, actions = []) => {
    if (!canShowBrowserNotification()) return;

    const options = {
      body: message,
      icon: getNotificationIcon(type),
      badge: '/badge-96x96.png',
      tag: 'schoolplatform-notification',
      requireInteraction: type === NOTIFICATION_TYPES.ERROR,
      silent: false,
      vibrate: getVibrationPattern(type),
      data: { type, actions }
    };

    const notification = new Notification('SchoolPlatform', options);

    // Handle notification clicks
    notification.onclick = () => {
      window.focus();
      notification.close();
      
      // Execute first action if available
      if (actions.length > 0 && actions[0].action) {
        actions[0].action();
      }
    };

    // Auto-close after duration
    setTimeout(() => {
      notification.close();
    }, type === NOTIFICATION_TYPES.ERROR ? 10000 : 5000);
  };

  /**
   * Get notification icon based on type
   */
  const getNotificationIcon = (type) => {
    const iconMap = {
      [NOTIFICATION_TYPES.SUCCESS]: '/icons/success.png',
      [NOTIFICATION_TYPES.ERROR]: '/icons/error.png',
      [NOTIFICATION_TYPES.WARNING]: '/icons/warning.png',
      [NOTIFICATION_TYPES.INFO]: '/icons/info.png'
    };
    
    return iconMap[type] || '/favicon.ico';
  };

  /**
   * Show toast notification
   */
  const showToastNotification = ({ message, type, priority, duration, actions }) => {
    // This integrates with the existing notification context
    // The enhanced features are handled here
  };

  /**
   * Request notification permission
   */
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
      
      if (permission === 'granted') {
        // Show a test notification
        new Notification('SchoolPlatform', {
          body: '🔔 Notifications enabled! You\'ll now receive real-time updates.',
          icon: '/favicon.ico'
        });
      }
      
      return permission === 'granted';
    }
    return false;
  };

  /**
   * Toggle sound notifications
   */
  const toggleSound = () => {
    setSoundEnabled(!soundEnabled);
    localStorage.setItem('notificationSound', (!soundEnabled).toString());
    
    if (!soundEnabled) {
      // Play test sound
      playNotificationSound(NOTIFICATION_TYPES.SUCCESS);
    }
  };

  /**
   * Toggle vibration
   */
  const toggleVibration = () => {
    setVibrationEnabled(!vibrationEnabled);
    localStorage.setItem('notificationVibration', (!vibrationEnabled).toString());
    
    if (!vibrationEnabled && 'vibrate' in navigator) {
      navigator.vibrate([200, 100, 200]);
    }
  };

  /**
   * Clear all notifications
   */
  const clearAllNotifications = () => {
    notifications.forEach(notification => {
      removeNotification(notification.id);
    });
    setUnreadCount(0);
  };

  /**
   * Get notification variant class
   */
  const getNotificationVariant = (type, priority) => {
    if (priority === 'high') return 'danger';
    
    switch (type) {
      case NOTIFICATION_TYPES.SUCCESS:
        return 'success';
      case NOTIFICATION_TYPES.ERROR:
        return 'danger';
      case NOTIFICATION_TYPES.WARNING:
        return 'warning';
      case NOTIFICATION_TYPES.INFO:
      default:
        return 'info';
    }
  };

  /**
   * Get priority icon
   */
  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'high':
        return '🚨';
      case 'normal':
        return '📢';
      case 'low':
        return '💬';
      default:
        return '📢';
    }
  };

  return (
    <div className="enhanced-notification-system">
      {/* Notification Settings Panel */}
      <div className="notification-settings">
        <div className="d-flex align-items-center gap-3">
          {/* Unread Badge */}
          {unreadCount > 0 && (
            <Badge bg="danger" className="notification-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
          
          {/* Browser Notification Permission */}
          {notificationPermission !== 'granted' && (
            <Button
              variant="outline-primary"
              size="sm"
              onClick={requestNotificationPermission}
              className="permission-btn"
            >
              <i className="fas fa-bell me-1"></i>
              Enable Notifications
            </Button>
          )}
          
          {/* Sound Toggle */}
          <Button
            variant={soundEnabled ? 'success' : 'outline-secondary'}
            size="sm"
            onClick={toggleSound}
            title={soundEnabled ? 'Sound: ON' : 'Sound: OFF'}
          >
            <i className={`fas fa-volume-${soundEnabled ? 'up' : 'mute'}`}></i>
          </Button>
          
          {/* Vibration Toggle */}
          {('vibrate' in navigator) && (
            <Button
              variant={vibrationEnabled ? 'success' : 'outline-secondary'}
              size="sm"
              onClick={toggleVibration}
              title={vibrationEnabled ? 'Vibration: ON' : 'Vibration: OFF'}
            >
              <i className="fas fa-mobile-alt"></i>
            </Button>
          )}
          
          {/* Clear All */}
          {notifications.length > 0 && (
            <Button
              variant="outline-danger"
              size="sm"
              onClick={clearAllNotifications}
              title="Clear All Notifications"
            >
              <i className="fas fa-trash"></i>
            </Button>
          )}
        </div>
      </div>

      {/* Toast Container */}
      <ToastContainer 
        position="top-end" 
        className="enhanced-toast-container"
        style={{ zIndex: 9999 }}
      >
        {notifications.map((notification) => (
          <Toast
            key={notification.id}
            onClose={() => removeNotification(notification.id)}
            show={true}
            delay={notification.duration || 5000}
            autohide={!notification.persistent}
            className={`enhanced-toast enhanced-toast-${getNotificationVariant(notification.type, notification.priority)}`}
          >
            <Toast.Header>
              <div className="toast-icon">
                {getPriorityIcon(notification.priority)}
              </div>
              <strong className="me-auto">
                SchoolPlatform
                {notification.priority === 'high' && (
                  <Badge bg="danger" className="ms-2">URGENT</Badge>
                )}
              </strong>
              <small className="text-muted">
                {new Date(notification.timestamp).toLocaleTimeString()}
              </small>
            </Toast.Header>
            
            <Toast.Body>
              <div className="notification-content">
                {typeof notification.message === 'string' ? (
                  <span>{notification.message}</span>
                ) : (
                  notification.message
                )}
              </div>
              
              {/* Action Buttons */}
              {notification.actions && notification.actions.length > 0 && (
                <div className="notification-actions mt-2">
                  {notification.actions.map((action, index) => (
                    <Button
                      key={index}
                      variant="outline-primary"
                      size="sm"
                      onClick={() => {
                        action.action();
                        removeNotification(notification.id);
                      }}
                      className="me-2"
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              )}
            </Toast.Body>
          </Toast>
        ))}
      </ToastContainer>
    </div>
  );
};

// Enable user gesture tracking for sound
document.addEventListener('click', () => {
  localStorage.setItem('userGesture', 'true');
}, { once: true });

document.addEventListener('keydown', () => {
  localStorage.setItem('userGesture', 'true');
}, { once: true });

export default EnhancedNotificationSystem;
