import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Button, Row, Col, Table } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import './AdminTeoCoinDashboard.scss';

/**
 * AdminTeoCoinDashboard - DB-based TeoCoin dashboard for administrators
 * Provides platform-wide statistics and user management
 */
const DBAdminTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    statistics: {},
    recentTransactions: [],
    pendingWithdrawals: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Auto-refresh interval (15 seconds for admin dashboard)
  const REFRESH_INTERVAL = 15000;

  useEffect(() => {
    loadDashboardData();
    
    // Set up auto-refresh
    const interval = setInterval(loadDashboardData, REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Load platform statistics
      const statsResponse = await fetch('/api/v1/teocoin/statistics/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!statsResponse.ok) {
        throw new Error('Failed to fetch platform statistics');
      }

      const statsData = await statsResponse.json();

      // Load admin-specific data (pending withdrawals, etc.)
      const adminResponse = await fetch('/api/v1/teocoin/admin/platform/stats/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const adminData = adminResponse.ok ? await adminResponse.json() : {};

      setDashboardData({
        statistics: { ...statsData, ...adminData },
        recentTransactions: adminData.recent_transactions || [],
        pendingWithdrawals: adminData.pending_withdrawals || []
      });

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading admin dashboard data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
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

  const formatTeoCoin = (amount) => {
    return parseFloat(amount || 0).toFixed(2);
  };

  if (loading && !dashboardData.statistics.total_users_with_balance) {
    return (
      <Card className="admin-teocoin-dashboard-card">
        <Card.Body className="text-center">
          <Spinner animation="border" variant="primary" />
          <p className="mt-2">Caricamento dashboard amministratore...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="admin-teocoin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h4>
          <i className="fas fa-crown"></i>
          Dashboard Admin TeoCoin
          <Badge bg="danger" className="ms-2">Admin</Badge>
          <Badge bg="success" className="ms-1">DB-Based</Badge>
        </h4>
        {lastUpdate && (
          <small className="text-muted">
            Ultimo aggiornamento: {formatDate(lastUpdate)}
          </small>
        )}
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <Alert.Heading>Errore</Alert.Heading>
          {error}
        </Alert>
      )}

      {/* Platform Statistics */}
      <Row className="mb-4">
        <Col lg={3} md={6}>
          <Card className="stat-card text-center">
            <Card.Body>
              <div className="stat-icon">
                <i className="fas fa-users text-primary"></i>
              </div>
              <h3>{dashboardData.statistics.total_users_with_balance || 0}</h3>
              <p className="text-muted">Utenti con Saldo</p>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6}>
          <Card className="stat-card text-center">
            <Card.Body>
              <div className="stat-icon">
                <i className="fas fa-coins text-warning"></i>
              </div>
              <h3>{formatTeoCoin(dashboardData.statistics.total_available_balance)} TEO</h3>
              <p className="text-muted">TEO in Circolazione</p>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6}>
          <Card className="stat-card text-center">
            <Card.Body>
              <div className="stat-icon">
                <i className="fas fa-lock text-success"></i>
              </div>
              <h3>{formatTeoCoin(dashboardData.statistics.total_staked_balance)} TEO</h3>
              <p className="text-muted">TEO in Staking</p>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6}>
          <Card className="stat-card text-center">
            <Card.Body>
              <div className="stat-icon">
                <i className="fas fa-exchange-alt text-info"></i>
              </div>
              <h3>{dashboardData.statistics.total_transactions || 0}</h3>
              <p className="text-muted">Transazioni Totali</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        {/* Supply Overview */}
        <Col lg={8}>
          <Card className="supply-card mb-3">
            <Card.Header>
              <h5>💰 Distribuzione TEO</h5>
              <Button 
                variant="outline-primary" 
                size="sm"
                onClick={loadDashboardData}
                disabled={loading}
              >
                {loading ? (
                  <Spinner animation="border" size="sm" />
                ) : (
                  <i className="fas fa-sync-alt"></i>
                )}
                Aggiorna
              </Button>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={4}>
                  <div className="supply-item">
                    <div className="supply-label">Disponibile</div>
                    <div className="supply-value text-primary">
                      {formatTeoCoin(dashboardData.statistics.total_available_balance)} TEO
                    </div>
                    <div className="supply-percentage">
                      {dashboardData.statistics.total_available_balance && dashboardData.statistics.total_staked_balance ? 
                        ((parseFloat(dashboardData.statistics.total_available_balance) / 
                          (parseFloat(dashboardData.statistics.total_available_balance) + 
                           parseFloat(dashboardData.statistics.total_staked_balance))) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="supply-item">
                    <div className="supply-label">In Staking</div>
                    <div className="supply-value text-warning">
                      {formatTeoCoin(dashboardData.statistics.total_staked_balance)} TEO
                    </div>
                    <div className="supply-percentage">
                      {dashboardData.statistics.total_available_balance && dashboardData.statistics.total_staked_balance ? 
                        ((parseFloat(dashboardData.statistics.total_staked_balance) / 
                          (parseFloat(dashboardData.statistics.total_available_balance) + 
                           parseFloat(dashboardData.statistics.total_staked_balance))) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="supply-item">
                    <div className="supply-label">In Prelievo</div>
                    <div className="supply-value text-secondary">
                      {formatTeoCoin(dashboardData.statistics.total_pending_withdrawal)} TEO
                    </div>
                    <div className="supply-percentage">
                      <Badge bg="info">{dashboardData.statistics.pending_withdrawal_requests || 0} richieste</Badge>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>

        {/* System Health */}
        <Col lg={4}>
          <Card className="health-card mb-3">
            <Card.Header>
              <h5>🔧 Stato Sistema</h5>
            </Card.Header>
            <Card.Body>
              <div className="health-items">
                <div className="health-item">
                  <i className="fas fa-database text-success"></i>
                  <span>Database</span>
                  <Badge bg="success">Online</Badge>
                </div>
                <div className="health-item">
                  <i className="fas fa-bolt text-warning"></i>
                  <span>Transazioni</span>
                  <Badge bg="success">Istantanee</Badge>
                </div>
                <div className="health-item">
                  <i className="fas fa-shield-alt text-primary"></i>
                  <span>Sicurezza</span>
                  <Badge bg="success">Attiva</Badge>
                </div>
                <div className="health-item">
                  <i className="fas fa-wallet text-info"></i>
                  <span>MetaMask</span>
                  <Badge bg="success">Supportato</Badge>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Pending Withdrawals */}
      {dashboardData.pendingWithdrawals && dashboardData.pendingWithdrawals.length > 0 && (
        <Card className="withdrawals-card mb-3">
          <Card.Header>
            <h5>📤 Prelievi in Attesa</h5>
            <Badge bg="warning">{dashboardData.pendingWithdrawals.length}</Badge>
          </Card.Header>
          <Card.Body>
            <Table responsive striped>
              <thead>
                <tr>
                  <th>Utente</th>
                  <th>Importo</th>
                  <th>Indirizzo</th>
                  <th>Data Richiesta</th>
                  <th>Stato</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.pendingWithdrawals.map((withdrawal, index) => (
                  <tr key={withdrawal.id || index}>
                    <td>{withdrawal.user_email || withdrawal.user_id}</td>
                    <td>{formatTeoCoin(withdrawal.amount)} TEO</td>
                    <td>
                      <code>{withdrawal.wallet_address ? 
                        `${withdrawal.wallet_address.slice(0, 8)}...${withdrawal.wallet_address.slice(-6)}` : 
                        'N/A'
                      }</code>
                    </td>
                    <td>{formatDate(withdrawal.created_at)}</td>
                    <td>
                      <Badge bg="warning">{withdrawal.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}

      {/* System Benefits */}
      <Card className="benefits-card">
        <Card.Body>
          <h6>🎯 Vantaggi Sistema DB per Admin</h6>
          <Row>
            <Col md={3}>
              <div className="benefit-item">
                <i className="fas fa-chart-line text-success"></i>
                <strong>Analytics Real-time</strong>
                <small>Statistiche istantanee</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item">
                <i className="fas fa-tools text-primary"></i>
                <strong>Controllo Totale</strong>
                <small>Gestione diretta</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item">
                <i className="fas fa-dollar-sign text-warning"></i>
                <strong>Zero Costi</strong>
                <small>Nessuna gas fee</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item">
                <i className="fas fa-lightning text-info"></i>
                <strong>Performance</strong>
                <small>Operazioni immediate</small>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
};

export default DBAdminTeoCoinDashboard;
