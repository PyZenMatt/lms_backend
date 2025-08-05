/**
 * 🔥 PHASE 4: Advanced Analytics Dashboard Component
 * 
 * Real-time analytics with:
 * - Live performance metrics
 * - Interactive charts
 * - Predictive insights
 * - Custom dashboards
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Badge, Button, Dropdown, Form, Alert } from 'react-bootstrap';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';
import { useAuth } from '../../contexts/AuthContext';
import './AdvancedAnalyticsDashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
);

const AdvancedAnalyticsDashboard = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState({});
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [realTimeData, setRealTimeData] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [customMetrics, setCustomMetrics] = useState([]);
  const intervalRef = useRef(null);

  // Time range options
  const timeRanges = {
    '1d': '24 Hours',
    '7d': '7 Days',
    '30d': '30 Days',
    '90d': '3 Months',
    '1y': '1 Year'
  };

  useEffect(() => {
    loadAnalytics();
    setupRealTimeUpdates();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [timeRange]);

  /**
   * Load analytics data from API
   */
  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('accessToken');
      const response = await fetch(`/api/v1/analytics/dashboard/?time_range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load analytics: ${response.status}`);
      }

      const data = await response.json();
      setAnalytics(data);
      setPredictions(data.predictions || {});
      setCustomMetrics(data.custom_metrics || []);

    } catch (error) {
      console.error('❌ Error loading analytics:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Setup real-time updates
   */
  const setupRealTimeUpdates = () => {
    // Update analytics every 30 seconds
    intervalRef.current = setInterval(() => {
      loadAnalytics();
    }, 30000);
  };

  /**
   * Generate KPI cards data
   */
  const getKPICards = () => {
    const { summary = {} } = analytics;
    
    return [
      {
        title: 'Total Revenue',
        value: `€${(summary.total_revenue || 0).toLocaleString()}`,
        change: summary.revenue_change || 0,
        icon: '💰',
        color: 'success'
      },
      {
        title: 'Active Students',
        value: (summary.active_students || 0).toLocaleString(),
        change: summary.students_change || 0,
        icon: '👥',
        color: 'primary'
      },
      {
        title: 'Course Completions',
        value: (summary.course_completions || 0).toLocaleString(),
        change: summary.completions_change || 0,
        icon: '🎓',
        color: 'info'
      },
      {
        title: 'TeoCoin Circulation',
        value: `${(summary.teocoin_circulation || 0).toLocaleString()} TEO`,
        change: summary.teocoin_change || 0,
        icon: '🪙',
        color: 'warning'
      }
    ];
  };

  /**
   * Generate revenue chart data
   */
  const getRevenueChartData = () => {
    const { revenue_data = [] } = analytics;
    
    return {
      labels: revenue_data.map(item => 
        new Date(item.date).toLocaleDateString('it-IT', { 
          month: 'short', 
          day: 'numeric' 
        })
      ),
      datasets: [
        {
          label: 'Revenue (€)',
          data: revenue_data.map(item => item.amount),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'Predicted',
          data: predictions.revenue || [],
          borderColor: 'rgba(255, 99, 132, 0.7)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          borderDash: [5, 5],
          fill: false,
          tension: 0.4
        }
      ]
    };
  };

  /**
   * Generate user engagement chart data
   */
  const getUserEngagementData = () => {
    const { user_engagement = {} } = analytics;
    
    return {
      labels: ['Course Views', 'Lesson Completions', 'TeoCoin Transactions', 'Social Interactions'],
      datasets: [
        {
          label: 'Current Period',
          data: [
            user_engagement.course_views || 0,
            user_engagement.lesson_completions || 0,
            user_engagement.teocoin_transactions || 0,
            user_engagement.social_interactions || 0
          ],
          backgroundColor: [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)'
          ]
        }
      ]
    };
  };

  /**
   * Generate performance radar chart data
   */
  const getPerformanceRadarData = () => {
    const { performance_metrics = {} } = analytics;
    
    return {
      labels: [
        'Student Satisfaction',
        'Course Quality',
        'Engagement Rate',
        'Completion Rate',
        'Revenue Growth',
        'Platform Usage'
      ],
      datasets: [
        {
          label: 'Current Performance',
          data: [
            performance_metrics.satisfaction_score || 0,
            performance_metrics.quality_score || 0,
            performance_metrics.engagement_rate || 0,
            performance_metrics.completion_rate || 0,
            performance_metrics.revenue_growth || 0,
            performance_metrics.usage_score || 0
          ],
          backgroundColor: 'rgba(102, 126, 234, 0.2)',
          borderColor: 'rgba(102, 126, 234, 1)',
          pointBackgroundColor: 'rgba(102, 126, 234, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
        },
        {
          label: 'Target',
          data: [85, 90, 75, 80, 70, 85], // Target values
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          pointBackgroundColor: 'rgba(75, 192, 192, 1)',
          pointBorderColor: '#fff'
        }
      ]
    };
  };

  /**
   * Generate real-time activity chart
   */
  const getRealTimeActivityData = () => {
    const last24Hours = realTimeData.filter(
      item => Date.now() - item.timestamp < 24 * 60 * 60 * 1000
    );

    // Group by hour
    const hourlyData = {};
    last24Hours.forEach(item => {
      const hour = new Date(item.timestamp).getHours();
      hourlyData[hour] = (hourlyData[hour] || 0) + 1;
    });

    const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const data = labels.map((_, hour) => hourlyData[hour] || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Activity Count',
          data,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    };
  };

  /**
   * Chart options
   */
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        }
      },
      y: {
        display: true,
        grid: {
          borderDash: [2, 2]
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100
      }
    }
  };

  const kpiCards = getKPICards();

  if (loading) {
    return (
      <div className="text-center p-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading analytics...</span>
        </div>
        <p className="mt-3 text-muted">Loading advanced analytics...</p>
      </div>
    );
  }

  return (
    <div className="advanced-analytics-dashboard">
      {/* Header */}
      <div className="analytics-header">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h3 className="mb-0">
              <i className="fas fa-chart-line me-2"></i>
              Advanced Analytics
              <Badge bg="success" className="ms-2">
                <i className="fas fa-circle pulse-dot"></i>
                LIVE
              </Badge>
            </h3>
            <p className="text-muted mb-0">Real-time insights and performance metrics</p>
          </div>
          
          <div className="d-flex gap-2">
            <Dropdown>
              <Dropdown.Toggle variant="outline-primary" size="sm">
                <i className="fas fa-calendar me-1"></i>
                {timeRanges[timeRange]}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                {Object.entries(timeRanges).map(([key, label]) => (
                  <Dropdown.Item
                    key={key}
                    active={timeRange === key}
                    onClick={() => setTimeRange(key)}
                  >
                    {label}
                  </Dropdown.Item>
                ))}
              </Dropdown.Menu>
            </Dropdown>
            
            <Button 
              variant="outline-secondary" 
              size="sm"
              onClick={loadAnalytics}
            >
              <i className="fas fa-sync-alt"></i>
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="danger" className="mb-4">
          <i className="fas fa-exclamation-triangle me-2"></i>
          {error}
        </Alert>
      )}

      {/* KPI Cards */}
      <Row className="mb-4">
        {kpiCards.map((kpi, index) => (
          <Col lg={3} md={6} key={index} className="mb-3">
            <Card className={`kpi-card kpi-${kpi.color}`}>
              <Card.Body>
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <div className="kpi-icon">{kpi.icon}</div>
                    <h3 className="kpi-value">{kpi.value}</h3>
                    <p className="kpi-title">{kpi.title}</p>
                  </div>
                  <div className={`kpi-change ${kpi.change >= 0 ? 'positive' : 'negative'}`}>
                    <i className={`fas fa-arrow-${kpi.change >= 0 ? 'up' : 'down'}`}></i>
                    {Math.abs(kpi.change)}%
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Charts Row 1 */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card className="chart-card">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-chart-area me-2"></i>
                Revenue Trends & Predictions
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="chart-container" style={{ height: '300px' }}>
                <Line data={getRevenueChartData()} options={chartOptions} />
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="chart-card">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-chart-pie me-2"></i>
                User Engagement
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="chart-container" style={{ height: '300px' }}>
                <Doughnut data={getUserEngagementData()} options={{ ...chartOptions, maintainAspectRatio: true }} />
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Charts Row 2 */}
      <Row className="mb-4">
        <Col lg={6}>
          <Card className="chart-card">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-radar-chart me-2"></i>
                Performance Radar
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="chart-container" style={{ height: '300px' }}>
                <Radar data={getPerformanceRadarData()} options={radarOptions} />
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={6}>
          <Card className="chart-card">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-activity me-2"></i>
                Real-time Activity (24h)
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="chart-container" style={{ height: '300px' }}>
                <Line data={getRealTimeActivityData()} options={chartOptions} />
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Custom Metrics */}
      {customMetrics.length > 0 && (
        <Row>
          <Col lg={12}>
            <Card className="chart-card">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="fas fa-cogs me-2"></i>
                  Custom Metrics
                </h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  {customMetrics.map((metric, index) => (
                    <Col lg={3} md={6} key={index} className="mb-3">
                      <div className="custom-metric">
                        <div className="metric-icon">{metric.icon}</div>
                        <h4 className="metric-value">{metric.value}</h4>
                        <p className="metric-label">{metric.label}</p>
                        {metric.trend && (
                          <div className={`metric-trend ${metric.trend > 0 ? 'up' : 'down'}`}>
                            <i className={`fas fa-arrow-${metric.trend > 0 ? 'up' : 'down'}`}></i>
                            {Math.abs(metric.trend)}%
                          </div>
                        )}
                      </div>
                    </Col>
                  ))}
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default AdvancedAnalyticsDashboard;
