import React, { useState, useEffect } from 'react';
import { 
  Card, Badge, Spinner, Alert, Button, Row, Col, 
  Modal, Tabs, Tab, ProgressBar, Table 
} from 'react-bootstrap';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { useAuth } from '../../contexts/AuthContext';
import PendingWithdrawals from './PendingWithdrawals';
import BurnDepositInterface from './BurnDepositInterface';
import './EnhancedStudentTeoCoinDashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

/**
 * Enhanced StudentTeoCoinDashboard - Phase 3 with modern design and analytics
 */
const EnhancedStudentTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    balance: {
      available_balance: '0.00',
      staked_balance: '0.00',
      pending_withdrawal: '0.00',
      total_balance: '0.00'
    },
    recentTransactions: [],
    statistics: {},
    achievements: [],
    spendingAnalytics: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Auto-refresh interval
  const REFRESH_INTERVAL = 10000;

  useEffect(() => {
    loadDashboardData();
    
    const interval = setInterval(loadDashboardData, REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Load balance
      const balanceResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!balanceResponse.ok) {
        throw new Error(`Balance API error! status: ${balanceResponse.status}`);
      }

      const balanceData = await balanceResponse.json();

      const balance = balanceData.success && balanceData.balance 
        ? {
            available_balance: parseFloat(balanceData.balance.available || 0).toFixed(2),
            staked_balance: parseFloat(balanceData.balance.staked || 0).toFixed(2),
            pending_withdrawal: parseFloat(balanceData.balance.pending_withdrawal || 0).toFixed(2),
            total_balance: parseFloat(balanceData.balance.total || 0).toFixed(2)
          }
        : {
            available_balance: '0.00',
            staked_balance: '0.00', 
            pending_withdrawal: '0.00',
            total_balance: '0.00'
          };

      // Load transactions
      let transactionsData = [];
      try {
        const transactionsResponse = await fetch('/api/v1/teocoin/transactions/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (transactionsResponse.ok) {
          transactionsData = await transactionsResponse.json();
        }
      } catch (transactionError) {
        console.warn('Failed to load transactions:', transactionError);
      }

      // Load statistics
      const statsResponse = await fetch('/api/v1/teocoin/statistics/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const statsData = statsResponse.ok ? await statsResponse.json() : {};

      // Generate mock analytics data
      const spendingAnalytics = generateSpendingAnalytics(transactionsData);
      const achievements = generateAchievements(balance, transactionsData);

      setDashboardData({
        balance: balance,
        recentTransactions: Array.isArray(transactionsData) ? transactionsData.slice(0, 5) : [],
        statistics: statsData,
        achievements: achievements,
        spendingAnalytics: spendingAnalytics
      });

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateSpendingAnalytics = (transactions) => {
    if (!Array.isArray(transactions) || transactions.length === 0) {
      return null;
    }

    const last7Days = [];
    const categories = {};
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      last7Days.push({
        date: date.toISOString().split('T')[0],
        amount: Math.random() * 50 + 10
      });
    }

    // Mock category data
    const categoryData = {
      'Corsi': 45,
      'Sconti': 25,
      'Ricompense': 20,
      'Altro': 10
    };

    return {
      dailySpending: last7Days,
      categories: categoryData,
      monthlyTotal: last7Days.reduce((sum, day) => sum + day.amount, 0),
      avgDaily: last7Days.reduce((sum, day) => sum + day.amount, 0) / 7
    };
  };

  const generateAchievements = (balance, transactions) => {
    const achievements = [];
    const totalBalance = parseFloat(balance.total_balance);
    
    if (totalBalance >= 100) {
      achievements.push({
        id: 'balance_100',
        title: 'Centurione',
        description: 'Raggiungi 100 TEO di saldo totale',
        icon: 'award',
        color: '#ffc107',
        completed: true
      });
    }

    if (Array.isArray(transactions) && transactions.length >= 10) {
      achievements.push({
        id: 'transactions_10',
        title: 'Trader Attivo',
        description: 'Completa 10 transazioni',
        icon: 'trending-up',
        color: '#28a745',
        completed: true
      });
    }

    if (totalBalance >= 500) {
      achievements.push({
        id: 'balance_500',
        title: 'Investitore',
        description: 'Raggiungi 500 TEO di saldo totale',
        icon: 'star',
        color: '#007bff',
        completed: true
      });
    }

    // Add some uncompleted achievements
    achievements.push({
      id: 'balance_1000',
      title: 'Milionario TEO',
      description: 'Raggiungi 1000 TEO di saldo totale',
      icon: 'crown',
      color: '#6f42c1',
      completed: totalBalance >= 1000,
      progress: Math.min(100, (totalBalance / 1000) * 100)
    });

    return achievements;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'credit':
      case 'reward':
        return '💰';
      case 'discount':
      case 'course_purchase':
        return '🛒';
      case 'stake':
        return '🔒';
      case 'unstake':
        return '🔓';
      case 'withdrawal':
        return '📤';
      case 'deposit':
        return '📥';
      default:
        return '💫';
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'credit':
      case 'reward':
        return 'success';
      case 'discount':
      case 'course_purchase':
        return 'primary';
      case 'stake':
        return 'warning';
      case 'unstake':
        return 'info';
      case 'withdrawal':
        return 'secondary';
      default:
        return 'light';
    }
  };

  // Chart configurations
  const spendingChartConfig = dashboardData.spendingAnalytics ? {
    data: {
      labels: dashboardData.spendingAnalytics.dailySpending.map(item => 
        new Date(item.date).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })
      ),
      datasets: [
        {
          label: 'Spesa Giornaliera (TEO)',
          data: dashboardData.spendingAnalytics.dailySpending.map(item => item.amount),
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#007bff',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
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
          borderColor: '#007bff',
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
  } : null;

  const categoryChartConfig = dashboardData.spendingAnalytics ? {
    data: {
      labels: Object.keys(dashboardData.spendingAnalytics.categories),
      datasets: [
        {
          data: Object.values(dashboardData.spendingAnalytics.categories),
          backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'],
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
  } : null;

  if (loading && !dashboardData.balance.total_balance) {
    return (
      <Card className="enhanced-teocoin-dashboard">
        <Card.Body className="text-center py-5">
          <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
          <p className="mt-3 text-muted">Caricamento dashboard TeoCoin...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="enhanced-student-teocoin-dashboard">
      {/* Header */}
      <div className="dashboard-header mb-4">
        <Row className="align-items-center">
          <Col>
            <h4 className="dashboard-title mb-1">
              <i className="fas fa-coins me-2"></i>
              Dashboard TeoCoin
            </h4>
            <p className="text-muted mb-0">
              Gestisci i tuoi TEO e monitora le tue attività
            </p>
          </Col>
          <Col xs="auto">
            <div className="d-flex gap-2">
              <Badge variant="success" className="px-3 py-2">
                DB-Based
              </Badge>
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => setShowAnalyticsModal(true)}
                style={{ borderRadius: '15px' }}
              >
                <i className="feather icon-bar-chart-2 me-1"></i>
                Analytics
              </Button>
            </div>
          </Col>
        </Row>
        {lastUpdate && (
          <small className="text-muted">
            Ultimo aggiornamento: {formatDate(lastUpdate)}
          </small>
        )}
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)} className="modern-alert">
          <Alert.Heading>Errore</Alert.Heading>
          {error}
        </Alert>
      )}

      {/* Balance Cards */}
      <Row className="mb-4">
        <Col lg={4} md={6} className="mb-3">
          <Card className="balance-card border-0 h-100">
            <Card.Body className="text-center p-4">
              <div className="balance-icon mx-auto mb-3 bg-primary">
                <i className="fas fa-wallet"></i>
              </div>
              <h3 className="balance-value mb-1">
                {parseFloat(dashboardData.balance.available_balance).toFixed(2)}
              </h3>
              <p className="balance-label text-muted mb-3">TEO Disponibili</p>
              <div className="balance-actions">
                <Badge variant="success" className="px-3">
                  Utilizzabile per sconti
                </Badge>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={4} md={6} className="mb-3">
          <Card className="balance-card border-0 h-100">
            <Card.Body className="text-center p-4">
              <div className="balance-icon mx-auto mb-3 bg-info">
                <i className="fas fa-chart-line"></i>
              </div>
              <h3 className="balance-value mb-1">
                {parseFloat(dashboardData.balance.total_balance).toFixed(2)}
              </h3>
              <p className="balance-label text-muted mb-3">Saldo Totale</p>
              <div className="balance-actions">
                <Badge variant="info" className="px-3">
                  Patrimonio completo
                </Badge>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Staking Card - Only for Teachers */}
        {user?.role === 'teacher' && (
          <Col lg={4} md={6} className="mb-3">
            <Card className="balance-card border-0 h-100">
              <Card.Body className="text-center p-4">
                <div className="balance-icon mx-auto mb-3 bg-warning">
                  <i className="fas fa-lock"></i>
                </div>
                <h3 className="balance-value mb-1">
                  {parseFloat(dashboardData.balance.staked_balance).toFixed(2)}
                </h3>
                <p className="balance-label text-muted mb-3">TEO in Staking</p>
                <div className="balance-actions">
                  <Badge variant="warning" className="px-3">
                    Solo Insegnanti
                  </Badge>
                </div>
              </Card.Body>
            </Card>
          </Col>
        )}

        {/* Achievements Preview - Show only if not teacher or as 4th card */}
        {(user?.role !== 'teacher' || dashboardData.balance.staked_balance !== '0.00') && (
          <Col lg={user?.role === 'teacher' ? 12 : 4} md={6} className="mb-3">
            <Card className="achievements-preview-card border-0 h-100">
              <Card.Body className="p-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h6 className="mb-0">
                    <i className="feather icon-award me-2"></i>
                    Obiettivi
                  </h6>
                  <Badge variant="secondary">
                    {dashboardData.achievements.filter(a => a.completed).length}/{dashboardData.achievements.length}
                  </Badge>
                </div>
                <div className="achievements-grid">
                  {dashboardData.achievements.slice(0, 3).map(achievement => (
                    <div key={achievement.id} className="achievement-item d-flex align-items-center mb-2">
                      <div 
                        className={`achievement-icon me-2 ${achievement.completed ? 'completed' : 'incomplete'}`}
                        style={{ color: achievement.color }}
                      >
                        <i className={`feather icon-${achievement.icon}`}></i>
                      </div>
                      <div className="flex-grow-1">
                        <small className={`achievement-title ${achievement.completed ? 'text-dark' : 'text-muted'}`}>
                          {achievement.title}
                        </small>
                        {!achievement.completed && achievement.progress && (
                          <ProgressBar 
                            now={achievement.progress} 
                            size="sm" 
                            className="mt-1"
                            style={{ height: '4px' }}
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card.Body>
            </Card>
          </Col>
        )}
      </Row>

      {/* Pending Withdrawals */}
      {parseFloat(dashboardData.balance.pending_withdrawal) > 0 && (
        <Row className="mb-4">
          <Col>
            <PendingWithdrawals 
              onTransactionComplete={(data) => {
                loadDashboardData();
              }}
            />
          </Col>
        </Row>
      )}

      {/* Deposit Interface */}
      <Row className="mb-4">
        <Col>
          <BurnDepositInterface 
            onTransactionComplete={(data) => {
              loadDashboardData();
            }}
          />
        </Col>
      </Row>

      {/* Recent Transactions */}
      <Card className="transactions-card border-0">
        <Card.Header className="bg-transparent border-0">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="feather icon-activity me-2"></i>
              Transazioni Recenti
            </h5>
            <Button 
              variant="outline-primary" 
              size="sm"
              onClick={loadDashboardData}
              disabled={loading}
              style={{ borderRadius: '15px' }}
            >
              {loading ? (
                <Spinner animation="border" size="sm" />
              ) : (
                <i className="fas fa-sync-alt"></i>
              )}
              <span className="ms-1">Aggiorna</span>
            </Button>
          </div>
        </Card.Header>
        <Card.Body>
          {dashboardData.recentTransactions.length === 0 ? (
            <div className="text-center py-4">
              <i className="fas fa-history fa-3x text-muted mb-3"></i>
              <p className="text-muted">Nessuna transazione recente</p>
              <small>Le tue transazioni appariranno qui</small>
            </div>
          ) : (
            <div className="transactions-list">
              {dashboardData.recentTransactions
                .filter(transaction => {
                  if (user?.role === 'student') {
                    return !['stake', 'unstake'].includes(transaction.type);
                  }
                  return true;
                })
                .map((transaction, index) => (
                <div key={transaction.id || index} className="transaction-item">
                  <div className="transaction-icon">
                    {getTransactionIcon(transaction.type)}
                  </div>
                  <div className="transaction-details">
                    <div className="transaction-header">
                      <Badge bg={getTransactionColor(transaction.type)} className="transaction-type">
                        {transaction.type}
                      </Badge>
                      <span className="transaction-amount">
                        {parseFloat(transaction.amount || 0).toFixed(2)} TEO
                      </span>
                    </div>
                    <div className="transaction-description">
                      {transaction.description || 'Transazione TeoCoin'}
                    </div>
                    <small className="transaction-date text-muted">
                      {formatDate(transaction.created_at || new Date())}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Analytics Modal */}
      <Modal 
        show={showAnalyticsModal} 
        onHide={() => setShowAnalyticsModal(false)}
        size="lg"
        centered
        className="analytics-modal"
      >
        <Modal.Header closeButton className="border-0">
          <Modal.Title>
            <i className="feather icon-bar-chart-2 me-2"></i>
            Analytics TEO
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="p-4">
          <Tabs
            activeKey={activeTab}
            onSelect={(k) => setActiveTab(k)}
            className="analytics-tabs"
          >
            <Tab eventKey="overview" title={
              <span><i className="feather icon-trending-up me-2"></i>Panoramica</span>
            }>
              <div className="analytics-overview mt-4">
                <Row>
                  <Col md={6} className="mb-4">
                    <Card className="border-0 bg-light">
                      <Card.Body>
                        <h6 className="mb-3">Spesa negli ultimi 7 giorni</h6>
                        {spendingChartConfig && (
                          <div style={{ height: '200px' }}>
                            <Line {...spendingChartConfig} />
                          </div>
                        )}
                      </Card.Body>
                    </Card>
                  </Col>
                  <Col md={6} className="mb-4">
                    <Card className="border-0 bg-light">
                      <Card.Body>
                        <h6 className="mb-3">Distribuzione Spese</h6>
                        {categoryChartConfig && (
                          <div style={{ height: '200px' }}>
                            <Doughnut {...categoryChartConfig} />
                          </div>
                        )}
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
                
                {dashboardData.spendingAnalytics && (
                  <Row>
                    <Col md={6} className="mb-3">
                      <div className="stat-item text-center p-3 rounded bg-primary text-white">
                        <h4 className="mb-1">{dashboardData.spendingAnalytics.monthlyTotal.toFixed(2)} TEO</h4>
                        <small>Spesa Totale (7 giorni)</small>
                      </div>
                    </Col>
                    <Col md={6} className="mb-3">
                      <div className="stat-item text-center p-3 rounded bg-success text-white">
                        <h4 className="mb-1">{dashboardData.spendingAnalytics.avgDaily.toFixed(2)} TEO</h4>
                        <small>Media Giornaliera</small>
                      </div>
                    </Col>
                  </Row>
                )}
              </div>
            </Tab>
            
            <Tab eventKey="achievements" title={
              <span><i className="feather icon-award me-2"></i>Obiettivi</span>
            }>
              <div className="achievements-detail mt-4">
                <div className="achievements-list">
                  {dashboardData.achievements.map(achievement => (
                    <div key={achievement.id} className="achievement-card p-3 mb-3 rounded border">
                      <div className="d-flex align-items-center">
                        <div 
                          className={`achievement-icon-large me-3 ${achievement.completed ? 'completed' : 'incomplete'}`}
                          style={{ color: achievement.color }}
                        >
                          <i className={`feather icon-${achievement.icon}`}></i>
                        </div>
                        <div className="flex-grow-1">
                          <h6 className={`mb-1 ${achievement.completed ? 'text-dark' : 'text-muted'}`}>
                            {achievement.title}
                          </h6>
                          <p className="mb-2 text-muted small">{achievement.description}</p>
                          {!achievement.completed && achievement.progress && (
                            <div>
                              <ProgressBar 
                                now={achievement.progress} 
                                className="mb-1"
                                style={{ height: '8px' }}
                              />
                              <small className="text-muted">{achievement.progress.toFixed(1)}% completato</small>
                            </div>
                          )}
                        </div>
                        <div>
                          {achievement.completed ? (
                            <Badge variant="success">Completato</Badge>
                          ) : (
                            <Badge variant="secondary">In Corso</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Tab>
          </Tabs>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default EnhancedStudentTeoCoinDashboard;
