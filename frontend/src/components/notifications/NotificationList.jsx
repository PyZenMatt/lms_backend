import React, { useState, useEffect } from 'react';
import { Card, ListGroup, Badge, Button, Alert, Spinner } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { fetchUserNotifications, markNotificationRead } from '../../services/api/notifications';
import TeacherDiscountChoiceModal from './TeacherDiscountChoiceModal';

/**
 * Enhanced Notification List Component
 * 
 * Displays all user notifications with special handling for TeoCoin discount notifications
 */
const NotificationList = () => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedAbsorption, setSelectedAbsorption] = useState(null);
    const [showModal, setShowModal] = useState(false);

    const fetchNotifications = async () => {
        setLoading(true);
        setError('');
        
        try {
            const data = await fetchUserNotifications();
            setNotifications(data.notifications || []);
        } catch (error) {
            console.error('Error fetching notifications:', error);
            setError('Failed to load notifications');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchNotifications();
            
            // Refresh every 30 seconds for real-time updates
            const interval = setInterval(fetchNotifications, 30000);
            return () => clearInterval(interval);
        }
    }, [user]);

    const handleNotificationClick = async (notification) => {
        // Mark as read
        if (!notification.read) {
            try {
                await markNotificationRead(notification.id);
                setNotifications(prev => 
                    prev.map(n => 
                        n.id === notification.id ? { ...n, read: true } : n
                    )
                );
            } catch (error) {
                console.error('Error marking notification as read:', error);
            }
        }

        // Handle special notification types
        if (notification.notification_type === 'teocoin_discount_pending' && notification.related_object_id) {
            // Fetch the absorption opportunity details
            await fetchAbsorptionDetails(notification.related_object_id);
        }
    };

    const fetchAbsorptionDetails = async (absorptionId) => {
        try {
            const response = await fetch('/api/v1/teocoin/teacher/absorptions/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                const absorption = data.pending_absorptions?.find(a => a.id === absorptionId);
                if (absorption) {
                    setSelectedAbsorption(absorption);
                    setShowModal(true);
                }
            }
        } catch (error) {
            console.error('Error fetching absorption details:', error);
        }
    };

    const getNotificationIcon = (type) => {
        const iconMap = {
            'teocoin_discount_pending': 'fas fa-handshake text-warning',
            'teocoin_discount_accepted': 'fas fa-check-circle text-success',
            'teocoin_discount_rejected': 'fas fa-times-circle text-info',
            'teocoin_discount_expired': 'fas fa-clock text-muted',
            'bonus_received': 'fas fa-gift text-success',
            'teocoins_earned': 'fas fa-coins text-warning',
            'teocoins_spent': 'fas fa-shopping-cart text-primary',
            'course_purchased': 'fas fa-graduation-cap text-success',
            'course_sold': 'fas fa-dollar-sign text-success',
            'exercise_graded': 'fas fa-clipboard-check text-info',
            'achievement_unlocked': 'fas fa-trophy text-warning',
            'system_message': 'fas fa-info-circle text-info'
        };
        
        return iconMap[type] || 'fas fa-bell text-muted';
    };

    const getNotificationVariant = (type) => {
        const variantMap = {
            'teocoin_discount_pending': 'warning',
            'teocoin_discount_accepted': 'success',
            'teocoin_discount_rejected': 'info',
            'teocoin_discount_expired': 'secondary',
            'bonus_received': 'success',
            'teocoins_earned': 'warning',
            'system_message': 'info'
        };
        
        return variantMap[type] || 'light';
    };

    const formatTimeAgo = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInHours = (now - date) / (1000 * 60 * 60);
        
        if (diffInHours < 1) {
            return 'Just now';
        } else if (diffInHours < 24) {
            return `${Math.floor(diffInHours)}h ago`;
        } else {
            return `${Math.floor(diffInHours / 24)}d ago`;
        }
    };

    const isActionableNotification = (type) => {
        return type === 'teocoin_discount_pending';
    };

    if (loading) {
        return (
            <Card>
                <Card.Body className="text-center">
                    <Spinner animation="border" size="sm" className="me-2" />
                    Loading notifications...
                </Card.Body>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <Card.Header>
                    <div className="d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">
                            <i className="fas fa-bell me-2"></i>
                            Notifications
                        </h5>
                        <Button
                            variant="outline-primary"
                            size="sm"
                            onClick={fetchNotifications}
                            disabled={loading}
                        >
                            <i className="fas fa-sync-alt me-1"></i>
                            Refresh
                        </Button>
                    </div>
                </Card.Header>
                
                <Card.Body className="p-0">
                    {error && (
                        <Alert variant="danger" className="m-3">
                            <i className="fas fa-exclamation-triangle me-2"></i>
                            {error}
                        </Alert>
                    )}

                    {notifications.length === 0 ? (
                        <div className="text-center text-muted py-4">
                            <i className="fas fa-inbox fa-3x mb-3"></i>
                            <h5>No notifications</h5>
                            <p>You're all caught up!</p>
                        </div>
                    ) : (
                        <ListGroup variant="flush">
                            {notifications.map((notification) => (
                                <ListGroup.Item
                                    key={notification.id}
                                    className={`d-flex justify-content-between align-items-start ${
                                        !notification.read ? 'bg-light' : ''
                                    } ${isActionableNotification(notification.notification_type) ? 'cursor-pointer' : ''}`}
                                    onClick={() => isActionableNotification(notification.notification_type) && handleNotificationClick(notification)}
                                    style={{ 
                                        cursor: isActionableNotification(notification.notification_type) ? 'pointer' : 'default'
                                    }}
                                >
                                    <div className="d-flex">
                                        <div className="me-3">
                                            <i className={getNotificationIcon(notification.notification_type)}></i>
                                        </div>
                                        <div className="flex-grow-1">
                                            <div className="fw-bold small text-muted mb-1">
                                                {notification.notification_type.replace(/_/g, ' ').toUpperCase()}
                                                {!notification.read && (
                                                    <Badge bg="primary" className="ms-2">NEW</Badge>
                                                )}
                                            </div>
                                            <p className="mb-1" style={{ fontSize: '0.9rem' }}>
                                                {notification.message}
                                            </p>
                                            <small className="text-muted">
                                                {formatTimeAgo(notification.created_at)}
                                            </small>
                                        </div>
                                    </div>
                                    <div>
                                        {isActionableNotification(notification.notification_type) && (
                                            <Button
                                                variant={getNotificationVariant(notification.notification_type)}
                                                size="sm"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleNotificationClick(notification);
                                                }}
                                            >
                                                <i className="fas fa-hand-pointer me-1"></i>
                                                Take Action
                                            </Button>
                                        )}
                                    </div>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                    )}
                </Card.Body>
            </Card>

            {/* Choice Modal for TeoCoin discount notifications */}
            <TeacherDiscountChoiceModal
                show={showModal}
                handleClose={() => setShowModal(false)}
                discountRequest={selectedAbsorption}
                onChoice={(choiceData) => {
                    setShowModal(false);
                    fetchNotifications(); // Refresh notifications after choice
                }}
            />
        </>
    );
};

export default NotificationList;
