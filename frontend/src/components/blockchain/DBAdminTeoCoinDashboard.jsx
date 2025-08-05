import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Table } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

const DBAdminTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    statistics: {},
    recentTransactions: [],
    pendingWithdrawals: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 15000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access');
      if (!token) throw new Error('No authentication token found');
      const statsResponse = await fetch('/api/v1/teocoin/statistics/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!statsResponse.ok) throw new Error('Failed to fetch platform statistics');
      const statsData = await statsResponse.json();
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
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
  const formatTeoCoin = (amount) => parseFloat(amount || 0).toFixed(2);

  if (loading) {
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
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <Alert.Heading>Errore</Alert.Heading>
          {error}
        </Alert>
      )}
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
    </div>
  );
};

export default DBAdminTeoCoinDashboard;
