import React, { useState, useEffect } from 'react';
import { 
  Container, Row, Col, Card, ProgressBar, Badge, Button,
  Dropdown, Alert, Spinner, Table
} from 'react-bootstrap';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import './AnalyticsDashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7days');
  const [analyticsData, setAnalyticsData] = useState(null);

  useEffect(() => {
    // Simulate data loading
    const loadAnalytics = async () => {
      setLoading(true);
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock analytics data
      setAnalyticsData({
        overview: {
          totalStudents: 324,
          activeCourses: 12,
          totalRevenue: 15420.50,
          completionRate: 78.5,
          avgRating: 4.3,
          totalViews: 2854
        },
        trends: {
          studentGrowth: [45, 52, 48, 61, 58, 67, 74],
          revenueGrowth: [1200, 1350, 1280, 1450, 1380, 1520, 1680],
          labels: ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        },
        topCourses: [
          { id: 1, title: 'React Avanzato', students: 89, revenue: 4450, rating: 4.8 },
          { id: 2, title: 'Python per Principianti', students: 76, revenue: 3800, rating: 4.6 },
          { id: 3, title: 'JavaScript Moderno', students: 68, revenue: 3400, rating: 4.5 },
          { id: 4, title: 'Design Thinking', students: 45, revenue: 2250, rating: 4.4 },
          { id: 5, title: 'Digital Marketing', students: 38, revenue: 1900, rating: 4.2 }
        ],
        categoryStats: {
          labels: ['Programmazione', 'Design', 'Marketing', 'Business', 'Lingue'],
          data: [45, 25, 15, 10, 5],
          colors: ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8']
        }
      });
      
      setLoading(false);
    };

    loadAnalytics();
  }, [timeRange]);

  const getGrowthIndicator = (current, previous) => {
    const growth = ((current - previous) / previous) * 100;
    return {
      percentage: Math.abs(growth).toFixed(1),
      isPositive: growth > 0,
      icon: growth > 0 ? 'trending-up' : 'trending-down',
      color: growth > 0 ? 'success' : 'danger'
    };
  };

  // Chart configurations
  const studentTrendConfig = {
    data: {
      labels: analyticsData?.trends.labels || [],
      datasets: [
        {
          label: 'Nuovi Studenti',
          data: analyticsData?.trends.studentGrowth || [],
          borderColor: 'rgb(4, 169, 245)',
          backgroundColor: 'rgba(4, 169, 245, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: 'rgb(4, 169, 245)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgb(4, 169, 245)',
          borderWidth: 1,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
          ticks: {
            color: '#6c757d',
          },
        },
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: '#6c757d',
          },
        },
      },
    },
  };

  const revenueChartConfig = {
    data: {
      labels: analyticsData?.trends.labels || [],
      datasets: [
        {
          label: 'Revenue (TEO)',
          data: analyticsData?.trends.revenueGrowth || [],
          backgroundColor: 'rgba(40, 167, 69, 0.8)',
          borderColor: 'rgb(40, 167, 69)',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgb(40, 167, 69)',
          borderWidth: 1,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
          ticks: {
            color: '#6c757d',
            callback: function(value) {
              return value + ' TEO';
            },
          },
        },
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: '#6c757d',
          },
        },
      },
    },
  };

  const categoryChartConfig = {
    data: {
      labels: analyticsData?.categoryStats.labels || [],
      datasets: [
        {
          data: analyticsData?.categoryStats.data || [],
          backgroundColor: analyticsData?.categoryStats.colors || [],
          borderWidth: 0,
          hoverOffset: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            color: '#495057',
          },
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.parsed}%`;
            },
          },
        },
      },
    },
  };

  if (loading) {
    return (
      <Container className="analytics-dashboard">
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
          <p className="mt-3 text-muted">Caricamento analytics...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid className="analytics-dashboard">
      {/* Header */}
      <div className="dashboard-header mb-4">
        <Row className="align-items-center">
          <Col>
            <h2 className="dashboard-title mb-1">Analytics Dashboard</h2>
            <p className="text-muted mb-0">Monitora le performance dei tuoi corsi</p>
          </Col>
          <Col xs="auto">
            <Dropdown>
              <Dropdown.Toggle 
                variant="outline-primary" 
                className="analytics-filter-btn"
                style={{ borderRadius: '25px' }}
              >
                <i className="feather icon-calendar me-2"></i>
                {timeRange === '7days' && 'Ultimi 7 giorni'}
                {timeRange === '30days' && 'Ultimi 30 giorni'}
                {timeRange === '90days' && 'Ultimi 3 mesi'}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item onClick={() => setTimeRange('7days')}>Ultimi 7 giorni</Dropdown.Item>
                <Dropdown.Item onClick={() => setTimeRange('30days')}>Ultimi 30 giorni</Dropdown.Item>
                <Dropdown.Item onClick={() => setTimeRange('90days')}>Ultimi 3 mesi</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </Col>
        </Row>
      </div>

      {/* Key Metrics */}
      <Row className="mb-4">
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-primary">
                <i className="feather icon-users"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.totalStudents}</h3>
              <p className="metric-label text-muted mb-2">Studenti Totali</p>
              <Badge variant="success" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +12.5%
              </Badge>
            </Card.Body>
          </Card>
        </Col>
        
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-success">
                <i className="feather icon-book-open"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.activeCourses}</h3>
              <p className="metric-label text-muted mb-2">Corsi Attivi</p>
              <Badge variant="info" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +2 questo mese
              </Badge>
            </Card.Body>
          </Card>
        </Col>
        
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-warning">
                <i className="feather icon-dollar-sign"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.totalRevenue.toFixed(0)}</h3>
              <p className="metric-label text-muted mb-2">Revenue (TEO)</p>
              <Badge variant="success" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +8.3%
              </Badge>
            </Card.Body>
          </Card>
        </Col>
        
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-info">
                <i className="feather icon-target"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.completionRate}%</h3>
              <p className="metric-label text-muted mb-2">Tasso Completamento</p>
              <Badge variant="success" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +3.2%
              </Badge>
            </Card.Body>
          </Card>
        </Col>
        
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-danger">
                <i className="feather icon-star"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.avgRating}</h3>
              <p className="metric-label text-muted mb-2">Rating Medio</p>
              <Badge variant="success" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +0.2
              </Badge>
            </Card.Body>
          </Card>
        </Col>
        
        <Col xl={2} md={4} sm={6} className="mb-3">
          <Card className="metric-card border-0 h-100">
            <Card.Body className="text-center">
              <div className="metric-icon mb-3 mx-auto bg-secondary">
                <i className="feather icon-eye"></i>
              </div>
              <h3 className="metric-value mb-1">{analyticsData.overview.totalViews}</h3>
              <p className="metric-label text-muted mb-2">Visualizzazioni</p>
              <Badge variant="success" className="metric-growth">
                <i className="feather icon-trending-up me-1"></i>
                +15.7%
              </Badge>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row className="mb-4">
        <Col lg={8} className="mb-4">
          <Card className="chart-card border-0 h-100">
            <Card.Header className="bg-transparent border-0 pb-0">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Crescita Studenti</h5>
                <Badge variant="primary" className="px-3">Trend Settimanale</Badge>
              </div>
            </Card.Header>
            <Card.Body>
              <div style={{ height: '300px' }}>
                <Line {...studentTrendConfig} />
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4} className="mb-4">
          <Card className="chart-card border-0 h-100">
            <Card.Header className="bg-transparent border-0 pb-0">
              <h5 className="card-title mb-0">Categorie Corsi</h5>
            </Card.Header>
            <Card.Body>
              <div style={{ height: '300px' }}>
                <Doughnut {...categoryChartConfig} />
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Revenue and Top Courses */}
      <Row className="mb-4">
        <Col lg={7} className="mb-4">
          <Card className="chart-card border-0 h-100">
            <Card.Header className="bg-transparent border-0 pb-0">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">Revenue Trend</h5>
                <Badge variant="success" className="px-3">TEO Tokens</Badge>
              </div>
            </Card.Header>
            <Card.Body>
              <div style={{ height: '300px' }}>
                <Bar {...revenueChartConfig} />
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={5} className="mb-4">
          <Card className="border-0 h-100">
            <Card.Header className="bg-transparent border-0 pb-0">
              <h5 className="card-title mb-0">Top Corsi Performanti</h5>
            </Card.Header>
            <Card.Body className="p-0">
              <div className="top-courses-list">
                {analyticsData.topCourses.map((course, index) => (
                  <div key={course.id} className="course-item d-flex align-items-center p-3 border-bottom">
                    <div className="position-indicator me-3">
                      <Badge 
                        variant={index === 0 ? 'warning' : index === 1 ? 'secondary' : 'light'}
                        className="rounded-circle p-2"
                        style={{ width: '35px', height: '35px', lineHeight: '1' }}
                      >
                        #{index + 1}
                      </Badge>
                    </div>
                    <div className="flex-grow-1">
                      <h6 className="mb-1">{course.title}</h6>
                      <div className="d-flex gap-3 align-items-center">
                        <small className="text-muted">
                          <i className="feather icon-users me-1"></i>
                          {course.students} studenti
                        </small>
                        <small className="text-muted">
                          <i className="feather icon-star me-1"></i>
                          {course.rating}
                        </small>
                      </div>
                    </div>
                    <div className="text-end">
                      <div className="fw-bold text-success">{course.revenue} TEO</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="text-center p-3">
                <Button variant="outline-primary" size="sm" style={{ borderRadius: '20px' }}>
                  Visualizza Tutti i Corsi
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* Insights and Recommendations */}
      <Row>
        <Col lg={12}>
          <Card className="border-0">
            <Card.Header className="bg-transparent border-0">
              <h5 className="card-title mb-0">
                <i className="feather icon-lightbulb me-2 text-warning"></i>
                Insights e Raccomandazioni
              </h5>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={4} className="mb-3">
                  <Alert variant="success" className="border-0 shadow-sm">
                    <Alert.Heading className="h6">
                      <i className="feather icon-trending-up me-2"></i>
                      Crescita Positiva
                    </Alert.Heading>
                    <p className="mb-0 small">
                      Le iscrizioni sono aumentate del 12.5% questa settimana. 
                      Ottimo lavoro sui contenuti!
                    </p>
                  </Alert>
                </Col>
                <Col md={4} className="mb-3">
                  <Alert variant="warning" className="border-0 shadow-sm">
                    <Alert.Heading className="h6">
                      <i className="feather icon-target me-2"></i>
                      Opportunità
                    </Alert.Heading>
                    <p className="mb-0 small">
                      Il corso "React Avanzato" ha il rating più alto. 
                      Considera di creare contenuti simili.
                    </p>
                  </Alert>
                </Col>
                <Col md={4} className="mb-3">
                  <Alert variant="info" className="border-0 shadow-sm">
                    <Alert.Heading className="h6">
                      <i className="feather icon-clock me-2"></i>
                      Timing Ottimale
                    </Alert.Heading>
                    <p className="mb-0 small">
                      Le pubblicazioni del mercoledì ottengono più engagement. 
                      Pianifica i nuovi contenuti di conseguenza.
                    </p>
                  </Alert>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AnalyticsDashboard;
