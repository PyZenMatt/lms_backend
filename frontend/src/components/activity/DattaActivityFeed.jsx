/**
 * 🎨 Datta Able Style Activity Feed
 * 
 * Clean, modern activity feed that matches the Datta Able theme
 */

import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Spinner } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { mockActivityAPI } from '../../services/mock/activityAPI';
import './DattaActivityFeed.css';

const DattaActivityFeed = () => {
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadActivities();
  }, []);

  const loadActivities = async () => {
    setLoading(true);
    try {
      const response = await mockActivityAPI.getActivityFeed();
      const data = await response.json();
      setActivities(data.activities || []);
    } catch (error) {
      console.error('Error loading activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    const icons = {
      'course_enrolled': 'feather icon-book-open',
      'exercise_completed': 'feather icon-check-circle',
      'lesson_viewed': 'feather icon-eye',
      'teocoin_earned': 'feather icon-award',
      'review_submitted': 'feather icon-edit',
      'achievement_unlocked': 'feather icon-star'
    };
    return icons[type] || 'feather icon-activity';
  };

  const getActivityColor = (type) => {
    const colors = {
      'course_enrolled': 'primary',
      'exercise_completed': 'success',
      'lesson_viewed': 'info',
      'teocoin_earned': 'warning',
      'review_submitted': 'secondary',
      'achievement_unlocked': 'warning'
    };
    return colors[type] || 'light';
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);

    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const filteredActivities = activities.filter(activity => {
    if (filter === 'all') return true;
    if (filter === 'teocoin') return activity.activity_type === 'teocoin_earned';
    if (filter === 'courses') return ['course_enrolled', 'exercise_completed', 'lesson_viewed'].includes(activity.activity_type);
    if (filter === 'achievements') return activity.activity_type === 'achievement_unlocked';
    return true;
  });

  const filters = [
    { key: 'all', label: 'All Activity', icon: 'feather icon-activity' },
    { key: 'teocoin', label: 'TeoCoin', icon: 'feather icon-award' },
    { key: 'courses', label: 'Courses', icon: 'feather icon-book' },
    { key: 'achievements', label: 'Achievements', icon: 'feather icon-star' }
  ];

  return (
    <Card>
      <Card.Header>
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-1">
              <i className="feather icon-activity me-2"></i>
              Activity Feed
            </h5>
            <p className="text-muted f-w-400 mb-0">
              Recent platform activities • {filteredActivities.length} items
            </p>
          </div>
          <Button 
            variant="outline-primary" 
            size="sm"
            onClick={loadActivities}
            disabled={loading}
          >
            <i className="feather icon-refresh-cw me-1"></i>
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
        </div>
      </Card.Header>

      <Card.Body>
        {/* Filter Buttons */}
        <div className="row mb-3">
          <div className="col-12">
            <div className="btn-group btn-group-sm w-100" role="group">
              {filters.map(filterItem => (
                <Button
                  key={filterItem.key}
                  variant={filter === filterItem.key ? 'primary' : 'outline-secondary'}
                  onClick={() => setFilter(filterItem.key)}
                  className="flex-fill"
                >
                  <i className={`${filterItem.icon} me-1`}></i>
                  {filterItem.label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Activity List */}
        {loading ? (
          <div className="text-center py-4">
            <Spinner animation="border" variant="primary" />
            <p className="mt-2 text-muted">Loading activities...</p>
          </div>
        ) : filteredActivities.length === 0 ? (
          <div className="text-center py-4">
            <i className="feather icon-inbox text-muted" style={{ fontSize: '3rem' }}></i>
            <p className="text-muted mt-2">No activities found</p>
          </div>
        ) : (
          <div className="activity-list-container" style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {filteredActivities.map((activity, index) => (
              <div key={activity.id || index} className="media mb-3 align-items-center">
                <div className="m-r-10">
                  <div className={`badge badge-light-${getActivityColor(activity.activity_type)} rounded-pill p-2`}>
                    <i className={getActivityIcon(activity.activity_type)}></i>
                  </div>
                </div>
                <div className="media-body">
                  <h6 className="mb-1 f-w-500">
                    {activity.user?.name || 'User'} 
                    <small className="text-muted ms-2">
                      {formatTimeAgo(activity.timestamp)}
                    </small>
                  </h6>
                  <p className="text-muted mb-1 f-w-400">
                    {activity.description}
                  </p>
                  <Badge bg={getActivityColor(activity.activity_type)} className="f-12">
                    {activity.activity_type?.replace('_', ' ') || 'Activity'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default DattaActivityFeed;
