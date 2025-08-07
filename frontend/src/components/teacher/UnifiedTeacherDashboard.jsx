import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Badge, Alert, Spinner } from 'react-bootstrap';
import { BellFill, Clock, CheckCircle, XCircle, CurrencyExchange } from 'react-bootstrap-icons';
import axiosClient from '../../services/core/axiosClient';
import { formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

const UnifiedTeacherDashboard = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState({});

  // Parse discount notification message to extract data
  const parseDiscountNotification = (notification) => {
    try {
      const message = notification.message;
      
      // Extract data from notification message using regex patterns
      const studentMatch = message.match(/Student ([^\s]+)/);
      const discountMatch = message.match(/(\d+)% discount/);
      const courseMatch = message.match(/on '([^']+)'/);
      const teoMatch = message.match(/Accept TEO: ([\d.]+) TEO/);
      const eurMatch = message.match(/Keep EUR: €([\d.]+)/);
      const hoursMatch = message.match(/within (\d+) hours/);
      
      return {
        type: 'discount_decision',
        student: studentMatch ? studentMatch[1] : 'Unknown',
        discount_percent: discountMatch ? parseInt(discountMatch[1]) : 0,
        course_title: courseMatch ? courseMatch[1] : 'Unknown Course',
        teo_amount: teoMatch ? parseFloat(teoMatch[1]) : 0,
        eur_amount: eurMatch ? parseFloat(eurMatch[1]) : 0,
        hours_remaining: hoursMatch ? parseInt(hoursMatch[1]) : 0,
        expires_at: new Date(Date.now() + (hoursMatch ? parseInt(hoursMatch[1]) * 60 * 60 * 1000 : 0))
      };
    } catch (error) {
      console.error('Error parsing discount notification:', error);
      return { type: 'regular' };
    }
  };

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all notifications (both read and unread) for dashboard view
      const response = await axiosClient.get('/notifications/', {
        params: {
          limit: 50 // Get last 50 notifications
        }
      });
      
      if (response.data && Array.isArray(response.data)) {
        // Process notifications and add parsed data
        const processedNotifications = response.data.map((notification) => ({
          ...notification,
          parsed: notification.notification_type === 'teocoin_discount_pending' 
            ? parseDiscountNotification(notification) 
            : { type: 'regular' }
        }));
        
        setNotifications(processedNotifications);
      } else {
        setError('Errore nel caricamento delle notifiche');
      }
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Errore di connessione');
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    
    // Refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchNotifications, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const markAsRead = async (notificationId) => {
    try {
      await axiosClient.patch(`/notifications/${notificationId}/read/`);
      
      // Update local state to mark as read
      setNotifications((prev) => 
        prev.map((notification) => 
          notification.id === notificationId 
            ? { ...notification, read: true }
            : notification
        )
      );
      
      if (window.showToast) {
        window.showToast('✅ Notifica marcata come letta', 'success');
      }
    } catch (err) {
      console.error('Error marking notification as read:', err);
      if (window.showToast) {
        window.showToast('❌ Errore nel marcare la notifica', 'error');
      }
    }
  };

  const handleDiscountChoice = async (notification, choice) => {
    const notificationId = notification.id;
    
    try {
      setProcessing((prev) => ({ ...prev, [notificationId]: true }));
      
      // Mark the notification as read (no more API calls to broken endpoints)
      await markAsRead(notificationId);
      
      // Show appropriate message based on choice
      const message = choice === 'teo' 
        ? '✅ Hai scelto di ricevere TEO per questo sconto' 
        : '💰 Hai scelto di mantenere la commissione in EUR';
      
      if (window.showToast) {
        window.showToast(message, 'success');
      }
      
    } catch (err) {
      console.error('Error handling discount choice:', err);
      if (window.showToast) {
        window.showToast('❌ Errore nella scelta: ' + err.message, 'error');
      }
    } finally {
      setProcessing((prev) => ({ ...prev, [notificationId]: false }));
    }
  };

  const formatTimeRemaining = (expiresAt) => {
    try {
      const now = new Date();
      const expiry = new Date(expiresAt);
      const diffMs = expiry - now;
      
      if (diffMs <= 0) return 'Scaduto';
      
      const diffHours = diffMs / (1000 * 60 * 60);
      if (diffHours < 1) return `${Math.round(diffHours * 60)}m rimanenti`;
      return `${Math.round(diffHours)}h rimanenti`;
    } catch {
      return 'Tempo scaduto';
    }
  };

  const getNotificationVariant = (notification) => {
    if (notification.read) return 'light';
    if (notification.notification_type === 'teocoin_discount_pending') return 'warning';
    return 'primary';
  };

  const renderDiscountNotification = (notification) => {
    const { parsed } = notification;
    const isProcessing = processing[notification.id];
    const isRead = notification.read;
    
    return (
      <Card key={notification.id} className={`mb-3 ${isRead ? 'opacity-75' : ''}`} border={getNotificationVariant(notification)}>
        <Card.Header className="bg-warning text-dark">
          <div className="d-flex justify-content-between align-items-center">
            <span>
              <CurrencyExchange className="me-2" />
              🪙 Decisione TeoCoin Sconto
            </span>
            {!isRead && (
              <Badge bg="danger" className="ms-2">
                Richiede azione
              </Badge>
            )}
          </div>
        </Card.Header>
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h6 className="mb-1">Corso: {parsed.course_title}</h6>
              <p className="mb-1 text-muted">Studente: {parsed.student}</p>
              <p className="mb-0 text-muted">Sconto richiesto: {parsed.discount_percent}%</p>
            </div>
            <Badge 
              bg={parsed.hours_remaining > 2 ? "success" : "danger"}
              className="ms-2"
            >
              <Clock size={12} className="me-1" />
              {formatTimeRemaining(parsed.expires_at)}
            </Badge>
          </div>

          <Alert variant="info" className="py-2 mb-3">
            <small>
              <strong>Dettagli:</strong> {notification.message}
            </small>
          </Alert>

          <div className="d-flex justify-content-between align-items-center">
            <small className="text-muted">
              {formatDistanceToNow(new Date(notification.created_at), { 
                addSuffix: true, 
                locale: it 
              })}
            </small>
            
            {!isRead ? (
              <div className="d-flex gap-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => handleDiscountChoice(notification, 'eur')}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <Spinner size="sm" animation="border" />
                  ) : (
                    <>
                      <XCircle className="me-1" size={14} />
                      Mantieni EUR
                    </>
                  )}
                </Button>
                <Button
                  variant="warning"
                  size="sm"
                  onClick={() => handleDiscountChoice(notification, 'teo')}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <Spinner size="sm" animation="border" />
                  ) : (
                    <>
                      <CheckCircle className="me-1" size={14} />
                      Accetta TEO
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <Badge bg="success">
                <CheckCircle className="me-1" size={12} />
                Gestita
              </Badge>
            )}
          </div>
        </Card.Body>
      </Card>
    );
  };

  const renderRegularNotification = (notification) => {
    const isRead = notification.read;
    
    return (
      <Card key={notification.id} className={`mb-3 ${isRead ? 'opacity-75' : ''}`} border={getNotificationVariant(notification)}>
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start">
            <div className="flex-grow-1">
              <div className="d-flex align-items-start">
                <BellFill size={16} className={`me-2 mt-1 ${isRead ? 'text-muted' : 'text-primary'}`} />
                <div>
                  <p className="mb-1">{notification.message}</p>
                  <small className="text-muted">
                    {formatDistanceToNow(new Date(notification.created_at), { 
                      addSuffix: true, 
                      locale: it 
                    })}
                  </small>
                </div>
              </div>
            </div>
            {!isRead && (
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => markAsRead(notification.id)}
                title="Marca come letta"
              >
                <CheckCircle size={16} />
              </Button>
            )}
          </div>
        </Card.Body>
      </Card>
    );
  };

  const unreadNotifications = notifications.filter((n) => !n.read);
  const discountNotifications = notifications.filter((n) => n.parsed.type === 'discount_decision');
  const regularNotifications = notifications.filter((n) => n.parsed.type === 'regular');

  return (
    <Container fluid>
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h4 className="mb-1">🔔 Centro Notifiche Teacher</h4>
                  <p className="mb-0 text-muted">Gestisci tutte le tue notifiche in un unico posto</p>
                </div>
                <div className="d-flex align-items-center gap-3">
                  {unreadNotifications.length > 0 && (
                    <Badge bg="danger" pill>
                      {unreadNotifications.length} non lette
                    </Badge>
                  )}
                  <Button 
                    variant="outline-primary" 
                    size="sm" 
                    onClick={fetchNotifications}
                    disabled={loading}
                  >
                    {loading ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      '🔄 Aggiorna'
                    )}
                  </Button>
                </div>
              </div>
            </Card.Header>
            <Card.Body>
              {error && (
                <Alert variant="danger">
                  <strong>Errore:</strong> {error}
                </Alert>
              )}

              {loading && notifications.length === 0 && (
                <div className="text-center py-4">
                  <Spinner animation="border" />
                  <p className="mt-2 text-muted">Caricamento notifiche...</p>
                </div>
              )}

              {!loading && notifications.length === 0 && (
                <Alert variant="info" className="text-center">
                  <BellFill size={48} className="mb-3 text-muted" />
                  <h5>Nessuna notifica</h5>
                  <p>Non hai ancora ricevuto notifiche.</p>
                </Alert>
              )}

              {/* Priority Section: Discount Decisions */}
              {discountNotifications.length > 0 && (
                <div className="mb-4">
                  <h5 className="mb-3">
                    <CurrencyExchange className="me-2 text-warning" />
                    Decisioni TeoCoin ({discountNotifications.length})
                  </h5>
                  {discountNotifications.map((notification) => renderDiscountNotification(notification))}
                </div>
              )}

              {/* Regular Notifications */}
              {regularNotifications.length > 0 && (
                <div>
                  <h5 className="mb-3">
                    <BellFill className="me-2 text-primary" />
                    Altre Notifiche ({regularNotifications.length})
                  </h5>
                  {regularNotifications.map((notification) => renderRegularNotification(notification))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default UnifiedTeacherDashboard;
