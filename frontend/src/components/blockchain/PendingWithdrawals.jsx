/**
 * TeoCoin Pending Withdrawals Component
 * Shows user's pending withdrawals and allows real-time processing
 */
import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const PendingWithdrawals = ({ onTransactionComplete = null }) => {
  const [pendingWithdrawals, setPendingWithdrawals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState({});
  const [results, setResults] = useState({});
  const [error, setError] = useState('');

  // Load pending withdrawals
  const loadPendingWithdrawals = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/pending/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setPendingWithdrawals(data.pending_withdrawals || []);
      } else {
        setError(data.error || 'Error loading pending withdrawals');
      }
    } catch (err) {
      console.error('Error loading pending withdrawals:', err);
      setError('Network error loading withdrawals');
    } finally {
      setLoading(false);
    }
  };

  // Process a specific withdrawal
  const processWithdrawal = async (withdrawalId) => {
    setProcessing(prev => ({ ...prev, [withdrawalId]: true }));
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/${withdrawalId}/process/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Success! Show transaction details
        setResults(prev => ({
          ...prev,
          [withdrawalId]: {
            success: true,
            transaction_hash: data.transaction_hash,
            gas_used: data.gas_used,
            amount_minted: data.amount_minted,
            message: data.message
          }
        }));

        // Remove from pending list
        setPendingWithdrawals(prev => 
          prev.filter(w => w.id !== withdrawalId)
        );

        // Callback to parent component
        if (onTransactionComplete) {
          onTransactionComplete(data);
        }

      } else {
        // Error during processing
        setResults(prev => ({
          ...prev,
          [withdrawalId]: {
            success: false,
            error: data.error || 'Processing failed'
          }
        }));
      }
    } catch (err) {
      console.error('Error processing withdrawal:', err);
      setResults(prev => ({
        ...prev,
        [withdrawalId]: {
          success: false,
          error: 'Network error during processing'
        }
      }));
    } finally {
      setProcessing(prev => ({ ...prev, [withdrawalId]: false }));
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadPendingWithdrawals();
  }, []);

  if (loading) {
    return (
      <div className="card">
        <div className="card-body text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Loading pending withdrawals...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="alert alert-danger">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </div>
          <button 
            className="btn btn-outline-primary"
            onClick={loadPendingWithdrawals}
          >
            <i className="fas fa-redo me-2"></i>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (pendingWithdrawals.length === 0) {
    return (
      <div className="card">
        <div className="card-body text-center">
          <i className="fas fa-check-circle text-success mb-3" style={{ fontSize: '3rem' }}></i>
          <h5>No Pending Withdrawals</h5>
          <p className="text-muted">All your withdrawals have been processed!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h5 className="mb-0">
          <i className="fas fa-clock text-warning me-2"></i>
          Pending Withdrawals ({pendingWithdrawals.length})
        </h5>
        <button 
          className="btn btn-sm btn-outline-secondary"
          onClick={loadPendingWithdrawals}
          disabled={loading}
        >
          <i className="fas fa-sync-alt me-1"></i>
          Refresh
        </button>
      </div>
      <div className="card-body">
        <div className="alert alert-info">
          <i className="fas fa-info-circle me-2"></i>
          <strong>Ready to mint!</strong> Click "Process Withdrawal" to mint TeoCoin tokens directly to your MetaMask wallet.
        </div>
        
        {pendingWithdrawals.map((withdrawal) => (
          <div key={withdrawal.id} className="border rounded p-3 mb-3">
            <div className="row align-items-center">
              <div className="col-md-8">
                <div className="d-flex align-items-center mb-2">
                  <span className="badge bg-warning text-dark me-2">PENDING</span>
                  <strong>{withdrawal.amount} TEO</strong>
                </div>
                <p className="text-muted mb-1">
                  <i className="fas fa-wallet me-1"></i>
                  To: <code>{withdrawal.metamask_address}</code>
                </p>
                <p className="text-muted mb-0">
                  <i className="fas fa-calendar me-1"></i>
                  Requested: {new Date(withdrawal.created_at).toLocaleString()}
                </p>
              </div>
              <div className="col-md-4 text-end">
                {processing[withdrawal.id] ? (
                  <div className="text-center">
                    <div className="spinner-border text-primary mb-2" role="status">
                      <span className="visually-hidden">Processing...</span>
                    </div>
                    <p className="text-primary mb-0">
                      <i className="fas fa-cog fa-spin me-1"></i>
                      Minting tokens...
                    </p>
                  </div>
                ) : results[withdrawal.id] ? (
                  <div className="text-center">
                    {results[withdrawal.id].success ? (
                      <div className="text-success">
                        <i className="fas fa-check-circle mb-2" style={{ fontSize: '2rem' }}></i>
                        <p className="mb-1"><strong>✅ Minted!</strong></p>
                        <p className="mb-1">
                          <small>TX: {results[withdrawal.id].transaction_hash?.substring(0, 10)}...</small>
                        </p>
                        <p className="mb-0">
                          <small>Gas: {results[withdrawal.id].gas_used}</small>
                        </p>
                      </div>
                    ) : (
                      <div className="text-danger">
                        <i className="fas fa-times-circle mb-2" style={{ fontSize: '2rem' }}></i>
                        <p className="mb-0"><strong>❌ Failed</strong></p>
                        <small>{results[withdrawal.id].error}</small>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    className="btn btn-primary"
                    onClick={() => processWithdrawal(withdrawal.id)}
                  >
                    <i className="fas fa-play me-2"></i>
                    Process Withdrawal
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PendingWithdrawals;
