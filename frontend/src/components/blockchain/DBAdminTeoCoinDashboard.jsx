import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Table } from '@/components/ui/legacy-shims';
import PendingWithdrawals from './PendingWithdrawals';
import BurnDepositInterface from './BurnDepositInterface';
import { useAuth } from '../../contexts/AuthContext';

const DBAdminTeoCoinDashboard = ({ onWithdrawalClick }) => {
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
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access');
      if (!token) throw new Error('No authentication token found');
      const statsResponse = await fetch('/teocoin/statistics/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!statsResponse.ok) throw new Error('Failed to fetch platform statistics');
      const statsData = await statsResponse.json();
      const adminResponse = await fetch('/teocoin/admin/platform/stats/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
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

  const formatDate = (dateString) =>
    new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
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
      <button className="btn btn-primary mb-3" onClick={loadDashboardData} disabled={loading}>
        {loading ? 'Aggiornamento...' : 'Aggiorna'}
      </button>
      <PendingWithdrawals />
      <BurnDepositInterface />
      <TeoCoinBalanceWidget onWithdrawalClick={onWithdrawalClick} />
    </div>
  );
};

export default DBAdminTeoCoinDashboard;
