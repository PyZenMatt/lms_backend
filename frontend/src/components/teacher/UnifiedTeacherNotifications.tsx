/* @ts-nocheck */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Badge,
  Card,
  CardContent,
  Button,
  Alert,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui';
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
        const processedNotifications = response.data.map((notification) => {
          const isPending = notification.notification_type === 'teocoin_discount_pending';
          return {
            ...notification,
            parsed: isPending ? parseDiscountNotification(notification) : { type: 'regular' }
          };
        });

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
      setProcessing((prev) => ({ ...prev, [notificationId]: true }));

      // Use absorption id from notification link when present
      const absorptionId = notification.related_object_id || notification.absorption_id || notificationId;

      // Minimal backend contract
      const resp = await axiosClient.post('/teocoin/teacher/choice/', {
        absorption_id: absorptionId,
        choice: choice === 'teo' ? 'teo' : 'eur'
      });

      if (!resp.data?.success) throw new Error(resp.data?.error || 'Operazione non riuscita');

      if (choice === 'teo') {
        const credited = resp.data?.absorption?.final_teacher_teo ?? notification.parsed?.teo_amount;
        if (window.showToast) window.showToast(`TEO accettati${credited ? `: ${credited} TEO` : ''}`, 'success');
      } else if (window.showToast) {
        window.showToast('Scelta EUR confermata', 'success');
      }

      await markAsRead(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
    } catch (err) {
      console.error('Error handling discount choice:', err);
      if (window.showToast) window.showToast('Errore: ' + err.message, 'error');
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
      return 'Scadenza non disponibile';
    }
  };

  const getNotificationIcon = (notification) => {
    if (notification.notification_type === 'teocoin_discount_pending') {
      return <CurrencyExchange size={16} className="text-warning me-2" />;
    }
    return <BellFill size={16} className="text-primary me-2" />;
  };

  const InlineSpinner = ({ size = 'sm' }) => (
    <svg
      role="status"
      aria-label="loading"
      className={
        size === 'sm'
          ? 'inline-block align-middle size-3 animate-spin text-current'
          : 'inline-block align-middle size-4 animate-spin text-current'
      }
      viewBox="0 0 50 50"
    >
      <circle cx="25" cy="25" r="20" fill="none" strokeWidth="5" stroke="currentColor" strokeOpacity="0.25" />
      <path d="M45 25a20 20 0 00-20-20" fill="none" strokeWidth="5" stroke="currentColor" />
    </svg>
  );

  const renderDiscountNotification = (notification) => {
    const { parsed } = notification;
    const isProcessing = processing[notification.id];

    return (
      <Card className="border-0 border-b">
        <CardContent className="p-3">
          <div className="d-flex justify-content-between align-items-start mb-2">
            <div>
              <strong className="text-warning">🪙 Decisione TeoCoin Sconto</strong>
              <br />
              <small className="text-muted">Corso: {parsed.course_title}</small>
              <br />
              <small className="text-muted">Studente: {parsed.student}</small>
            </div>
              <Badge bg={parsed.hours_remaining > 2 ? 'success' : 'warning'} className="ms-2">
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

          <div className="flex gap-2 justify-end">
            <Button variant="outline-primary" size="sm" onClick={() => handleDiscountChoice(notification, 'eur')} disabled={isProcessing}>
              {isProcessing ? (
                <InlineSpinner size="sm" />
              ) : (
                <>
                  <XCircle className="me-1" size={14} />
                  EUR
                </>
              )}
            </Button>
            <Button variant="warning" size="sm" onClick={() => handleDiscountChoice(notification, 'teo')} disabled={isProcessing}>
              {isProcessing ? (
                <InlineSpinner size="sm" />
              ) : (
                <>
                  <CheckCircle className="me-1" size={14} />
                  TEO
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderRegularNotification = (notification) => {
    return (
      <Card className="border-0 border-b">
        <CardContent className="p-3">
          <div className="flex justify-between items-start">
            <div className="flex-grow">
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
        </CardContent>
      </Card>
    );
  };
  const unreadCount = notifications.length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="nav-link relative p-2"
          style={{ border: 'none', background: 'none', boxShadow: 'none' }}
          aria-label="Notifiche"
        >
          <BellFill size={20} className="text-primary" />
          {unreadCount > 0 && (
            <Badge bg="danger" pill className="absolute top-0 right-0 translate-x-1/2 -translate-y-1/2 text-[0.7rem]">
              {unreadCount}
            </Badge>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent sideOffset={8} className="w-[400px] max-h-[500px] overflow-y-auto">
        <div className="px-3 py-2 flex justify-between items-center">
          <span>🔔 Notifiche Teacher</span>
          {loading && <InlineSpinner size="sm" />}
        </div>

        {error && (
          <div className="px-3 py-3 text-danger text-sm">
            <small>⚠️ {error}</small>
          </div>
        )}

        {!loading && unreadCount === 0 && (
          <div className="px-3 py-3 text-muted text-center">
            <BellFill className="mb-2" size={32} style={{ opacity: 0.5 }} />
            <br />
            <small>Nessuna notifica non letta</small>
          </div>
        )}

        <div>
          {notifications.map((notification) => (
            <div key={notification.id} className="p-0">
              {notification.parsed.type === 'discount_decision'
                ? renderDiscountNotification(notification)
                : renderRegularNotification(notification)}
            </div>
          ))}
        </div>

        {unreadCount > 0 && (
          <DropdownMenuItem className="text-center text-primary" onSelect={fetchNotifications}>
            🔄 Aggiorna notifiche
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UnifiedTeacherNotifications;
