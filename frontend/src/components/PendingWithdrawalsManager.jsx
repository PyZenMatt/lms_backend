import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Badge, Alert, Modal, Spinner } from 'react-bootstrap';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const PendingWithdrawalsManager = ({ onWithdrawalCancelled }) => {
  const [pendingWithdrawals, setPendingWithdrawals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [withdrawalToCancel, setWithdrawalToCancel] = useState(null);

  const fetchPendingWithdrawals = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');

      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/history/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch withdrawals: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        const pending = data.withdrawals?.filter((w) => w.status === 'pending' || w.status === 'processing') || [];
        setPendingWithdrawals(pending);
      } else {
        throw new Error(data.error || 'Failed to load pending withdrawals');
      }
    } catch (err) {
      console.error('Pending withdrawals fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingWithdrawals();
  }, []);

  const handleCancelWithdrawal = async () => {
    if (!withdrawalToCancel) return;

    try {
      setCancelling(withdrawalToCancel.id);
      const token = localStorage.getItem('accessToken');

      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/legacy/withdraw/${withdrawalToCancel.id}/cancel/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to cancel withdrawal: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        // Refresh pending withdrawals
        await fetchPendingWithdrawals();
        // Notify parent component
        if (onWithdrawalCancelled) {
          onWithdrawalCancelled(data.amount_returned);
        }
        setShowCancelModal(false);
        setWithdrawalToCancel(null);
      } else {
        throw new Error(data.error || 'Failed to cancel withdrawal');
      }
    } catch (err) {
      console.error('Cancel withdrawal error:', err);
      setError(err.message);
    } finally {
      setCancelling(null);
    }
  };

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

  if (pendingWithdrawals.length === 0 && !loading) {
    return null; // Don't show anything if no pending withdrawals
  }

  return (
    <>
      <Card className="border-warning shadow-sm mb-3">
        <Card.Header className="bg-warning text-dark border-0">
          <Card.Title as="h6" className="mb-0 d-flex align-items-center">
            <i className="feather icon-clock me-2"></i>
            Pending Withdrawals ({pendingWithdrawals.length}/3)
          </Card.Title>
        </Card.Header>
        <Card.Body>
          {error && (
            <Alert variant="danger" className="mb-3">
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          )}

          {pendingWithdrawals.length >= 3 && (
            <Alert variant="warning" className="mb-3">
              <i className="feather icon-alert-triangle me-2"></i>
              <strong>Withdrawal limit reached!</strong> Cancel some pending withdrawals to create new ones.
            </Alert>
          )}

          {loading ? (
            <div className="text-center py-3">
              <Spinner animation="border" size="sm" className="me-2" />
              <span className="text-muted">Loading pending withdrawals...</span>
            </div>
          ) : (
            <Table responsive size="sm" className="mb-0">
              <thead>
                <tr>
                  <th>Amount</th>
                  <th>To Address</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th style={{ width: '80px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {pendingWithdrawals.map((withdrawal) => (
                  <tr key={withdrawal.id}>
                    <td className="fw-medium">{formatAmount(withdrawal.amount)} TEO</td>
                    <td className="font-monospace small">{withdrawal.wallet_address?.substring(0, 10)}...</td>
                    <td className="text-muted small">{formatDate(withdrawal.created_at)}</td>
                    <td>
                      <Badge bg={withdrawal.status === 'pending' ? 'warning' : 'info'}>{withdrawal.status}</Badge>
                    </td>
                    <td>
                      {withdrawal.status === 'pending' && (
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => {
                            setWithdrawalToCancel(withdrawal);
                            setShowCancelModal(true);
                          }}
                          disabled={cancelling === withdrawal.id}
                        >
                          {cancelling === withdrawal.id ? <Spinner animation="border" size="sm" /> : <i className="feather icon-x"></i>}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Cancel Confirmation Modal */}
      <Modal show={showCancelModal} onHide={() => setShowCancelModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Cancel Withdrawal</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {withdrawalToCancel && (
            <div>
              <p>Are you sure you want to cancel this withdrawal?</p>
              <div className="bg-light p-3 rounded">
                <div className="row">
                  <div className="col-sm-4">
                    <strong>Amount:</strong>
                  </div>
                  <div className="col-sm-8">{formatAmount(withdrawalToCancel.amount)} TEO</div>
                </div>
                <div className="row">
                  <div className="col-sm-4">
                    <strong>To Address:</strong>
                  </div>
                  <div className="col-sm-8 font-monospace small">{withdrawalToCancel.wallet_address}</div>
                </div>
                <div className="row">
                  <div className="col-sm-4">
                    <strong>Created:</strong>
                  </div>
                  <div className="col-sm-8">{formatDate(withdrawalToCancel.created_at)}</div>
                </div>
              </div>
              <Alert variant="info" className="mt-3 mb-0">
                <i className="feather icon-info me-2"></i>
                The TEO amount will be returned to your available balance.
              </Alert>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCancelModal(false)}>
            Keep Withdrawal
          </Button>
          <Button variant="danger" onClick={handleCancelWithdrawal} disabled={cancelling}>
            {cancelling ? <Spinner animation="border" size="sm" className="me-2" /> : null}
            Cancel Withdrawal
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default PendingWithdrawalsManager;
