import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Alert, Spinner, Button, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import PendingTeachersCard from '../../components/cards/PendingTeachersCard';
import PendingCoursesCard from '../../components/cards/PendingCoursesCard';
import ApprovalStats from '../../components/ui/ApprovalStats';
import AdminTransactionMonitor from '../../components/admin/AdminTransactionMonitor';
import AdminTeoCoinDashboard from '../../components/blockchain/DBAdminTeoCoinDashboard';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import RevenueAnalytics from '../../components/admin/RevenueAnalytics';
import { fetchAdminDashboard } from '../../services/api/admin';
import { fetchUserProfile } from '../../services/api/dashboard';
import { getRewardPoolInfo } from '../../services/api/blockchain';

// Import dashboard styles
import '../dashboard/dashboard-styles.css';

// Placeholder avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [rewardPoolStatus, setRewardPoolStatus] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    totalUsers: 0,
    totalCourses: 0,
    pendingApprovals: 0,
    monthlyRevenue: 0
  });

  // Enhanced admin stats with better calculations
  const adminStatsData = [
    {
      title: 'Utenti Totali',
      value: dashboardData.totalUsers.toString(),
      icon: 'users',
      iconColor: 'text-primary',
      percentage: Math.min((dashboardData.totalUsers / 1000) * 100, 100),
      description: 'Studenti e insegnanti registrati',
      bgGradient: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(4, 169, 245, 0.05) 100%)'
    },
    {
      title: 'Corsi Attivi',
      value: dashboardData.totalCourses.toString(),
      icon: 'book-open',
      iconColor: 'text-success',
      percentage: Math.min((dashboardData.totalCourses / 100) * 100, 100),
      description: 'Corsi pubblicati sulla piattaforma',
      bgGradient: 'linear-gradient(135deg, rgba(29, 233, 182, 0.1) 0%, rgba(29, 233, 182, 0.05) 100%)'
    },
    {
      title: 'Revenue Mensile',
      value: `€${dashboardData.monthlyRevenue}`,
      icon: 'trending-up',
      iconColor: 'text-warning',
      percentage: Math.min((dashboardData.monthlyRevenue / 10000) * 100, 100),
      description: 'Ricavi della piattaforma',
      bgGradient: 'linear-gradient(135deg, rgba(244, 194, 43, 0.1) 0%, rgba(244, 194, 43, 0.05) 100%)'
    },
    {
      title: 'Approvazioni',
      value: dashboardData.pendingApprovals.toString(),
      icon: 'check-circle',
      iconColor: 'text-info',
      percentage: dashboardData.pendingApprovals > 0 ? 100 : 0,
      description: 'Contenuti in attesa di revisione',
      bgGradient: 'linear-gradient(135deg, rgba(23, 162, 184, 0.1) 0%, rgba(23, 162, 184, 0.05) 100%)'
    }
  ];

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchAdminDashboard();
        setDashboardData(res.data);
        
        // Fetch reward pool status
        try {
          const poolRes = await getRewardPoolInfo();
          setRewardPoolStatus(poolRes.data);
        } catch (poolErr) {
          console.error('Error fetching reward pool info:', poolErr);
          // Don't show error for this, just show in console
        }
      } catch (err) {
        console.error('Errore API admin dashboard:', err);
        setError('Errore nel caricamento della dashboard admin');
        // Fallback data for demo
        setDashboardData({
          totalUsers: 150,
          totalCourses: 25,
          pendingApprovals: 8,
          monthlyRevenue: 2450
        });
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="pcoded-content">
        <div className="card">
          <div className="card-body text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="mt-3 text-muted">Caricamento dashboard admin...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <React.Fragment>
      {/* Enhanced Welcome Section */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center py-5" style={{
              background: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(29, 233, 182, 0.1) 100%)'
            }}>
              <div className="d-flex align-items-center justify-content-center mb-3">
                <div className="avatar-lg me-3">
                  <div className="d-flex align-items-center justify-content-center bg-primary rounded-circle text-white" style={{ width: '70px', height: '70px' }}>
                    <i className="feather icon-shield" style={{ fontSize: '2rem' }} />
                  </div>
                </div>
                <div className="text-start">
                  <h2 className="fw-bold mb-1 text-dark">
                    Pannello Amministratore
                  </h2>
                  <p className="text-muted mb-0">
                    Gestisci la piattaforma TeoArt e approva nuovi contenuti
                    {userProfile?.first_name && <span className="fw-semibold"> - {userProfile.first_name}</span>}
                  </p>
                </div>
              </div>
              
              {/* Quick Admin Actions */}
              <div className="d-flex gap-3 justify-content-center flex-wrap mt-4">
                <Link to="/admin/reward-pool" className="btn btn-primary rounded-pill px-4 py-2">
                  <i className="feather icon-database me-2"></i>
                  Reward Pool
                </Link>
                <Link to="/admin/pending-courses" className="btn btn-outline-primary rounded-pill px-4 py-2">
                  <i className="feather icon-book-open me-2"></i>
                  Approva Corsi
                </Link>
                <Button 
                  variant="outline-secondary" 
                  className="rounded-pill px-4 py-2"
                  onClick={() => {
                    const revenueSection = document.getElementById('revenue-analytics');
                    if (revenueSection) {
                      revenueSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                >
                  <i className="feather icon-bar-chart-2 me-2"></i>
                  Analytics
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Enhanced Stats Cards */}
      <Row className="mb-4">
        {adminStatsData.map((data, index) => (
          <Col key={index} md={6} xl={3}>
            <Card className="dashboard-stat-card border-0 shadow-sm h-100">
              <Card.Body style={{ background: data.bgGradient }}>
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <div className="stat-icon">
                    <i className={`feather icon-${data.icon} ${data.iconColor}`} style={{ fontSize: '2.5rem' }} />
                  </div>
                  <div className="text-end">
                    <h3 className="mb-0 fw-bold text-dark">{data.value}</h3>
                    <small className="text-muted">{data.percentage}%</small>
                  </div>
                </div>
                <h6 className="mb-2 fw-semibold text-dark">{data.title}</h6>
                <p className="text-muted mb-3 small">{data.description}</p>
                <div className="progress mb-0" style={{ height: '6px' }}>
                  <div
                    className="progress-bar progress-c-theme"
                    role="progressbar"
                    style={{ width: data.percentage + '%' }}
                    aria-valuenow={data.percentage}
                    aria-valuemin="0"
                    aria-valuemax="100"
                  />
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* System Alerts */}
      {error && (
        <Alert variant="warning" className="mb-4 border-0 shadow-sm">
          <i className="feather icon-alert-circle me-2"></i>
          {error}
        </Alert>
      )}
      
      {/* Reward Pool Status Alert */}
      {rewardPoolStatus && rewardPoolStatus.status === 'critical' && (
        <Alert variant="danger" className="mb-4 border-0 shadow-sm">
          <Row className="align-items-center">
            <Col>
              <i className="feather icon-alert-triangle me-2"></i>
              <strong>Critical:</strong> Reward Pool MATIC balance is critically low ({rewardPoolStatus.matic_balance} MATIC). 
              Transactions may fail!
            </Col>
            <Col xs="auto">
              <Link to="/admin/reward-pool" className="btn btn-light btn-sm">
                Manage Reward Pool
              </Link>
            </Col>
          </Row>
        </Alert>
      )}
      
      {rewardPoolStatus && rewardPoolStatus.status === 'warning' && (
        <Alert variant="warning" className="mb-4 border-0 shadow-sm">
          <Row className="align-items-center">
            <Col>
              <i className="feather icon-alert-circle me-2"></i>
              <strong>Warning:</strong> Reward Pool MATIC balance is low ({rewardPoolStatus.matic_balance} MATIC). 
              Consider refilling soon.
            </Col>
            <Col xs="auto">
              <Link to="/admin/reward-pool" className="btn btn-light btn-sm">
                Manage Reward Pool
              </Link>
            </Col>
          </Row>
        </Alert>
      )}

      {/* Platform Overview */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-transparent">
              <Card.Title as="h5" className="mb-0">
                <i className="feather icon-activity text-primary me-2"></i>
                Attività Piattaforma
              </Card.Title>
              <small className="text-muted">Panoramica delle attività recenti</small>
            </Card.Header>
            <Card.Body>
              <div className="platform-activity">
                <div className="activity-item d-flex align-items-center mb-3">
                  <div className="activity-indicator me-3">
                    <div className="rounded-circle d-flex align-items-center justify-content-center bg-success" 
                         style={{ width: '40px', height: '40px' }}>
                      <i className="feather icon-user-plus text-white"></i>
                    </div>
                  </div>
                  <div className="flex-grow-1">
                    <h6 className="mb-1 fw-semibold">Nuovi Utenti Registrati</h6>
                    <p className="text-muted mb-0 small">+15 studenti, +3 insegnanti nelle ultime 24h</p>
                  </div>
                  <div className="text-end">
                    <Badge bg="success" className="rounded-pill">+18</Badge>
                  </div>
                </div>
                
                <div className="activity-item d-flex align-items-center mb-3">
                  <div className="activity-indicator me-3">
                    <div className="rounded-circle d-flex align-items-center justify-content-center bg-primary" 
                         style={{ width: '40px', height: '40px' }}>
                      <i className="feather icon-book text-white"></i>
                    </div>
                  </div>
                  <div className="flex-grow-1">
                    <h6 className="mb-1 fw-semibold">Corsi Pubblicati</h6>
                    <p className="text-muted mb-0 small">5 nuovi corsi approvati questa settimana</p>
                  </div>
                  <div className="text-end">
                    <Badge bg="primary" className="rounded-pill">+5</Badge>
                  </div>
                </div>
                
                <div className="activity-item d-flex align-items-center">
                  <div className="activity-indicator me-3">
                    <div className="rounded-circle d-flex align-items-center justify-content-center bg-warning" 
                         style={{ width: '40px', height: '40px' }}>
                      <i className="feather icon-clock text-white"></i>
                    </div>
                  </div>
                  <div className="flex-grow-1">
                    <h6 className="mb-1 fw-semibold">Approvazioni Pending</h6>
                    <p className="text-muted mb-0 small">{dashboardData.pendingApprovals} contenuti in attesa</p>
                  </div>
                  <div className="text-end">
                    <Badge bg="warning" className="rounded-pill">{dashboardData.pendingApprovals}</Badge>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-transparent">
              <Card.Title as="h6" className="mb-0">
                <i className="feather icon-trending-up text-success me-2"></i>
                Metriche Chiave
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="admin-metrics">
                <div className="metric-item mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="small fw-semibold">Engagement Rate</span>
                    <span className="small text-success fw-bold">87%</span>
                  </div>
                  <div className="progress" style={{ height: '6px' }}>
                    <div className="progress-bar bg-success" style={{ width: '87%' }}></div>
                  </div>
                </div>
                
                <div className="metric-item mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="small fw-semibold">Revenue Growth</span>
                    <span className="small text-primary fw-bold">+23%</span>
                  </div>
                  <div className="progress" style={{ height: '6px' }}>
                    <div className="progress-bar bg-primary" style={{ width: '76%' }}></div>
                  </div>
                </div>
                
                <div className="metric-item">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="small fw-semibold">System Health</span>
                    <span className="small text-success fw-bold">Optimal</span>
                  </div>
                  <div className="progress" style={{ height: '6px' }}>
                    <div className="progress-bar bg-success" style={{ width: '95%' }}></div>
                  </div>
                </div>
              </div>
              
              <div className="text-center mt-4">
                <small className="text-muted">
                  <i className="feather icon-refresh-cw me-1"></i>
                  Aggiornato 2 min fa
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Admin Actions Grid */}
      <Row className="g-3 mb-4">
        <Col lg={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="border-0 bg-light">
              <Card.Title as="h5">
                <i className="feather icon-command me-2"></i>
                Azioni Amministrative
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <Row className="g-3">
                <Col md={3} sm={6}>
                  <Link to="/admin/reward-pool" className="btn btn-outline-primary w-100 py-3 border-0 shadow-sm admin-action-btn">
                    <i className="feather icon-database d-block mb-2" style={{ fontSize: '1.8rem' }}></i>
                    <strong>Reward Pool</strong>
                    <small className="d-block text-muted mt-1">Gestisci MATIC</small>
                  </Link>
                </Col>
                <Col md={3} sm={6}>
                  <Button 
                    variant="outline-success" 
                    className="w-100 py-3 border-0 shadow-sm admin-action-btn" 
                    onClick={() => {
                      const revenueSection = document.getElementById('revenue-analytics');
                      if (revenueSection) {
                        revenueSection.scrollIntoView({ behavior: 'smooth' });
                      }
                    }}
                  >
                    <i className="feather icon-bar-chart-2 d-block mb-2" style={{ fontSize: '1.8rem' }}></i>
                    <strong>Analytics</strong>
                    <small className="d-block text-muted mt-1">Revenue & Stats</small>
                  </Button>
                </Col>
                <Col md={3} sm={6}>
                  <Link to="/admin/pending-courses" className="btn btn-outline-info w-100 py-3 border-0 shadow-sm admin-action-btn">
                    <i className="feather icon-book-open d-block mb-2" style={{ fontSize: '1.8rem' }}></i>
                    <strong>Approvazioni</strong>
                    <small className="d-block text-muted mt-1">Corsi pending</small>
                  </Link>
                </Col>
                <Col md={3} sm={6}>
                  <Button 
                    variant="outline-warning" 
                    className="w-100 py-3 border-0 shadow-sm admin-action-btn"
                    onClick={() => {
                      const transactionSection = document.getElementById('transaction-monitor');
                      if (transactionSection) {
                        transactionSection.scrollIntoView({ behavior: 'smooth' });
                      }
                    }}
                  >
                    <i className="feather icon-activity d-block mb-2" style={{ fontSize: '1.8rem' }}></i>
                    <strong>Transazioni</strong>
                    <small className="d-block text-muted mt-1">Monitor blockchain</small>
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Pending Approvals */}
      <Row className="g-3 mb-4">
        <Col lg={6} md={12}>
          <PendingTeachersCard />
        </Col>
        <Col lg={6} md={12}>
          <PendingCoursesCard />
        </Col>
      </Row>

      {/* Approval Stats */}
      <Row className="g-3 mb-4">
        <Col lg={12}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-light">
              <Card.Title as="h5">
                <i className="feather icon-bar-chart-2 me-2"></i>
                Statistiche Approvazioni
              </Card.Title>
            </Card.Header>
            <Card.Body className="approval-stats">
              <ApprovalStats />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Revenue Analytics */}
      <Row className="g-3 mb-4" id="revenue-analytics">
        <Col lg={12}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-light">
              <Card.Title as="h5">
                <i className="feather icon-trending-up me-2"></i>
                Revenue Analytics
              </Card.Title>
              <p className="text-muted mb-0 small">
                Comprehensive revenue tracking, course performance, and TEO economics
              </p>
            </Card.Header>
            <Card.Body>
              <RevenueAnalytics />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Transaction Monitor */}
      <Row className="g-3 mb-4" id="transaction-monitor">
        <Col lg={12}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-light">
              <Card.Title as="h5">
                <i className="feather icon-activity me-2"></i>
                Monitoraggio Transazioni Blockchain
              </Card.Title>
              <p className="text-muted mb-0 small">
                Monitor delle transazioni TEO per reward, acquisti e pagamenti degli utenti
              </p>
            </Card.Header>
            <Card.Body>
              <AdminTransactionMonitor />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* TeoCoin Dashboard and Balance */}
      <Row>
        <Col lg={8}>
          <AdminTeoCoinDashboard />
        </Col>
        <Col lg={4}>
          <TeoCoinBalanceWidget variant="compact" />
        </Col>
      </Row>
    </React.Fragment>
  );
};

export default AdminDashboard;
