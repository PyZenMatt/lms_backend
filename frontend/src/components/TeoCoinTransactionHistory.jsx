import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Spinner, Alert } from 'react-bootstrap';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const TeoCoinTransactionHistory = ({ limit = 5 }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');

      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/transactions/history/?limit=${limit}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch transactions: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setTransactions(data.transactions || []);
      } else {
        throw new Error(data.error || 'Failed to load transactions');
      }
    } catch (err) {
      console.error('Transaction fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [limit]);

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'reward':
        return <i className="feather icon-award text-success"></i>;
      case 'discount':
        return <i className="feather icon-percent text-primary"></i>;
      case 'withdrawal':
        return <i className="feather icon-send text-warning"></i>;
      case 'deposit':
        return <i className="feather icon-download text-info"></i>;
      default:
        return <i className="feather icon-activity text-muted"></i>;
    }
  };

  const getTransactionBadge = (type) => {
    const badges = {
      reward: { variant: 'success', text: 'Reward' },
      discount: { variant: 'primary', text: 'Discount' },
      withdrawal: { variant: 'warning', text: 'Withdrawal' },
      deposit: { variant: 'info', text: 'Deposit' },
      default: { variant: 'secondary', text: type || 'Transaction' }
    };

    const badge = badges[type] || badges.default;
    return <Badge bg={badge.variant}>{badge.text}</Badge>;
  };

  return (
    <Card className="border-0 shadow-sm">
      <Card.Header className="bg-light border-0">
        <Card.Title as="h5" className="mb-1 d-flex align-items-center">
          <i className="feather icon-list me-2"></i>
          Recent TeoCoin Activity
        </Card.Title>
      </Card.Header>
      <Card.Body>
        {error && (
          <Alert variant="danger" className="mb-3">
            <i className="feather icon-alert-circle me-2"></i>
            {error}
          </Alert>
        )}

        {loading ? (
          <div className="text-center py-4">
            <Spinner animation="border" className="me-2" />
            <span className="text-muted">Loading transactions...</span>
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-4">
            <i className="feather icon-activity text-muted" style={{ fontSize: '3rem' }}></i>
            <p className="text-muted mt-3">No transactions yet</p>
            <p className="text-muted small">Start earning TeoCoin by completing exercises!</p>
          </div>
        ) : (
          <Table responsive className="mb-0">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>Type</th>
                <th>Description</th>
                <th style={{ width: '100px' }} className="text-end">
                  Amount
                </th>
                <th style={{ width: '120px' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction, index) => (
                <tr key={transaction.id || index}>
                  <td className="text-center">{getTransactionIcon(transaction.type)}</td>
                  <td>
                    <div>
                      <span className="fw-medium">{transaction.description}</span>
                      <div className="mt-1">{getTransactionBadge(transaction.type)}</div>
                    </div>
                  </td>
                  <td className="text-end">
                    <span
                      className={
                        transaction.type === 'withdrawal'
                          ? 'text-warning'
                          : transaction.type === 'discount'
                            ? 'text-primary'
                            : 'text-success'
                      }
                    >
                      {transaction.type === 'withdrawal' ? '-' : '+'}
                      {formatAmount(Math.abs(transaction.amount))} TEO
                    </span>
                  </td>
                  <td className="text-muted small">{formatDate(transaction.created_at || transaction.date)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card.Body>
    </Card>
  );
};

export default TeoCoinTransactionHistory;
