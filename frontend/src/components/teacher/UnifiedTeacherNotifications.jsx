import React, { useState, useEffect, useCallback } from 'react';
import { Badge, Dropdown, Card, Button, Spinner, Alert } from 'react-bootstrap';
import { BellFill, Clock, CheckCircle, XCircle, CurrencyExchange } from 'react-bootstrap-icons';
import axiosClient from '../../services/core/axiosClient';
import { formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

const UnifiedTeacherNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState({});

  // Parse notification message to extract discount data
  const parseDiscountNotification = (notification) => {
    try {
      const message = notification.message;
      
      // Extract data from notification message using regex
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

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all unread notifications
      const response = await axiosClient.get('/notifications/', {
        params: {
          read: 'false', // Only unread notifications
          limit: 50
        }
      });
      
      if (response.data && Array.isArray(response.data)) {
        // Process notifications and add parsed data
        const processedNotifications = response.data.map((notification) => ({
          ...notification,
          parsed: notification.notification_type === 'teocoin_discount_pending' ? parseDiscountNotification(notification) : { type: 'regular' }
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
  }, []);

  useEffect(() => {
    fetchNotifications();
    // Refresh every 30 seconds for real-time notifications
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = async (notificationId) => {
    try {
      await axiosClient.patch(`/notifications/${notificationId}/read/`);
      
      // Remove from local state
  setNotifications((prev) => prev.filter((notification) => notification.id !== notificationId));
      
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
      setProcessing(prev => ({ ...prev, [notificationId]: true }));

      if (choice === 'teo') {
        const msg = notification.message || '';
        const totalRe = /=\s*([\d.,]+)\s*TEO\s*total/i;
        const partsRe = /Accept\s+TEO:\s*([\d.,]+)\s*TEO\s*\+\s*([\d.,]+)\s*bonus/i;

        let amountTotal = null;
        // 1) payload strutturato se presente
        const p = notification.payload || notification.data || {};
        if (p.amount_total) amountTotal = parseFloat(String(p.amount_total).replace(',', '.'));
        if ((!amountTotal || !isFinite(amountTotal)) && p.amount && p.bonus) {
          amountTotal = parseFloat(String(p.amount).replace(',', '.')) + parseFloat(String(p.bonus).replace(',', '.'));
        }
        // 2) dal testo
        if (!amountTotal || !isFinite(amountTotal)) {
          const mt = msg.match(totalRe);
          if (mt && mt[1]) amountTotal = parseFloat(mt[1].replace(',', '.'));
        }
        if (!amountTotal || !isFinite(amountTotal)) {
          const mp = msg.match(partsRe);
          if (mp && mp[1] && mp[2]) {
            const used = parseFloat(mp[1].replace(',', '.'));
            const bonus = parseFloat(mp[2].replace(',', '.'));
            amountTotal = (isFinite(used) ? used : 0) + (isFinite(bonus) ? bonus : 0);
          }
        }
        if (!amountTotal || !isFinite(amountTotal) || amountTotal <= 0) {
          throw new Error('Importo TEO non disponibile nella notifica');
        }

        const resp = await axiosClient.post('/teocoin/teacher/choice/', {
          absorption_id: notificationId,
          choice: 'teo',
          amount_total: amountTotal,
          transaction_type: 'discount_absorption',
          description: `Discount absorption - total ${amountTotal} TEO`
        });
        if (!resp.data?.success) throw new Error(resp.data?.error || 'Operazione non riuscita');

        if (window.showToast) window.showToast(`Accreditati ${amountTotal} TEO`, 'success');
        // marca read SOLO dopo successo
        await markAsRead(notificationId);
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        return;
      }

      // EUR
      await axiosClient.post('/teocoin/teacher/choice/', {
        absorption_id: notificationId,
        choice: 'eur',
        amount_total: 0,
        transaction_type: 'discount_declined',
        description: 'EUR commission chosen'
      });
      await markAsRead(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      if (window.showToast) window.showToast('Scelta EUR confermata', 'success');

    } catch (err) {
      console.error('Error handling discount choice:', err);
      if (window.showToast) window.showToast('Errore: ' + err.message, 'error');
    } finally {
      setProcessing(prev => ({ ...prev, [notificationId]: false }));
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
      return 'Scadenza non disponibile';
    }
  };

  const getNotificationIcon = (notification) => {
    if (notification.notification_type === 'teocoin_discount_pending') {
      return <CurrencyExchange size={16} className="text-warning me-2" />;
    }
    return <BellFill size={16} className="text-primary me-2" />;
  };

  const renderDiscountNotification = (notification) => {
    const { parsed } = notification;
    const isProcessing = processing[notification.id];
    
    return (
      <Card className="border-0 border-bottom">
        <Card.Body className="p-3">
          <div className="d-flex justify-content-between align-items-start mb-2">
            <div>
              <strong className="text-warning">🪙 Decisione TeoCoin Sconto</strong>
              <br />
              <small className="text-muted">
                Corso: {parsed.course_title}
              </small>
              <br />
              <small className="text-muted">
                Studente: {parsed.student}
              </small>
            </div>
            <Badge 
              bg={parsed.hours_remaining > 2 ? "success" : "warning"}
              className="ms-2"
            >
              <Clock size={12} className="me-1" />
              {formatTimeRemaining(parsed.expires_at)}
            </Badge>
          </div>

          <div className="mb-3">
            <div className="d-flex justify-content-between text-sm">
              <span>Sconto applicato:</span>
              <span className="text-warning">-{parsed.discount_percent}%</span>
            </div>
          </div>

          <Alert variant="info" className="py-2 mb-3">
            <small>
              <strong>Messaggio:</strong> {notification.message}
            </small>
          </Alert>

          <div className="d-grid gap-2 d-md-flex justify-content-md-end">
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => handleDiscountChoice(notification, 'eur')}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <Spinner size="sm" animation="border" />
              ) : (
                <>
                  <XCircle className="me-1" size={14} />
                  EUR
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
                  TEO
                </>
              )}
            </Button>
          </div>
        </Card.Body>
      </Card>
    );
  };

  const renderRegularNotification = (notification) => {
    return (
      <Card className="border-0 border-bottom">
        <Card.Body className="p-3">
          <div className="d-flex justify-content-between align-items-start">
            <div className="flex-grow-1">
              {getNotificationIcon(notification)}
              <span className="text-sm">{notification.message}</span>
            </div>
            <Button
              variant="link"
              size="sm"
              className="text-muted p-0"
              onClick={() => markAsRead(notification.id)}
              title="Marca come letta"
            >
              <CheckCircle size={16} />
            </Button>
          </div>
          <div className="text-muted text-xs mt-1">
            {formatDistanceToNow(new Date(notification.created_at), { 
              addSuffix: true, 
              locale: it 
            })}
          </div>
        </Card.Body>
      </Card>
    );
  };

  const unreadCount = notifications.length;

  return (
    <Dropdown align="end">
      <Dropdown.Toggle
        variant="link"
        className="nav-link position-relative p-2"
        style={{ border: 'none', background: 'none', boxShadow: 'none' }}
      >
        <BellFill size={20} className="text-primary" />
        {unreadCount > 0 && (
          <Badge 
            bg="danger" 
            pill 
            className="position-absolute top-0 start-100 translate-middle"
            style={{ fontSize: '0.7rem' }}
          >
            {unreadCount}
          </Badge>
        )}
      </Dropdown.Toggle>

      <Dropdown.Menu 
        className="dropdown-menu-end" 
        style={{ width: '400px', maxHeight: '500px', overflowY: 'auto' }}
      >
        <Dropdown.Header>
          <div className="d-flex justify-content-between align-items-center">
            <span>🔔 Notifiche Teacher</span>
            {loading && <Spinner size="sm" animation="border" />}
          </div>
        </Dropdown.Header>

        {error && (
          <div className="dropdown-item-text text-danger p-3">
            <small>⚠️ {error}</small>
          </div>
        )}

        {!loading && unreadCount === 0 && (
          <div className="dropdown-item-text text-muted p-3 text-center">
            <BellFill className="mb-2" size={32} style={{ opacity: 0.5 }} />
            <br />
            <small>Nessuna notifica non letta</small>
          </div>
        )}

        {notifications.map((notification) => (
          <div key={notification.id} className="dropdown-item-text p-0">
            {notification.parsed.type === 'discount_decision' 
              ? renderDiscountNotification(notification)
              : renderRegularNotification(notification)
            }
          </div>
        ))}

        {unreadCount > 0 && (
          <Dropdown.Item 
            className="text-center text-primary"
            onClick={fetchNotifications}
          >
            🔄 Aggiorna notifiche
          </Dropdown.Item>
        )}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default UnifiedTeacherNotifications;
