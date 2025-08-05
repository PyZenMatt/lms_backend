import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Spinner, Alert, ProgressBar } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { getAnalyticsData, getRevenueChartData } from '../../services/api/analytics';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const RevenueAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [chartData, setChartData] = useState(null);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const [analyticsRes, chartRes] = await Promise.all([
        getAnalyticsData(),
        getRevenueChartData()
      ]);
      
      setAnalyticsData(analyticsRes.data);
      
      // Format chart data
      const chart = chartRes.data.chart_data;
      setChartData({
        labels: chart.map(item => {
          const date = new Date(item.date);
          return date.toLocaleDateString('it-IT', { month: 'short', day: 'numeric' });
        }),
        datasets: [
          {
            label: 'Revenue Daily (€)',
            data: chart.map(item => item.revenue),
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.1)',
            tension: 0.1,
            fill: true
          }
        ]
      });
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyticsData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadAnalyticsData, 300000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card>
        <Card.Body className="text-center py-5">
          <Spinner animation="border" variant="primary" />
          <p className="mt-3 text-muted">Loading revenue analytics...</p>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <i className="feather icon-alert-triangle me-2"></i>
        {error}
      </Alert>
    );
  }

  const { overview, recent_activity, top_courses, teo_economics } = analyticsData;

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Daily Revenue Trend (Last 30 Days)'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '€' + value.toLocaleString();
          }
        }
      }
    }
  };

  // Calculate TEO Pool health percentage
  const poolHealthPercentage = teo_economics.fiat_to_teo_ratio > 0 ? 
    Math.min((teo_economics.total_rewards_distributed / overview.total_revenue_eur) * 100, 100) : 0;

  return (
    <div className="revenue-analytics">
      {/* Overview Cards */}
      <Row className="g-3 mb-4">
        <Col lg={3} md={6}>
          <Card className="h-100 bg-primary text-white">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="mb-1 text-white-50">Total Revenue</h6>
                  <h4 className="mb-0 text-white">€{overview.total_revenue_eur.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</h4>
                </div>
                <div className="flex-shrink-0">
                  <i className="feather icon-euro" style={{ fontSize: '2.5rem', opacity: 0.3 }}></i>
                </div>
              </div>
              <div className="mt-3">
                <small className="text-white-50">
                  {overview.total_enrollments} total enrollments
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6}>
          <Card className="h-100 bg-success text-white">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="mb-1 text-white-50">Average Order Value</h6>
                  <h4 className="mb-0 text-white">€{overview.average_order_value.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</h4>
                </div>
                <div className="flex-shrink-0">
                  <i className="feather icon-trending-up" style={{ fontSize: '2.5rem', opacity: 0.3 }}></i>
                </div>
              </div>
              <div className="mt-3">
                <small className="text-white-50">
                  {overview.conversion_rate}% conversion rate
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6}>
          <Card className="h-100 bg-warning text-dark">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="mb-1 text-dark opacity-75">TeoCoin Rewards</h6>
                  <h4 className="mb-0 text-dark">{teo_economics.total_rewards_distributed.toLocaleString()} TEO</h4>
                </div>
                <div className="flex-shrink-0">
                  <i className="feather icon-award" style={{ fontSize: '2.5rem', opacity: 0.3 }}></i>
                </div>
              </div>
              <div className="mt-3">
                <small className="text-dark opacity-75">
                  Distributed as rewards
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6}>
          <Card className="h-100 bg-info text-white">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="mb-1 text-white-50">Last 7 Days</h6>
                  <h4 className="mb-0 text-white">€{recent_activity.revenue_7d.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</h4>
                </div>
                <div className="flex-shrink-0">
                  <i className="feather icon-calendar" style={{ fontSize: '2.5rem', opacity: 0.3 }}></i>
                </div>
              </div>
              <div className="mt-3">
                <small className="text-white-50">
                  {recent_activity.enrollments_7d} new enrollments
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Revenue Chart and TEO Economics */}
      <Row className="g-3 mb-4">
        <Col lg={8}>
          <Card className="h-100">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-trending-up me-2"></i>
                Revenue Trend
              </Card.Title>
            </Card.Header>
            <Card.Body>
              {chartData && (
                <Line data={chartData} options={chartOptions} />
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="h-100">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-shuffle me-2"></i>
                TEO Economics
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="teo-economics">
                <div className="mb-4">
                  <h6 className="mb-2">Revenue Pool Health</h6>
                  <ProgressBar 
                    now={Math.min(poolHealthPercentage, 100)}
                    variant={poolHealthPercentage > 80 ? 'success' : poolHealthPercentage > 50 ? 'warning' : 'danger'}
                    className="mb-2"
                  />
                  <small className="text-muted">
                    {poolHealthPercentage.toFixed(1)}% sustainable
                  </small>
                </div>
                
                <div className="row g-2">
                  <div className="col-6">
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-1 text-dark">€{overview.total_revenue_eur.toLocaleString()}</h6>
                      <small className="text-secondary">Fiat Revenue</small>
                    </div>
                  </div>
                  <div className="col-6">
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-1 text-dark">{teo_economics.teocoin_payments_value.toLocaleString()}</h6>
                      <small className="text-secondary">TEO Payments</small>
                    </div>
                  </div>
                </div>
                
                <div className="mt-3 p-3 bg-primary bg-opacity-10 rounded">
                  <small className="d-block text-dark">
                    <strong>Self-Sustaining Model:</strong>
                  </small>
                  <small className="text-dark opacity-75">
                    10% of fiat revenue funds TEO rewards, creating a sustainable token economy.
                  </small>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Courses */}
      <Row className="g-3">
        <Col lg={12}>
          <Card>
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-star me-2"></i>
                Top Performing Courses
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Revenue</th>
                      <th>Enrollments</th>
                      <th>Price</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {top_courses.map((course, index) => (
                      <tr key={index}>
                        <td>
                          <div className="d-flex align-items-center">
                            <div className="badge bg-primary me-2">{index + 1}</div>
                            <strong>{course.title}</strong>
                          </div>
                        </td>
                        <td>
                          <span className="text-success fw-bold">
                            €{course.revenue.toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td>
                          <span className="badge bg-info">{course.enrollments}</span>
                        </td>
                        <td>€{course.price.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</td>
                        <td>
                          <div className="d-flex align-items-center">
                            <ProgressBar 
                              now={(course.revenue / top_courses[0]?.revenue) * 100}
                              style={{ width: '60px', height: '6px' }}
                              className="me-2"
                            />
                            <small className="text-muted">
                              {((course.revenue / overview.total_revenue_eur) * 100).toFixed(1)}%
                            </small>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RevenueAnalytics;
