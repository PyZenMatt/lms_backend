import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner, Alert } from '@/components/ui/legacy-shims';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const StudentTeoCoinStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');

      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/stats/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch stats: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      } else {
        throw new Error(data.error || 'Failed to load stats');
      }
    } catch (err) {
      console.error('Stats fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <Card.Body className="text-center py-4">
          <Spinner animation="border" className="me-2" />
          <span className="text-muted">Loading your TeoCoin journey...</span>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-0 shadow-sm">
        <Card.Body>
          <Alert variant="danger">
            <i className="feather icon-border rounded-md p-3 bg-muted text-muted-foreground-circle me-2"></i>
            {error}
          </Alert>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm">
      <Card.Header className="bg-gradient-primary text-white border-0">
        <Card.Title as="h5" className="mb-0 d-flex align-items-center">
          <i className="feather icon-trending-up me-2"></i>
          Your TeoCoin Journey
        </Card.Title>
      </Card.Header>
      <Card.Body>
        <Row>
          <Col md={3}>
            <div
              className="text-center p-3 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, hsl(var(--success) / 0.05) 100%)'
              }}
            >
              <i className="feather icon-award text-success" style={{ fontSize: '2rem' }}></i>
              <h4 className="text-success mt-2 mb-1">{formatAmount(stats?.total_earned || 0)}</h4>
              <p className="text-muted small mb-0">Total Earned</p>
            </div>
          </Col>
          <Col md={3}>
            <div
              className="text-center p-3 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(23, 162, 184, 0.1) 0%, hsl(var(--info) / 0.05) 100%)'
              }}
            >
              <i className="feather icon-percent text-info" style={{ fontSize: '2rem' }}></i>
              <h4 className="text-info mt-2 mb-1">{formatAmount(stats?.total_used_discounts || 0)}</h4>
              <p className="text-muted small mb-0">Used for Discounts</p>
            </div>
          </Col>
          <Col md={3}>
            <div
              className="text-center p-3 rounded"
              style={{
                background: 'linear-gradient(135deg, color-mix(in srgb, var(--warning) 10%, transparent) 0%, hsl(var(--warning) / 0.05) 100%)'
              }}
            >
              <i className="feather icon-send text-warning" style={{ fontSize: '2rem' }}></i>
              <h4 className="text-warning mt-2 mb-1">{formatAmount(stats?.total_withdrawn || 0)}</h4>
              <p className="text-muted small mb-0">Withdrawn</p>
            </div>
          </Col>
          <Col md={3}>
            <div
              className="text-center p-3 rounded"
              style={{
                background: 'linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(108, 117, 125, 0.05) 100%)'
              }}
            >
              <i className="feather icon-activity text-secondary" style={{ fontSize: '2rem' }}></i>
              <h4 className="text-secondary mt-2 mb-1">{stats?.total_transactions || 0}</h4>
              <p className="text-muted small mb-0">Total Transactions</p>
            </div>
          </Col>
        </Row>

        {/* Achievement level */}
        <div className="mt-4 text-center">
          <div
            className="p-3 rounded"
            style={{
              background: 'linear-gradient(135deg, rgba(220, 53, 69, 0.1) 0%, hsl(var(--danger) / 0.05) 100%)'
            }}
          >
            <h5 className="text-danger mb-2">
              <i className="feather icon-star me-2"></i>
              {stats?.achievement_level || 'Beginner'} Student
            </h5>
            <p className="text-muted small mb-0">{stats?.next_level_info || 'Complete more exercises to earn more TeoCoin!'}</p>
          </div>
        </div>

        {/* Recent achievement */}
        {stats?.recent_achievement && (
          <Alert variant="success" className="mt-3 mb-0">
            <i className="feather icon-trophy me-2"></i>
            <strong>Recent Achievement:</strong> {stats.recent_achievement}
          </Alert>
        )}
      </Card.Body>
    </Card>
  );
};

export default StudentTeoCoinStats;
