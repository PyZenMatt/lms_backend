/* @ts-nocheck */
/**
 * TeoCoin Pending Withdrawals Component
 * Shows user's pending withdrawals and allows real-time processing
 */
import React, { useState, useEffect } from 'react';
import api from '../../services/core/axiosClient';

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
      console.log('🔄 Loading pending withdrawals...');

      const response = await api.get('/teocoin/withdrawals/pending/');
      console.log('📊 Pending withdrawals response:', response.data);

      if (response.data.success && Array.isArray(response.data.pending_withdrawals)) {
        setPendingWithdrawals(response.data.pending_withdrawals);
        setError('');
        console.log(`✅ Loaded ${response.data.pending_withdrawals.length} pending withdrawals`);
      } else if (
        response.data.success === false &&
        Array.isArray(response.data.pending_withdrawals) &&
        response.data.pending_withdrawals.length === 0
      ) {
        setPendingWithdrawals([]);
        setError('');
        console.log('ℹ️ No pending withdrawals found');
      } else {
        const errorMsg = response.data.error || 'Error loading pending withdrawals';
        setError(errorMsg);
        console.error('❌ Error in response:', errorMsg);
      }
    } catch (err) {
      console.error('❌ Error loading pending withdrawals:', err);
      console.error('Response data:', err.response?.data);
      console.error('Response status:', err.response?.status);

      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Network error loading withdrawals');
      }
    } finally {
      setLoading(false);
    }
  };

  // Process a specific withdrawal
  const processWithdrawal = async (withdrawalId) => {
    setProcessing((prev) => ({ ...prev, [withdrawalId]: true }));
    setError('');

    try {
      console.log(`🎯 Processing withdrawal ${withdrawalId}...`);

      const response = await api.post(`/teocoin/withdrawals/${withdrawalId}/process/`, {});
      console.log(`📤 Process withdrawal response:`, response.data);

      if (response.data.success) {
        // Success! Show transaction details
        setResults((prev) => ({
          ...prev,
          [withdrawalId]: {
            success: true,
            transaction_hash: response.data.transaction_hash,
            gas_used: response.data.gas_used,
            amount_minted: response.data.amount_minted,
            message: response.data.message
          }
        }));

        // Remove from pending list
        setPendingWithdrawals((prev) => prev.filter((w) => w.id !== withdrawalId));

        console.log(`✅ Withdrawal ${withdrawalId} processed successfully`);

        // Callback to parent component
        if (onTransactionComplete) {
          onTransactionComplete(response.data);
        }
      } else {
        // Error during processing
        const errorMsg = response.data.error || 'Processing failed';
        setResults((prev) => ({
          ...prev,
          [withdrawalId]: {
            success: false,
            error: errorMsg
          }
        }));
        console.error(`❌ Withdrawal ${withdrawalId} processing failed:`, errorMsg);
      }
    } catch (err) {
      console.error(`❌ Error processing withdrawal ${withdrawalId}:`, err);
      console.error('Response data:', err.response?.data);
      console.error('Response status:', err.response?.status);

      const errorMsg = err.response?.data?.error || 'Network error during processing';
      setResults((prev) => ({
        ...prev,
        [withdrawalId]: {
          success: false,
          error: 'Network error during processing'
        }
      }));
    } finally {
      setProcessing((prev) => ({ ...prev, [withdrawalId]: false }));
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadPendingWithdrawals();
  }, []);

  if (loading) {
    return (
      <div className="bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm">
        <div className="p-4 text-center">
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
      <div className="bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm">
        <div className="p-4">
          <div className="border rounded-md p-3 bg-muted text-muted-foreground bg-destructive/15 border-destructive text-destructive-foreground">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </div>
          <button className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-outline-primary" onClick={loadPendingWithdrawals}>
            <i className="fas fa-redo me-2"></i>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (pendingWithdrawals.length === 0) {
    return (
      <div className="bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm">
        <div className="p-4 text-center">
          <i className="fas fa-check-circle text-success mb-3" style={{ fontSize: '3rem' }}></i>
          <h5>No Pending Withdrawals</h5>
          <p className="text-muted">All your withdrawals have been processed!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm">
      <div className="px-4 py-2 border-b border-border d-flex justify-content-between align-items-center">
        <h5 className="mb-0">
          <i className="fas fa-clock text-warning me-2"></i>
          Pending Withdrawals ({pendingWithdrawals.length})
        </h5>
        <button className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-sm inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-outline-secondary" onClick={loadPendingWithdrawals} disabled={loading}>
          <i className="fas fa-sync-alt me-1"></i>
          Refresh
        </button>
      </div>
      <div className="p-4">
        <div className="border rounded-md p-3 bg-muted text-muted-foreground bg-info/15 border-info text-info-foreground">
          <i className="fas fa-info-circle me-2"></i>
          <strong>Ready to mint!</strong> Click "Process Withdrawal" to mint TeoCoin tokens directly to your MetaMask wallet.
        </div>

        {pendingWithdrawals.map((withdrawal) => (
          <div key={withdrawal.id} className="border rounded p-3 mb-3">
            <div className="row align-items-center">
              <div className="col-md-8">
                <div className="d-flex align-items-center mb-2">
                  <span className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground bg-warning text-dark me-2">PENDING</span>
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
                        <p className="mb-1">
                          <strong>✅ Minted!</strong>
                        </p>
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
                        <p className="mb-0">
                          <strong>❌ Failed</strong>
                        </p>
                        <small>{results[withdrawal.id].error}</small>
                      </div>
                    )}
                  </div>
                ) : (
                  <button className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground bg-primary text-primary-foreground" onClick={() => processWithdrawal(withdrawal.id)}>
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
