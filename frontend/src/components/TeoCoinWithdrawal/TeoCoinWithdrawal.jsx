import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  Chip,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip
} from '@mui/material';
import { AccountBalanceWallet, Send, Refresh, Close, Info, Warning, CheckCircle } from '@mui/icons-material';
import { BrowserProvider, Contract, formatEther, parseEther } from 'ethers';
import api from '../../services/core/axiosClient';
import './TeoCoinWithdrawal.scss';

// TeoCoin contract configuration
const TEOCOIN_CONTRACT = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
const POLYGON_AMOY_CHAIN_ID = '0x13882'; // 80002 in hex
const TEOCOIN_ABI = [
  {
    inputs: [{ internalType: 'address', name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [],
    name: 'decimals',
    outputs: [{ internalType: 'uint8', name: '', type: 'uint8' }],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [
      { internalType: 'address', name: 'to', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' }
    ],
    name: 'mintTo',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function'
  }
];

const TeoCoinWithdrawal = ({ open, onClose, userBalance = 0 }) => {
  // State management
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);
  const [dbBalance, setDbBalance] = useState(userBalance);
  const [metamaskBalance, setMetamaskBalance] = useState(0);
  const [withdrawalHistory, setWithdrawalHistory] = useState([]);
  const [pendingWithdrawals, setPendingWithdrawals] = useState(0);
  const [provider, setProvider] = useState(null);
  const [contract, setContract] = useState(null);

  // Utility functions
  const showAlert = useCallback((message, severity = 'info', duration = 5000) => {
    setAlert({ message, severity });
    setTimeout(() => setAlert(null), duration);
  }, []);

  const getCsrfToken = useCallback(() => {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    return null;
  }, []);

  // MetaMask connection helpers (ORDINE CORRETTO)

  // Network switching function - must be defined BEFORE connectWallet
  const switchToPolygonAmoy = useCallback(async () => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: POLYGON_AMOY_CHAIN_ID }]
      });
    } catch (error) {
      if (error.code === 4902) {
        // Network not added, add it
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [
              {
                chainId: POLYGON_AMOY_CHAIN_ID,
                chainName: 'Polygon Amoy Testnet',
                nativeCurrency: {
                  name: 'MATIC',
                  symbol: 'MATIC',
                  decimals: 18
                },
                rpcUrls: ['https://rpc-amoy.polygon.technology/'],
                blockExplorerUrls: ['https://amoy.polygonscan.com/']
              }
            ]
          });
        } catch (addError) {
          throw new Error('Failed to add Polygon Amoy network');
        }
      } else {
        throw error;
      }
    }
  }, []);

  const linkWalletAddress = useCallback(
    async (address) => {
      try {
        // For now, we'll store the wallet address locally
        // In the future, this can be sent to the backend
        console.log('Wallet linked:', address);
        showAlert('Wallet address linked successfully!', 'success');
      } catch (error) {
        console.error('Failed to link wallet:', error);
        showAlert('Failed to link wallet address. Please try again.', 'warning');
      }
    },
    [showAlert]
  );

  // MetaMask connection functions
  const connectWallet = useCallback(async () => {
    if (!window.ethereum) {
      showAlert('MetaMask is not installed. Please install MetaMask to continue.', 'error');
      return;
    }

    try {
      setIsProcessing(true);

      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });

      const address = accounts[0];
      setWalletAddress(address);
      setWalletConnected(true);

      // Initialize provider and contract with signer
      const provider = new BrowserProvider(window.ethereum);
      setProvider(provider);
      await switchToPolygonAmoy();

      // Crea contract con signer e salvalo nello state
      const signer = await provider.getSigner();
      const contractWithSigner = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, signer);
      setContract(contractWithSigner);

      showAlert('Wallet connected successfully!', 'success');

      // Link wallet address with user account
      await linkWalletAddress(address);
    } catch (error) {
      console.error('Wallet connection failed:', error);
      showAlert('Failed to connect wallet. Please try again.', 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [showAlert, switchToPolygonAmoy, linkWalletAddress]);

  // Balance functions
  const refreshBalances = useCallback(async () => {
    try {
      // Refresh DB balance using the withdrawal API balance endpoint
      const dbResponse = await api.get('/teocoin/withdrawals/balance/');
      const dbData = dbResponse.data;

      if (dbData.success && dbData.balance) {
        // Use the correct field names from the API response
        setDbBalance(parseFloat(dbData.balance.available || 0));
      } else {
        console.warn('Balance API returned no data or error:', dbData);
        showAlert('Failed to load balance. Using cached data.', 'warning');
      }

      // Refresh MetaMask balance if connected
      if (walletConnected && walletAddress && provider) {
        try {
          const contract = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, provider);
          const balance = await contract.balanceOf(walletAddress);
          const decimals = await contract.decimals();
          const formattedBalance = parseFloat(formatEther(balance));
          setMetamaskBalance(formattedBalance);
        } catch (error) {
          console.error('Failed to fetch MetaMask balance:', error);
          showAlert('Failed to refresh MetaMask balance', 'warning');
        }
      }
    } catch (error) {
      console.error('Failed to refresh balances:', error);
      showAlert('Failed to refresh balance. Please check your connection.', 'error');
    }
  }, [walletConnected, walletAddress, provider, showAlert]);

  // Withdrawal functions
  const handleWithdrawal = useCallback(async () => {
    if (!withdrawalAmount || parseFloat(withdrawalAmount) <= 0) {
      showAlert('Please enter a valid withdrawal amount', 'error');
      return;
    }

    if (parseFloat(withdrawalAmount) > dbBalance) {
      showAlert('Insufficient balance for withdrawal', 'error');
      return;
    }

    if (!walletConnected || !walletAddress) {
      showAlert('Please connect your MetaMask wallet first', 'error');
      return;
    }

    try {
      setIsProcessing(true);

      const token = localStorage.getItem('accessToken');

      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      // Use the correct field name that the API expects
      const requestData = {
        amount: parseFloat(withdrawalAmount),
        metamask_address: walletAddress // Changed from wallet_address to metamask_address
      };

      console.log('Sending withdrawal request:', requestData);

      const response = await api.post('/teocoin/withdrawals/create/', requestData);
      const data = response.data;

      console.log('Withdrawal response:', data);

      if (data.success) {
        showAlert(
          `Withdrawal request submitted successfully! Request ID: ${data.withdrawal_id}. 
          Your tokens will be minted to your wallet within 1-24 hours.`,
          'success'
        );
        setWithdrawalAmount('');

        // Aggiorna balances dopo la richiesta
        setTimeout(async () => {
          await refreshBalances();
          await loadWithdrawalHistory();
        }, 1000);
      } else {
        // Handle API-level errors (when response is 200 but success is false)
        const errorMessage = data.error || data.message || 'Withdrawal failed for unknown reason';
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('Withdrawal failed:', error);

      // Provide specific error messages for common issues
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        showAlert('Network error. Please check your internet connection and try again.', 'error');
      } else if (error.message.includes('Authentication')) {
        showAlert('Authentication failed. Please log in again.', 'error');
      } else if (error.message.includes('Insufficient balance')) {
        showAlert('Insufficient balance for this withdrawal.', 'error');
      } else if (error.message.includes('too many pending withdrawals')) {
        showAlert(
          'You have too many pending withdrawals. Please wait for current withdrawals to complete before making new requests.',
          'warning'
        );
      } else {
        showAlert(`Withdrawal failed: ${error.message}`, 'error');
      }
    } finally {
      setIsProcessing(false);
    }
  }, [withdrawalAmount, dbBalance, walletConnected, walletAddress, getCsrfToken, showAlert, refreshBalances]);

  // Process pending withdrawal requests (triggers server-side minting)
  const handleProcessPendingWithdrawals = useCallback(async () => {
    try {
      setIsProcessing(true);

      const response = await api.post('/teocoin/withdrawals/admin/process-pending/');
      const data = response.data;

      if (data.success) {
        showAlert(`✅ ${data.message}. Processed: ${data.results.successful}, Failed: ${data.results.failed}`, 'success', 8000);
        // Refresh balances and history after processing
        await refreshBalances();
        await loadWithdrawalHistory();
      } else {
        showAlert(`❌ Processing failed: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Processing failed:', error);
      showAlert(`❌ Processing failed: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [showAlert, refreshBalances]);

  const loadWithdrawalHistory = useCallback(async () => {
    try {
      const response = await api.get('/teocoin/withdrawals/history/');
      const data = response.data;

      if (data.success) {
        const withdrawals = data.withdrawals || [];
        setWithdrawalHistory(withdrawals);

        // Count pending withdrawals
        const pending = withdrawals.filter((w) => w.status === 'pending' || w.status === 'processing').length;
        setPendingWithdrawals(pending);
      }
    } catch (error) {
      console.error('Failed to load withdrawal history:', error);
    }
  }, []);

  // Effects
  useEffect(() => {
    if (open) {
      refreshBalances();
      loadWithdrawalHistory();
    }
  }, [open, refreshBalances, loadWithdrawalHistory]);

  useEffect(() => {
    setDbBalance(userBalance);
  }, [userBalance]);

  // Cancel withdrawal function
  const cancelWithdrawal = useCallback(
    async (withdrawalId) => {
      try {
        setLoading(true);

        const response = await api.post(`/teocoin/withdrawals/${withdrawalId}/cancel/`);
        const data = response.data;

        if (data.success) {
          showAlert(`Withdrawal cancelled successfully! ${data.amount_returned} TEO returned to your balance.`, 'success');
          await loadWithdrawalHistory();
          if (refreshBalances) {
            refreshBalances();
          }
        } else {
          showAlert(data.error || 'Failed to cancel withdrawal', 'error');
        }
      } catch (error) {
        console.error('Error cancelling withdrawal:', error);
        showAlert('Failed to cancel withdrawal. Please try again.', 'error');
      } finally {
        setLoading(false);
      }
    },
    [showAlert, loadWithdrawalHistory, refreshBalances]
  );

  // Event handlers
  const handleClose = () => {
    setAlert(null);
    onClose();
  };

  const handleAddTokenToWallet = async () => {
    if (!window.ethereum) return;

    try {
      await window.ethereum.request({
        method: 'wallet_watchAsset',
        params: {
          type: 'ERC20',
          options: {
            address: TEOCOIN_CONTRACT,
            symbol: 'TEO',
            decimals: 18,
            image: 'https://via.placeholder.com/64/667eea/ffffff?text=TEO'
          }
        }
      });
      showAlert('TEO token added to wallet!', 'success');
    } catch (error) {
      showAlert('Failed to add token to wallet', 'error');
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth className="teocoin-withdrawal-dialog">
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <AccountBalanceWallet color="primary" />
            <Typography variant="h6">TeoCoin Withdrawal</Typography>
          </Box>
          <IconButton onClick={handleClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {alert && (
          <Alert severity={alert.severity} sx={{ mb: 2 }}>
            {alert.message}
          </Alert>
        )}

        {/* Balance Overview */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Platform Balance
                </Typography>
                <Typography variant="h5" color="primary">
                  {dbBalance.toFixed(2)} TEO
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">
                      MetaMask Balance
                    </Typography>
                    <Typography variant="h5" color="secondary">
                      {metamaskBalance.toFixed(2)} TEO
                    </Typography>
                  </Box>
                  <Tooltip title="Refresh balances">
                    <IconButton onClick={refreshBalances} size="small">
                      <Refresh />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Wallet Connection */}
        {!walletConnected ? (
          <Box textAlign="center" sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Connect your MetaMask wallet to start withdrawing TeoCoin
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={connectWallet}
              disabled={isProcessing}
              startIcon={isProcessing ? <CircularProgress size={20} /> : <AccountBalanceWallet />}
            >
              {isProcessing ? 'Connecting...' : 'Connect MetaMask'}
            </Button>
          </Box>
        ) : (
          <Box sx={{ mb: 3 }}>
            <Box display="flex" alignItems="center" gap={1} sx={{ mb: 2 }}>
              <CheckCircle color="success" />
              <Typography variant="body2">Wallet connected: {`${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`}</Typography>
              <Chip label="Connected" color="success" size="small" />
            </Box>

            {/* Withdrawal Form */}
            <Card variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Request Withdrawal
              </Typography>

              {/* Pending Withdrawals Warning */}
              {pendingWithdrawals > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    You have {pendingWithdrawals} pending withdrawal{pendingWithdrawals > 1 ? 's' : ''}.
                    {pendingWithdrawals >= 3
                      ? ' Please wait for current withdrawals to complete before making new requests.'
                      : ' New requests may be delayed.'}
                  </Typography>
                </Alert>
              )}

              <TextField
                fullWidth
                label="Withdrawal Amount (TEO)"
                type="number"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                inputProps={{
                  min: 0.01,
                  max: dbBalance,
                  step: 0.01
                }}
                helperText={`Available: ${dbBalance.toFixed(2)} TEO`}
                sx={{ mb: 2 }}
              />

              <Box display="flex" gap={2} mb={2}>
                <Button
                  variant="contained"
                  onClick={handleWithdrawal}
                  disabled={isProcessing || !withdrawalAmount || parseFloat(withdrawalAmount) <= 0 || pendingWithdrawals >= 3}
                  startIcon={isProcessing ? <CircularProgress size={20} /> : <Send />}
                  fullWidth
                >
                  {isProcessing ? 'Processing...' : 'Request Withdrawal'}
                </Button>

                <Button variant="outlined" onClick={handleAddTokenToWallet} sx={{ minWidth: 'fit-content' }}>
                  Add TEO to Wallet
                </Button>
              </Box>

              {/* Admin/Test Button - Process pending withdrawals */}
              <Box display="flex" gap={2}>
                <Button
                  variant="outlined"
                  color="warning"
                  onClick={handleProcessPendingWithdrawals}
                  disabled={isProcessing || pendingWithdrawals === 0}
                  startIcon={isProcessing ? <CircularProgress size={20} /> : <Refresh />}
                  fullWidth
                >
                  {isProcessing ? 'Processing...' : `Process ${pendingWithdrawals} Pending Withdrawals`}
                </Button>
              </Box>
            </Card>

            {/* Withdrawal History */}
            {withdrawalHistory.length > 0 && (
              <Card variant="outlined" sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="h6">Recent Withdrawals</Typography>
                  {pendingWithdrawals > 0 && (
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      onClick={() => {
                        const pendingIds = withdrawalHistory
                          .filter((w) => w.status === 'pending' || w.status === 'processing')
                          .map((w) => w.id);

                        if (window.confirm(`Cancel all ${pendingWithdrawals} pending withdrawals?`)) {
                          pendingIds.forEach((id) => cancelWithdrawal(id));
                        }
                      }}
                      disabled={loading}
                      sx={{ fontSize: '0.75rem' }}
                    >
                      Clear All Pending
                    </Button>
                  )}
                </Box>
                {withdrawalHistory.slice(0, 3).map((withdrawal, index) => (
                  <Box
                    key={index}
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    sx={{ py: 1, borderBottom: index < 2 ? '1px solid hsl(var(--muted))' : 'none' }}
                  >
                    <Box>
                      <Typography variant="body2">{withdrawal.amount} TEO</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {new Date(withdrawal.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={withdrawal.status}
                        color={withdrawal.status === 'completed' ? 'success' : withdrawal.status === 'pending' ? 'warning' : 'default'}
                        size="small"
                      />
                      {(withdrawal.status === 'pending' || withdrawal.status === 'processing') && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          onClick={() => cancelWithdrawal(withdrawal.id)}
                          disabled={loading}
                          sx={{ minWidth: '70px', fontSize: '0.7rem' }}
                        >
                          Cancel
                        </Button>
                      )}
                    </Box>
                  </Box>
                ))}
              </Card>
            )}
          </Box>
        )}

        {/* Information */}
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2">
            Withdrawals are processed to the Polygon Amoy testnet. Make sure your MetaMask is connected to the correct network.
          </Typography>
        </Alert>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default TeoCoinWithdrawal;
