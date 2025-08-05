import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, Badge, Button, Row, Col, Nav, Spinner } from 'react-bootstrap';
import { fetchUserNotifications, markNotificationRead, markAllNotificationsRead, clearAllNotifications, deleteNotification } from '../../services/api/notifications';
import MainCard from '../../components/Card/MainCard';

const NotificationListNew = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, unread, read
  const [error, setError] = useState('');

  // Real API call to fetch notifications
  useEffect(() => {
    const loadNotifications = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await fetchUserNotifications();
        const apiNotifications = response.map(notification => ({
          id: notification.id,
          type: getNotificationType(notification.notification_type),
          title: getNotificationTitle(notification.notification_type),
          message: notification.message,
          timestamp: new Date(notification.created_at),
          read: notification.read,
          icon: getNotificationIcon(notification.notification_type),
          color: getNotificationColor(notification.notification_type),
          link: notification.link
        }));
        setNotifications(apiNotifications);
      } catch (err) {
        console.error('Error loading notifications:', err);
        setError('Errore nel caricamento delle notifiche');
        // Fallback to empty array
        setNotifications([]);
      } finally {
        setLoading(false);
      }
    };

    loadNotifications();
  }, []);

  // Helper functions to map API data to UI format
  const getNotificationType = (type) => {
    const typeMap = {
      'teocoins_earned': 'reward',
      'teocoins_spent': 'reward', 
      'reward_earned': 'reward',
      'bonus_received': 'reward',
      'course_approved': 'course',
      'course_rejected': 'course',
      'lesson_approved': 'lesson',
      'lesson_rejected': 'lesson',
      'review_assigned': 'review',
      'review_completed': 'review',
      'teacher_approved': 'teacher',
      'teacher_rejected': 'teacher',
      'exercise_submitted': 'exercise',
      'exercise_graded': 'exercise',
      'new_comment': 'comment',
      'new_course': 'course',
      'new_lesson': 'lesson'
    };
    return typeMap[type] || 'system';
  };

  const getNotificationTitle = (type) => {
    const titleMap = {
      'teocoins_earned': 'TeoCoin Guadagnati',
      'teocoins_spent': 'TeoCoin Spesi',
      'reward_earned': 'Premio Ottenuto',
      'bonus_received': 'Bonus Ricevuto',
      'course_approved': 'Corso Approvato',
      'course_rejected': 'Corso Rifiutato',
      'lesson_approved': 'Lezione Approvata',
      'lesson_rejected': 'Lezione Rifiutata',
      'review_assigned': 'Nuova Revisione',
      'review_completed': 'Revisione Completata',
      'teacher_approved': 'Stato Teacher Approvato',
      'teacher_rejected': 'Stato Teacher Rifiutato',
      'exercise_submitted': 'Esercizio Inviato',
      'exercise_graded': 'Esercizio Valutato',
      'new_comment': 'Nuovo Commento',
      'new_course': 'Nuovo Corso',
      'new_lesson': 'Nuova Lezione'
    };
    return titleMap[type] || 'Notifica Sistema';
  };

  const getNotificationIcon = (type) => {
    const iconMap = {
      'teocoins_earned': 'icon-dollar-sign',
      'teocoins_spent': 'icon-shopping-cart',
      'reward_earned': 'icon-award',
      'bonus_received': 'icon-gift',
      'course_approved': 'icon-check-circle',
      'course_rejected': 'icon-x-circle',
      'lesson_approved': 'icon-check-circle',
      'lesson_rejected': 'icon-x-circle',
      'review_assigned': 'icon-clipboard',
      'review_completed': 'icon-clipboard',
      'teacher_approved': 'icon-user-check',
      'teacher_rejected': 'icon-user-x',
      'exercise_submitted': 'icon-file-text',
      'exercise_graded': 'icon-star',
      'new_comment': 'icon-message-circle',
      'new_course': 'icon-book',
      'new_lesson': 'icon-file-text'
    };
    return `feather ${iconMap[type] || 'icon-bell'}`;
  };

  const getNotificationColor = (type) => {
    const typeCategory = getNotificationType(type);
    const colorMap = {
      'reward': 'success',
      'course': 'primary',
      'lesson': 'info',
      'review': 'warning',
      'teacher': 'secondary',
      'exercise': 'info',
      'comment': 'dark',
      'system': 'light'
    };
    return colorMap[typeCategory] || 'primary';
  };

  // Handlers for notification actions
  const handleMarkAsRead = async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      setNotifications(
        notifications.map(notif => 
          notif.id === notificationId ? { ...notif, read: true } : notif
        )
      );
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(
        notifications.map(notif => ({ ...notif, read: true }))
      );
    } catch (err) {
      console.error('Error marking all notifications as read:', err);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllNotifications();
      setNotifications([]);
    } catch (err) {
      console.error('Error clearing all notifications:', err);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await deleteNotification(notificationId);
      setNotifications(notifications.filter(notif => notif.id !== notificationId));
    } catch (err) {
      console.error('Error deleting notification:', err);
    }
  };

  // Format timestamp to readable string
  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    
    if (months > 0) {
      return `${months} ${months === 1 ? 'mese' : 'mesi'} fa`;
    }
    if (days > 0) {
      return `${days} ${days === 1 ? 'giorno' : 'giorni'} fa`;
    }
    if (hours > 0) {
      return `${hours} ${hours === 1 ? 'ora' : 'ore'} fa`;
    }
    if (minutes > 0) {
      return `${minutes} ${minutes === 1 ? 'minuto' : 'minuti'} fa`;
    }
    return 'Poco fa';
  };

  // Check if we have unread notifications
  const hasUnreadNotifications = notifications.some(notif => !notif.read);

  // Apply filter
  const filteredNotifications = notifications.filter(notif => {
    if (filter === 'unread') return !notif.read;
    if (filter === 'read') return notif.read;
    return true;
  });

  const unreadCount = notifications.filter(notif => !notif.read).length;

  if (loading) {
    return (
      <div className="card">
        <div className="card-body text-center py-5">
          <div className="spinner-border text-primary" role="status"></div>
          <p className="mt-3 text-muted">Caricamento notifiche...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header Card */}
      <Card className="mb-4">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="feather icon-bell me-2"></i>
              Le tue notifiche
            </h5>
            <div className="d-flex align-items-center">
              {unreadCount > 0 && (
                <span className="badge bg-primary me-3">
                  {unreadCount} non lette
                </span>
              )}
            </div>
          </div>
        </Card.Header>
      </Card>

      {/* Navigation Tabs */}
      <Card className="mb-4">
        <Card.Body>
          <Nav variant="pills" className="mb-4">
            <Nav.Item>
              <Link to="/profile" className="nav-link">
                <i className="feather icon-user me-1"></i>
                Profilo
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="/profile/notifications" className="nav-link active">
                <i className="feather icon-bell me-1"></i>
                Notifiche
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="/profile/settings" className="nav-link">
                <i className="feather icon-settings me-1"></i>
                Impostazioni
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="/profile/progress" className="nav-link">
                <i className="feather icon-trending-up me-1"></i>
                Progressi
              </Link>
            </Nav.Item>
          </Nav>
        </Card.Body>
      </Card>

      {/* Notifications Card */}
      <Card>
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <div className="btn-group">
              <Button 
                variant={filter === 'all' ? 'primary' : 'outline-primary'} 
                onClick={() => setFilter('all')}
              >
                Tutte
              </Button>
              <Button 
                variant={filter === 'unread' ? 'primary' : 'outline-primary'} 
                onClick={() => setFilter('unread')}
              >
                Non lette
              </Button>
              <Button 
                variant={filter === 'read' ? 'primary' : 'outline-primary'} 
                onClick={() => setFilter('read')}
              >
                Lette
              </Button>
            </div>
            
            <div>
              <Button 
                variant="light" 
                size="sm" 
                className="me-2" 
                onClick={handleMarkAllRead}
                disabled={!hasUnreadNotifications}
              >
                <i className="feather icon-check-circle me-1"></i>
                Segna tutte lette
              </Button>
              <Button 
                variant="light" 
                size="sm" 
                onClick={handleClearAll}
                disabled={notifications.length === 0}
              >
                <i className="feather icon-trash-2 me-1"></i>
                Cancella tutte
              </Button>
            </div>
          </div>
        </Card.Header>
        <Card.Body>
          {error && (
            <div className="alert alert-danger" role="alert">
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </div>
          )}
          
          {filteredNotifications.length === 0 ? (
            <div className="text-center py-5">
              <i className="feather icon-bell-off" style={{fontSize: '3rem', opacity: 0.3}}></i>
              <p className="mt-3 text-muted">
                {filter === 'all' 
                  ? 'Non hai ancora ricevuto notifiche' 
                  : filter === 'unread' 
                    ? 'Non hai notifiche non lette' 
                    : 'Non hai notifiche già lette'}
              </p>
            </div>
          ) : (
            <div className="list-group">
              {filteredNotifications.map((notification) => (
                <div 
                  key={notification.id} 
                  className={`list-group-item list-group-item-action ${!notification.read ? 'bg-light' : ''}`}
                >
                  <Row className="align-items-center">
                    <Col xs={1} className="text-center">
                      <div className={`text-${notification.color}`}>
                        <i className={notification.icon} style={{fontSize: '1.5rem'}}></i>
                      </div>
                    </Col>
                    <Col xs={9}>
                      <div className="d-flex w-100 justify-content-between">
                        <h6 className="mb-1 fw-bold">{notification.title}</h6>
                        <small className="text-muted">{formatTimestamp(notification.timestamp)}</small>
                      </div>
                      <p className="mb-1">{notification.message}</p>
                    </Col>
                    <Col xs={2} className="text-end">
                      {!notification.read && (
                        <Button 
                          variant="outline-primary" 
                          size="sm" 
                          onClick={() => handleMarkAsRead(notification.id)}
                          className="me-1"
                        >
                          <i className="feather icon-check"></i>
                        </Button>
                      )}
                      <Button 
                        variant="outline-danger" 
                        size="sm" 
                        onClick={() => handleDeleteNotification(notification.id)}
                        className="me-1"
                      >
                        <i className="feather icon-trash-2"></i>
                      </Button>
                      {notification.link && (
                        <Link 
                          to={notification.link} 
                          className="btn btn-sm btn-light"
                        >
                          <i className="feather icon-external-link"></i>
                        </Link>
                      )}
                    </Col>
                  </Row>
                </div>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default NotificationListNew;
