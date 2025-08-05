const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
/**
 * 🎉 Development Status Dashboard
 * 
 * Shows implementation status and handles development mode gracefully
 */

import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Alert, Badge, Button, Accordion, ProgressBar } from 'react-bootstrap';
import { useTheme } from '../../contexts/ThemeContext';
import ThemeToggle from '../../components/ui/ThemeToggle';

const DevelopmentStatusDashboard = () => {
  const { isDark } = useTheme();
  const [apiStatus, setApiStatus] = useState({
    websocket: 'checking',
    activity: 'checking',
    staking: 'checking',
    notifications: 'checking'
  });

  useEffect(() => {
    checkAPIStatus();
  }, []);

  const checkAPIStatus = async () => {
    const checks = {
      websocket: 'unavailable',
      activity: 'unavailable', 
      staking: 'unavailable',
      notifications: 'unavailable'
    };

    try {
      // Quick API checks (these will fail in development)
      const responses = await Promise.allSettled([
        fetch(`${API_BASE_URL}/api/v1/activity/feed/`, { method: 'HEAD' }),
        fetch(`${API_BASE_URL}/api/v1/teocoin/staking-info/`, { method: 'HEAD' }),
        fetch(`${API_BASE_URL}/api/v1/notifications/`, { method: 'HEAD' })
      ]);

      checks.activity = responses[0].status === 'fulfilled' && responses[0].value.ok ? 'available' : 'mock';
      checks.staking = responses[1].status === 'fulfilled' && responses[1].value.ok ? 'available' : 'mock';
      checks.notifications = responses[2].status === 'fulfilled' && responses[2].value.ok ? 'available' : 'mock';
      checks.websocket = 'mock'; // WebSocket always falls back to mock in development

    } catch (error) {
      // All services are using mock data
      Object.keys(checks).forEach(key => {
        checks[key] = 'mock';
      });
    }

    setApiStatus(checks);
  };

  const features = [
    {
      name: '🌙 Dark Theme System',
      status: 'complete',
      description: 'Comprehensive dark/light theme with system preference detection',
      progress: 100,
      details: [
        'ThemeContext for global state management',
        'Animated theme toggle component',
        'CSS custom properties for dynamic colors',
        'Local storage persistence',
        'System preference detection',
        'Mobile browser meta theme support'
      ]
    },
    {
      name: '📊 Real-time Activity Feed',
      status: 'demo',
      description: 'Live activity feed with WebSocket support (mock data in development)',
      progress: 95,
      details: [
        'Mock activity generation',
        'Real-time simulation',
        'User interaction tracking',
        'Achievement notifications',
        'WebSocket fallback handling'
      ]
    },
    {
      name: '📈 Advanced Analytics',
      status: 'complete',
      description: 'Enhanced analytics dashboard with charts and metrics',
      progress: 100,
      details: [
        'Interactive charts with Chart.js',
        'Performance metrics',
        'User engagement tracking',
        'Export functionality',
        'Responsive design'
      ]
    },
    {
      name: '💰 TeoCoin Staking',
      status: 'demo',
      description: 'Teacher staking interface (mock data in development)',
      progress: 90,
      details: [
        'Mock staking simulation',
        'Tier calculation',
        'Earnings projection',
        'Transaction history',
        'Error handling with fallbacks'
      ]
    },
    {
      name: '🔔 Enhanced Notifications',
      status: 'complete',
      description: 'Advanced notification system with real-time updates',
      progress: 100,
      details: [
        'Multiple notification types',
        'Real-time delivery',
        'Sound and visual alerts',
        'Browser notifications',
        'Notification center'
      ]
    },
    {
      name: '📱 PWA Features',
      status: 'complete',
      description: 'Progressive Web App capabilities',
      progress: 100,
      details: [
        'Service worker implementation',
        'Offline functionality',
        'App manifest',
        'Installation prompts',
        'Background sync'
      ]
    }
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'complete':
        return <Badge bg="success">✅ Complete</Badge>;
      case 'demo':
        return <Badge bg="warning">🎭 Demo Mode</Badge>;
      case 'in-progress':
        return <Badge bg="info">🚧 In Progress</Badge>;
      default:
        return <Badge bg="secondary">⏳ Planned</Badge>;
    }
  };

  const getAPIStatusBadge = (status) => {
    switch (status) {
      case 'available':
        return <Badge bg="success">🟢 Live</Badge>;
      case 'mock':
        return <Badge bg="warning">🎭 Mock</Badge>;
      case 'unavailable':
        return <Badge bg="danger">🔴 Offline</Badge>;
      default:
        return <Badge bg="secondary">⏳ Checking</Badge>;
    }
  };

  return (
    <Container fluid className="p-4">
      <Row>
        <Col lg={12}>
          <Card className="border-0 shadow-sm mb-4">
            <Card.Header className="bg-transparent border-0 pb-0">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h3 className="mb-1">🎉 SchoolPlatform Development Status</h3>
                  <p className="text-muted mb-0">
                    Phase 4 implementation complete with comprehensive features
                  </p>
                </div>
                <ThemeToggle size="lg" showLabel={true} />
              </div>
            </Card.Header>

            <Card.Body>
              {/* Development Mode Notice */}
              <Alert variant={isDark ? 'info' : 'primary'} className="mb-4">
                <div className="d-flex align-items-start">
                  <div className="me-3" style={{ fontSize: '1.5rem' }}>🔧</div>
                  <div className="flex-grow-1">
                    <h5 className="mb-2">Development Mode Active</h5>
                    <p className="mb-2">
                      The application is running in development mode with mock data services. 
                      All UI features are fully functional for demonstration purposes.
                    </p>
                    <small>
                      🎭 Mock services provide realistic data simulation when backend is not available.
                    </small>
                  </div>
                </div>
              </Alert>

              {/* API Status */}
              <Row className="mb-4">
                <Col lg={12}>
                  <h5 className="mb-3">🔌 Service Status</h5>
                  <Row>
                    {Object.entries(apiStatus).map(([service, status]) => (
                      <Col md={3} key={service} className="mb-2">
                        <Card className="h-100">
                          <Card.Body className="p-3 text-center">
                            <h6 className="mb-2">{service.charAt(0).toUpperCase() + service.slice(1)}</h6>
                            {getAPIStatusBadge(status)}
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Col>
              </Row>

              {/* Feature Implementation Status */}
              <h5 className="mb-3">🚀 Implementation Progress</h5>
              <Accordion>
                {features.map((feature, index) => (
                  <Accordion.Item eventKey={index.toString()} key={index}>
                    <Accordion.Header>
                      <div className="d-flex align-items-center justify-content-between w-100 me-3">
                        <div className="d-flex align-items-center">
                          <span className="me-3">{feature.name}</span>
                          {getStatusBadge(feature.status)}
                        </div>
                        <div className="text-end" style={{ minWidth: '100px' }}>
                          <ProgressBar 
                            now={feature.progress} 
                            style={{ height: '8px', width: '80px' }}
                            variant={feature.progress === 100 ? 'success' : 'warning'}
                          />
                          <small className="text-muted">{feature.progress}%</small>
                        </div>
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      <p className="mb-3">{feature.description}</p>
                      <h6>Implemented Features:</h6>
                      <ul className="mb-0">
                        {feature.details.map((detail, idx) => (
                          <li key={idx} className="text-muted">{detail}</li>
                        ))}
                      </ul>
                    </Accordion.Body>
                  </Accordion.Item>
                ))}
              </Accordion>

              {/* Quick Navigation */}
              <div className="mt-4">
                <h5 className="mb-3">🧭 Quick Navigation</h5>
                <Row>
                  <Col md={4} className="mb-2">
                    <Button 
                      variant="outline-primary" 
                      href="/profile/settings/theme"
                      className="w-100"
                    >
                      🌙 Theme Settings
                    </Button>
                  </Col>
                  <Col md={4} className="mb-2">
                    <Button 
                      variant="outline-success" 
                      href="/demo/dark-theme"
                      className="w-100"
                    >
                      🎨 Theme Showcase
                    </Button>
                  </Col>
                  <Col md={4} className="mb-2">
                    <Button 
                      variant="outline-info" 
                      href="/dashboard/teacher"
                      className="w-100"
                    >
                      📊 Teacher Dashboard
                    </Button>
                  </Col>
                </Row>
              </div>

              {/* Development Notes */}
              <Alert variant="light" className="mt-4">
                <h6>📝 Development Notes:</h6>
                <ul className="mb-0 small">
                  <li><strong>Mock Data:</strong> All APIs use realistic mock data when backend is unavailable</li>
                  <li><strong>Error Handling:</strong> Graceful fallbacks prevent application crashes</li>
                  <li><strong>Theme System:</strong> Complete dark/light theme with persistence</li>
                  <li><strong>Real-time Features:</strong> Simulated WebSocket events for demonstration</li>
                  <li><strong>PWA Ready:</strong> Service worker and offline functionality implemented</li>
                </ul>
              </Alert>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default DevelopmentStatusDashboard;
