/**
 * 🔥 PHASE 4: Real-time Activity Feed Component
 * 
 * Displays live activity feed with:
 * - Real-time course enrollments
 * - TeoCoin transactions
 * - Achievement unlocks
 * - User interactions
 * - Social features
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, Badge, Button, Spinner, Alert, Modal, Form, InputGroup } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';
import WebSocketService from '../../services/websocket/WebSocketService';
import { mockActivityAPI } from '../../services/mock/activityAPI';
import './RealTimeActivityFeed.css';

const RealTimeActivityFeed = () => {
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLive, setIsLive] = useState(false);
  const [filter, setFilter] = useState('all');
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [comment, setComment] = useState('');
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const feedEndRef = useRef(null);

  // Activity filters
  const filters = {
    all: { label: 'All Activity', icon: '📊' },
    teocoin: { label: 'TeoCoin', icon: '🪙' },
    courses: { label: 'Courses', icon: '📚' },
    achievements: { label: 'Achievements', icon: '🏆' },
    social: { label: 'Social', icon: '💬' }
  };

  useEffect(() => {
    loadActivityHistory();
    setupWebSocketListeners();
    
    return () => {
      // Cleanup WebSocket listeners
      WebSocketService.off('user_activity', handleNewActivity);
      WebSocketService.off('connection_status', handleConnectionStatus);
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new activities arrive
    if (feedEndRef.current && isLive) {
      feedEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activities, isLive]);

  /**
   * Load activity history from API
   */
  const loadActivityHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('accessToken');
      
      // Try real API first
      try {
        const response = await fetch('/api/v1/activity/feed/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`API not available: ${response.status}`);
        }

        const data = await response.json();
        setActivities(data.activities || []);
        
      } catch (apiError) {
        console.log('📡 Real API not available, using mock data...');
        
        // Fallback to mock API
        const mockResponse = await mockActivityAPI.getActivityFeed();
        const mockData = await mockResponse.json();
        setActivities(mockData.activities || []);
        
        // Show info message that we're using mock data
        showSuccess('Demo Mode: Using sample activity data for demonstration');
      }

    } catch (error) {
      console.error('❌ Error loading activity feed:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Setup WebSocket listeners for real-time updates
   */
  const setupWebSocketListeners = () => {
    try {
      // Listen for new activities
      WebSocketService.on('user_activity', handleNewActivity);
      
      // Listen for connection status
      WebSocketService.on('connection_status', handleConnectionStatus);
      
      // Listen for online users
      WebSocketService.on('user_online', handleUserOnline);
      WebSocketService.on('user_offline', handleUserOffline);
      
      // Try to connect WebSocket (with fallback to mock)
      const token = localStorage.getItem('accessToken');
      if (token) {
        console.log('🔌 Attempting WebSocket connection...');
        WebSocketService.connect(token);
        
        // Set up mock activity simulation if WebSocket fails
        setTimeout(() => {
          if (!WebSocketService.getStatus().connected) {
            console.log('📡 WebSocket failed, starting mock activity simulation...');
            startMockActivitySimulation();
          }
        }, 5000); // Wait 5 seconds for connection
      }
      
    } catch (error) {
      console.error('❌ WebSocket setup failed:', error);
      startMockActivitySimulation();
    }
  };

  /**
   * Start mock activity simulation when WebSocket is not available
   */
  const startMockActivitySimulation = () => {
    console.log('🎭 Starting mock activity simulation...');
    setIsLive(false); // Not truly live, but simulated
    
    // Subscribe to mock activity updates
    const unsubscribe = mockActivityAPI.subscribeToActivities((event) => {
      if (event.type === 'new_activity') {
        handleNewActivity(event.data);
      }
    });
    
    // Store unsubscribe function for cleanup
    return unsubscribe;
  };

  /**
   * Handle new activity from WebSocket
   */
  const handleNewActivity = (activityData) => {
    const newActivity = {
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      ...activityData
    };

    setActivities(prev => [newActivity, ...prev].slice(0, 100)); // Keep last 100 activities
    
    // Show notification for relevant activities
    if (shouldNotifyActivity(newActivity)) {
      showActivityNotification(newActivity);
    }
  };

  /**
   * Handle WebSocket connection status
   */
  const handleConnectionStatus = (status) => {
    setIsLive(status.connected);
    
    if (status.connected) {
      showSuccess('🔴 Live feed connected!');
    } else {
      showError('🔴 Live feed disconnected');
    }
  };

  /**
   * Handle user coming online
   */
  const handleUserOnline = (userData) => {
    setOnlineUsers(prev => new Set([...prev, userData.user_id]));
  };

  /**
   * Handle user going offline
   */
  const handleUserOffline = (userData) => {
    setOnlineUsers(prev => {
      const newSet = new Set(prev);
      newSet.delete(userData.user_id);
      return newSet;
    });
  };

  /**
   * Check if activity should trigger notification
   */
  const shouldNotifyActivity = (activity) => {
    // Only notify for activities related to current user or their content
    if (activity.user_id === user.id) return false; // Don't notify for own activities
    
    return (
      activity.activity_type === 'course_enrolled' && activity.teacher_id === user.id ||
      activity.activity_type === 'course_completed' && activity.teacher_id === user.id ||
      activity.activity_type === 'achievement_unlocked' ||
      activity.activity_type === 'teocoin_milestone'
    );
  };

  /**
   * Show notification for activity
   */
  const showActivityNotification = (activity) => {
    const message = formatActivityMessage(activity, false);
    showSuccess(message, 4000);
  };

  /**
   * Get filtered activities
   */
  const getFilteredActivities = () => {
    if (filter === 'all') return activities;
    
    return activities.filter(activity => {
      switch (filter) {
        case 'teocoin':
          return ['teocoin_earned', 'teocoin_spent', 'teocoin_staked', 'teocoin_milestone'].includes(activity.activity_type);
        case 'courses':
          return ['course_enrolled', 'course_completed', 'course_published', 'lesson_completed'].includes(activity.activity_type);
        case 'achievements':
          return ['achievement_unlocked', 'badge_earned', 'level_up'].includes(activity.activity_type);
        case 'social':
          return ['comment_added', 'like_given', 'share_created'].includes(activity.activity_type);
        default:
          return true;
      }
    });
  };

  /**
   * Format activity message
   */
  const formatActivityMessage = (activity, showTime = true) => {
    const timeStr = showTime ? ` • ${formatTimeAgo(activity.timestamp)}` : '';
    const userName = activity.user_name || activity.user?.name || 'User';
    
    // If we have a description, use it (for mock data)
    if (activity.description) {
      return `${userName} ${activity.description}${timeStr}`;
    }
    
    if (!activity.activity_type) {
      return `${userName} performed an action${timeStr}`;
    }
    
    switch (activity.activity_type) {
      case 'course_enrolled':
        return `📚 ${userName} enrolled in "${activity.course_title}"${timeStr}`;
      case 'course_completed':
        return `🎓 ${userName} completed "${activity.course_title}"${timeStr}`;
      case 'course_published':
        return `✨ ${userName} published "${activity.course_title}"${timeStr}`;
      case 'lesson_completed':
        return `📖 ${userName} completed lesson "${activity.lesson_title}"${timeStr}`;
      case 'teocoin_earned':
        return `🪙 ${userName} earned ${activity.amount} TEO${timeStr}`;
      case 'teocoin_spent':
        return `💰 ${userName} spent ${activity.amount} TEO${timeStr}`;
      case 'teocoin_staked':
        return `🔒 ${userName} staked ${activity.amount} TEO${timeStr}`;
      case 'teocoin_milestone':
        return `🎯 ${userName} reached ${activity.milestone} TEO milestone${timeStr}`;
      case 'achievement_unlocked':
        return `🏆 ${userName} unlocked "${activity.achievement_name}"${timeStr}`;
      case 'badge_earned':
        return `🎖️ ${userName} earned "${activity.badge_name}" badge${timeStr}`;
      case 'level_up':
        return `⬆️ ${userName} reached level ${activity.new_level}${timeStr}`;
      case 'comment_added':
        return `💬 ${userName} commented on "${activity.target_title}"${timeStr}`;
      case 'like_given':
        return `❤️ ${userName} liked "${activity.target_title}"${timeStr}`;
      default:
        return `${userName} performed an action${timeStr}`;
    }
  };

  /**
   * Format time ago
   */
  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);

    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  /**
   * Get activity icon
   */
  const getActivityIcon = (activityType) => {
    if (!activityType) return '📊';
    
    switch (activityType) {
      case 'course_enrolled':
      case 'course_completed':
      case 'course_published':
        return '📚';
      case 'lesson_completed':
        return '📖';
      case 'teocoin_earned':
      case 'teocoin_spent':
      case 'teocoin_staked':
      case 'teocoin_milestone':
        return '🪙';
      case 'achievement_unlocked':
        return '🏆';
      case 'badge_earned':
        return '🎖️';
      case 'level_up':
        return '⬆️';
      case 'comment_added':
        return '💬';
      case 'like_given':
        return '❤️';
      default:
        return '📊';
    }
  };

  /**
   * Get activity priority color
   */
  const getActivityPriority = (activityType) => {
    if (!activityType) return 'light';
    
    switch (activityType) {
      case 'achievement_unlocked':
      case 'level_up':
      case 'teocoin_milestone':
        return 'success';
      case 'course_completed':
      case 'course_published':
        return 'primary';
      case 'teocoin_earned':
      case 'teocoin_staked':
        return 'warning';
      default:
        return 'light';
    }
  };

  /**
   * Handle activity interaction
   */
  const handleActivityClick = (activity) => {
    if (activity.activity_type === 'comment_added' || activity.activity_type === 'like_given') {
      setSelectedActivity(activity);
      setShowCommentModal(true);
    }
  };

  /**
   * Add comment to activity
   */
  const handleAddComment = async () => {
    if (!comment.trim()) return;

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/v1/activity/comment/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          activity_id: selectedActivity.id,
          comment: comment.trim()
        })
      });

      if (response.ok) {
        showSuccess('Comment added!');
        setComment('');
        setShowCommentModal(false);
      }
    } catch (error) {
      showError('Failed to add comment');
    }
  };

  const filteredActivities = getFilteredActivities();

  return (
    <div className="real-time-activity-feed">
      <Card className="activity-feed-card">
        <Card.Header className="activity-feed-header">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0">
                <i className="fas fa-broadcast-tower me-2"></i>
                Live Activity Feed
                <Badge 
                  bg={isLive ? 'success' : 'secondary'} 
                  className="ms-2 activity-status-badge"
                >
                  {isLive ? '🔴 LIVE' : '⚫ OFFLINE'}
                </Badge>
              </h5>
              <small className="text-muted">
                {onlineUsers.size} users online • {filteredActivities.length} activities
              </small>
            </div>
            <Button
              variant="outline-primary"
              size="sm"
              onClick={loadActivityHistory}
              disabled={loading}
            >
              <i className="fas fa-sync-alt me-1"></i>
              Refresh
            </Button>
          </div>
        </Card.Header>

        <Card.Body className="p-0">
          {/* Filters */}
          <div className="activity-filters">
            {Object.entries(filters).map(([key, filterData]) => (
              <Button
                key={key}
                variant={filter === key ? 'primary' : 'outline-secondary'}
                size="sm"
                className="filter-btn"
                onClick={() => setFilter(key)}
              >
                <span className="me-1">{filterData.icon}</span>
                {filterData.label}
              </Button>
            ))}
          </div>

          {/* Activity Feed */}
          <div className="activity-feed-container">
            {loading && (
              <div className="text-center p-4">
                <Spinner animation="border" variant="primary" />
                <p className="mt-2 text-muted">Loading activity feed...</p>
              </div>
            )}

            {error && (
              <Alert variant="danger" className="m-3">
                <i className="fas fa-exclamation-triangle me-2"></i>
                {error}
              </Alert>
            )}

            {!loading && filteredActivities.length === 0 && (
              <div className="text-center p-4 text-muted">
                <i className="fas fa-rss fa-3x mb-3"></i>
                <h5>No Activity Yet</h5>
                <p>Activity will appear here as users interact with the platform.</p>
              </div>
            )}

            {!loading && filteredActivities.length > 0 && (
              <div className="activity-list">
                {filteredActivities.map((activity, index) => (
                  <div 
                    key={activity.id}
                    className={`activity-item ${index === 0 && isLive ? 'new-activity' : ''}`}
                    onClick={() => handleActivityClick(activity)}
                  >
                    <div className="activity-icon">
                      <span className="icon-wrapper">
                        {getActivityIcon(activity.activity_type)}
                      </span>
                      {onlineUsers.has(activity.user_id) && (
                        <div className="online-indicator"></div>
                      )}
                    </div>
                    
                    <div className="activity-content">
                      <div className="activity-message">
                        {formatActivityMessage(activity)}
                      </div>
                      
                      {activity.description && (
                        <div className="activity-description">
                          {activity.description}
                        </div>
                      )}
                      
                      <div className="activity-meta">
                        <Badge bg={getActivityPriority(activity.activity_type)}>
                          {activity.activity_type ? activity.activity_type.replace('_', ' ') : 'Activity'}
                        </Badge>
                        {activity.points && (
                          <span className="activity-points">
                            +{activity.points} pts
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="activity-actions">
                      {activity.activity_type === 'course_enrolled' && activity.teacher_id === user.id && (
                        <Button variant="outline-success" size="sm">
                          <i className="fas fa-graduation-cap"></i>
                        </Button>
                      )}
                      {activity.activity_type === 'achievement_unlocked' && (
                        <Button variant="outline-warning" size="sm">
                          <i className="fas fa-trophy"></i>
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={feedEndRef} />
              </div>
            )}
          </div>
        </Card.Body>
      </Card>

      {/* Comment Modal */}
      <Modal 
        show={showCommentModal} 
        onHide={() => setShowCommentModal(false)}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="fas fa-comment me-2"></i>
            Add Comment
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedActivity && (
            <div className="mb-3">
              <div className="activity-preview">
                {formatActivityMessage(selectedActivity, false)}
              </div>
            </div>
          )}
          <Form>
            <Form.Group>
              <Form.Label>Your Comment</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Write a comment..."
                maxLength={500}
              />
              <Form.Text className="text-muted">
                {comment.length}/500 characters
              </Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button 
            variant="secondary" 
            onClick={() => setShowCommentModal(false)}
          >
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleAddComment}
            disabled={!comment.trim()}
          >
            <i className="fas fa-paper-plane me-1"></i>
            Add Comment
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default RealTimeActivityFeed;
