/**
 * 💸 Platform Withdrawal Component
 * 
 * Handles Platform → MetaMask balance transfers
 * Shows withdrawal history and status
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Modal, Form, Alert, Table, Badge } from 'react-bootstrap';
import stakingService from '../../services/stakingService';

const PlatformWithdrawal = ({ onWithdrawalComplete }) => {
  const [stakingInfo, setStakingInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [walletAddress, setWalletAddress] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Mock withdrawal history
  const [withdrawals] = useState([
    { id: 1, amount: 100, status: 'Pending', date: '2024-01-15', address: '0x1234...5678' },
    { id: 2, amount: 50, status: 'Completed', date: '2024-01-10', address: '0x1234...5678' }
  ]);

  useEffect(() => {
    loadBalanceData();
  }, []);

  const loadBalanceData = async () => {
    try {
      setLoading(true);
      const response = await stakingService.getStakingInfo();
      setStakingInfo(response);
    } catch (err) {
      console.error('Error loading balance data:', err);
      setError('Failed to load balance information');
    } finally {
      setLoading(false);
    }
  };

  const handleWithdrawal = async () => {
    if (!withdrawalAmount || parseFloat(withdrawalAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (!walletAddress) {
      setError('Please enter your MetaMask wallet address');
      return;
    }

    if (parseFloat(withdrawalAmount) > (stakingInfo?.current_balance || 0)) {
      setError('Insufficient platform balance');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      // TODO: Replace with actual withdrawal API call
      // POST /api/v1/withdrawals/create/ { amount: withdrawalAmount, wallet_address: walletAddress }
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setSuccess(`Withdrawal request for ${withdrawalAmount} TEO submitted successfully! You will receive tokens at ${walletAddress} after admin approval.`);
      setWithdrawalAmount('');
      setWalletAddress('');
      setShowModal(false);
      
      // Reload balance data
      await loadBalanceData();
      
      if (onWithdrawalComplete) {
        onWithdrawalComplete();
      }
      
    } catch (error) {
      console.error('Withdrawal error:', error);
      setError('Failed to submit withdrawal request. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'Pending': 'warning',
      'Completed': 'success',
      'Cancelled': 'danger',
      'Processing': 'info'
    };
    return <Badge bg={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const platformBalance = stakingInfo?.current_balance || 0;

  if (loading) {
    return (
      <Card className="platform-withdrawal-card">
        <Card.Header className="bg-gradient-info text-white">
          <h5 className="mb-0">
            <i className="feather icon-arrow-up-right me-2"></i>
            Withdraw to MetaMask
          </h5>
        </Card.Header>
        <Card.Body className="text-center p-4">
          <div className="spinner-border text-info" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-muted">Loading withdrawal information...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <>
      <Card className="platform-withdrawal-card">
        <Card.Header className="bg-gradient-info text-white">
          <h5 className="mb-0">
            <i className="feather icon-arrow-up-right me-2"></i>
            Withdraw to MetaMask
            <span className="badge bg-light text-dark ms-2">Platform → MetaMask</span>
          </h5>
        </Card.Header>

        <Card.Body>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError('')}>
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          )}
          {success && (
            <Alert variant="success" dismissible onClose={() => setSuccess('')}>
              <i className="feather icon-check-circle me-2"></i>
              {success}
            </Alert>
          )}

          {/* Platform Balance Display */}
          <div className="text-center p-3 bg-light rounded mb-4">
            <h4 className="text-primary mb-1">{formatAmount(platformBalance)} TEO</h4>
            <p className="text-muted mb-0">Available for Withdrawal</p>
          </div>

          {/* Withdrawal Button */}
          <div className="d-grid mb-4">
            <Button 
              variant="info" 
              size="lg"
              onClick={() => setShowModal(true)}
              disabled={platformBalance <= 0}
            >
              <i className="feather icon-arrow-up-right me-2"></i>
              Request Withdrawal
            </Button>
          </div>

          {/* Withdrawal History */}
          <h6 className="mb-3">Recent Withdrawals</h6>
          {withdrawals.length > 0 ? (
            <Table responsive size="sm">
              <thead>
                <tr>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Address</th>
                </tr>
              </thead>
              <tbody>
                {withdrawals.map((withdrawal) => (
                  <tr key={withdrawal.id}>
                    <td>{formatAmount(withdrawal.amount)} TEO</td>
                    <td>{getStatusBadge(withdrawal.status)}</td>
                    <td>{withdrawal.date}</td>
                    <td>
                      <small className="text-muted">{withdrawal.address}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <div className="text-center py-3">
              <i className="feather icon-arrow-up-right text-muted" style={{ fontSize: '2rem' }}></i>
              <p className="text-muted mt-2">No withdrawal history</p>
            </div>
          )}

          <div className="alert alert-warning">
            <i className="feather icon-clock me-2"></i>
            <strong>Note:</strong> Withdrawals require admin approval and may take 24-48 hours to process.
          </div>
        </Card.Body>
      </Card>

      {/* Withdrawal Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-arrow-up-right me-2"></i>
            Request Withdrawal
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Withdrawal Amount</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                min="0"
                max={platformBalance}
                step="0.01"
              />
              <Form.Text className="text-muted">
                Available: {formatAmount(platformBalance)} TEO
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>MetaMask Wallet Address</Form.Label>
              <Form.Control
                type="text"
                placeholder="0x..."
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
              />
              <Form.Text className="text-muted">
                Enter your MetaMask wallet address to receive tokens
              </Form.Text>
            </Form.Group>

            <div className="alert alert-info">
              <i className="feather icon-info me-2"></i>
              <strong>Processing Time:</strong> Withdrawals are processed manually and may take 24-48 hours.
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="info" 
            onClick={handleWithdrawal}
            disabled={processing || !withdrawalAmount || !walletAddress}
          >
            {processing ? (
              <>
                <i className="feather icon-clock me-2"></i>
                Submitting...
              </>
            ) : (
              <>
                <i className="feather icon-arrow-up-right me-1"></i>
                Submit Request
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default PlatformWithdrawal;
