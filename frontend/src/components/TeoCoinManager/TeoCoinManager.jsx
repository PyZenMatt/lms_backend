/**
 * 🪙 TeoCoin Manager - Unified Component
 * 
 * Handles all TeoCoin operations for all user roles:
 * - BURN: MetaMask → Database (converts MetaMask tokens to platform balance)
 * - WITHDRAWAL: Database → MetaMask (mints new tokens to user wallet)
 * - STAKING: Available only for teachers (stakes database TeoCoin)
 * 
 * Shared by: Student, Teacher, Admin
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent,
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
  Tooltip,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import {
  AccountBalanceWallet,
  Send,
  Refresh,
  Close,
  Info,
  CheckCircle,
  LocalFireDepartment,
  AccountBalance,
  TrendingUp
} from '@mui/icons-material';
import { BrowserProvider, Contract, formatEther, parseEther } from 'ethers';
import { useAuth } from '../../contexts/AuthContext';
import './TeoCoinManager.scss';

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
  }
];

const TeoCoinManager = ({ open, onClose, userBalance = 0 }) => {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState(0); // 0: Withdraw, 1: Burn, 2: Stake (teacher only)
  
  // State management
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [alert, setAlert] = useState(null);
  
  // Balances
  const [dbBalance, setDbBalance] = useState(userBalance);
  const [metamaskBalance, setMetamaskBalance] = useState(0);
  const [stakedBalance, setStakedBalance] = useState(0);
  
  // Form inputs
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [burnAmount, setBurnAmount] = useState('');
  const [stakeAmount, setStakeAmount] = useState('');
  
  // Web3 objects
  const [provider, setProvider] = useState(null);
  const [contract, setContract] = useState(null);
  
  // History
  const [withdrawalHistory, setWithdrawalHistory] = useState([]);
  const [transactionHistory, setTransactionHistory] = useState([]);

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

  // Check if user is teacher (for staking feature)
  const isTeacher = user?.role === 'teacher' || user?.is_teacher;

  // Network switching function
  const switchToPolygonAmoy = useCallback(async () => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: POLYGON_AMOY_CHAIN_ID }]
      });
    } catch (error) {
      if (error.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
              chainId: POLYGON_AMOY_CHAIN_ID,
              chainName: 'Polygon Amoy Testnet',
              nativeCurrency: {
                name: 'MATIC',
                symbol: 'MATIC',
                decimals: 18
              },
              rpcUrls: ['https://rpc-amoy.polygon.technology/'],
              blockExplorerUrls: ['https://amoy.polygonscan.com/']
            }]
          });
        } catch (addError) {
          throw new Error('Failed to add Polygon Amoy network');
        }
      } else {
        throw error;
      }
    }
  }, []);

  // MetaMask connection
  const connectWallet = useCallback(async () => {
    if (!window.ethereum) {
      showAlert('MetaMask is not installed. Please install MetaMask to continue.', 'error');
      return;
    }

    try {
      setIsProcessing(true);

      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });

      const address = accounts[0];
      setWalletAddress(address);
      setWalletConnected(true);

      const provider = new BrowserProvider(window.ethereum);
      setProvider(provider);
      await switchToPolygonAmoy();

      const signer = await provider.getSigner();
      const contractWithSigner = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, signer);
      setContract(contractWithSigner);

      showAlert('Wallet connected successfully!', 'success');

    } catch (error) {
      console.error('Wallet connection failed:', error);
      showAlert('Failed to connect wallet. Please try again.', 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [showAlert, switchToPolygonAmoy]);

  // Balance functions
  const refreshBalances = useCallback(async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      // Refresh DB balance
      const dbResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (dbResponse.ok) {
        const dbData = await dbResponse.json();
        if (dbData.success && dbData.balance) {
          setDbBalance(parseFloat(dbData.balance.available || 0));
          setStakedBalance(parseFloat(dbData.balance.staked || 0));
        }
      }

      // Refresh MetaMask balance if connected
      if (walletConnected && walletAddress && contract) {
        try {
          const balance = await contract.balanceOf(walletAddress);
          const formattedBalance = parseFloat(formatEther(balance));
          setMetamaskBalance(formattedBalance);
        } catch (error) {
          console.error('Failed to fetch MetaMask balance:', error);
        }
      }
    } catch (error) {
      console.error('Failed to refresh balances:', error);
      showAlert('Failed to refresh balance. Please check your connection.', 'error');
    }
  }, [walletConnected, walletAddress, contract, showAlert]);

  // WITHDRAWAL: Database → MetaMask (mint new tokens)
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

      const requestData = {
        amount: parseFloat(withdrawalAmount),
        metamask_address: walletAddress
      };

      const response = await fetch('/api/v1/teocoin/withdrawals/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Withdrawal request failed');
      }
      
      if (data.success) {
        showAlert(`Withdrawal request submitted successfully! Request ID: ${data.withdrawal_id}`, 'success');
        setWithdrawalAmount('');
        await refreshBalances();
      } else {
        throw new Error(data.error || 'Withdrawal failed');
      }
      
    } catch (error) {
      console.error('Withdrawal failed:', error);
      showAlert(`Withdrawal failed: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [withdrawalAmount, dbBalance, walletConnected, walletAddress, getCsrfToken, showAlert, refreshBalances]);

  // BURN: MetaMask → Database (burn tokens and credit platform balance)
  const handleBurn = useCallback(async () => {
    if (!burnAmount || parseFloat(burnAmount) <= 0) {
      showAlert('Please enter a valid burn amount', 'error');
      return;
    }

    if (parseFloat(burnAmount) > metamaskBalance) {
      showAlert('Insufficient MetaMask balance for burn', 'error');
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

      // Call burn API (burns tokens and credits database balance)
      const requestData = {
        amount: parseFloat(burnAmount),
        wallet_address: walletAddress
      };

      const response = await fetch('/api/v1/teocoin/burn/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Burn request failed');
      }
      
      if (data.success) {
        showAlert(`Burn successful! ${burnAmount} TEO tokens burned and credited to your platform balance.`, 'success');
        setBurnAmount('');
        await refreshBalances();
      } else {
        throw new Error(data.error || 'Burn failed');
      }
      
    } catch (error) {
      console.error('Burn failed:', error);
      showAlert(`Burn failed: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [burnAmount, metamaskBalance, walletConnected, walletAddress, getCsrfToken, showAlert, refreshBalances]);

  // STAKING: Database → Staked (only for teachers)
  const handleStaking = useCallback(async () => {
    if (!isTeacher) {
      showAlert('Staking is only available for teachers', 'error');
      return;
    }

    if (!stakeAmount || parseFloat(stakeAmount) <= 0) {
      showAlert('Please enter a valid stake amount', 'error');
      return;
    }

    if (parseFloat(stakeAmount) > dbBalance) {
      showAlert('Insufficient balance for staking', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const requestData = {
        amount: parseFloat(stakeAmount)
      };

      const response = await fetch('/api/v1/teocoin/staking/stake/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Staking request failed');
      }
      
      if (data.success) {
        showAlert(`Staking successful! ${stakeAmount} TEO staked.`, 'success');
        setStakeAmount('');
        await refreshBalances();
      } else {
        throw new Error(data.error || 'Staking failed');
      }
      
    } catch (error) {
      console.error('Staking failed:', error);
      showAlert(`Staking failed: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [isTeacher, stakeAmount, dbBalance, getCsrfToken, showAlert, refreshBalances]);

  // Load transaction history
  const loadTransactionHistory = useCallback(async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/v1/teocoin/transactions/history/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setTransactionHistory(data.transactions || []);
        }
      }
    } catch (error) {
      console.error('Failed to load transaction history:', error);
    }
  }, []);

  // Effects
  useEffect(() => {
    if (open) {
      refreshBalances();
      loadTransactionHistory();
    }
  }, [open, refreshBalances, loadTransactionHistory]);

  useEffect(() => {
    setDbBalance(userBalance);
  }, [userBalance]);

  // Event handlers
  const handleClose = () => {
    setAlert(null);
    onClose();
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Tab content rendering
  const renderWithdrawalTab = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Withdraw TEO to MetaMask
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
        Transfer TeoCoin from your platform balance to your MetaMask wallet. New tokens will be minted directly to your wallet.
      </Typography>
      
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

      <Button
        variant="contained"
        onClick={handleWithdrawal}
        disabled={isProcessing || !withdrawalAmount || parseFloat(withdrawalAmount) <= 0 || !walletConnected}
        startIcon={isProcessing ? <CircularProgress size={20} /> : <Send />}
        fullWidth
        size="large"
      >
        {isProcessing ? 'Processing...' : 'Request Withdrawal'}
      </Button>
    </Box>
  );

  const renderBurnTab = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Deposit TEO from MetaMask
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
        Burn TeoCoin tokens from your MetaMask wallet and credit your platform balance. Tokens will be permanently destroyed.
      </Typography>
      
      <TextField
        fullWidth
        label="Burn Amount (TEO)"
        type="number"
        value={burnAmount}
        onChange={(e) => setBurnAmount(e.target.value)}
        inputProps={{ 
          min: 0.01, 
          max: metamaskBalance,
          step: 0.01 
        }}
        helperText={`MetaMask balance: ${metamaskBalance.toFixed(2)} TEO`}
        sx={{ mb: 2 }}
      />

      <Button
        variant="contained"
        color="warning"
        onClick={handleBurn}
        disabled={isProcessing || !burnAmount || parseFloat(burnAmount) <= 0 || !walletConnected}
        startIcon={isProcessing ? <CircularProgress size={20} /> : <LocalFireDepartment />}
        fullWidth
        size="large"
      >
        {isProcessing ? 'Processing...' : 'Burn & Deposit'}
      </Button>
    </Box>
  );

  const renderStakingTab = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Stake TeoCoin (Teachers Only)
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
        Stake your platform TeoCoin to increase your commission rates and earnings. Staked tokens remain in the database.
      </Typography>
      
      <TextField
        fullWidth
        label="Stake Amount (TEO)"
        type="number"
        value={stakeAmount}
        onChange={(e) => setStakeAmount(e.target.value)}
        inputProps={{ 
          min: 0.01, 
          max: dbBalance,
          step: 0.01 
        }}
        helperText={`Available: ${dbBalance.toFixed(2)} TEO | Currently staked: ${stakedBalance.toFixed(2)} TEO`}
        sx={{ mb: 2 }}
      />

      <Button
        variant="contained"
        color="secondary"
        onClick={handleStaking}
        disabled={isProcessing || !stakeAmount || parseFloat(stakeAmount) <= 0 || !isTeacher}
        startIcon={isProcessing ? <CircularProgress size={20} /> : <TrendingUp />}
        fullWidth
        size="large"
      >
        {isProcessing ? 'Processing...' : 'Stake TEO'}
      </Button>
    </Box>
  );

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      className="teocoin-manager-dialog"
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <AccountBalanceWallet color="primary" />
            <Typography variant="h6">TeoCoin Manager</Typography>
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
          <Grid item xs={12} md={4}>
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
          <Grid item xs={12} md={4}>
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
          {isTeacher && (
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="textSecondary">
                    Staked Balance
                  </Typography>
                  <Typography variant="h5" color="success.main">
                    {stakedBalance.toFixed(2)} TEO
                  </Typography>
                </CardContent>
            </Card>
          </Grid>
          )}
        </Grid>

        {/* Wallet Connection */}
        {!walletConnected ? (
          <Box textAlign="center" sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Connect your MetaMask wallet to manage TeoCoin
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
              <Typography variant="body2">
                Wallet connected: {`${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`}
              </Typography>
              <Chip 
                label="Connected" 
                color="success" 
                size="small" 
              />
            </Box>

            {/* Tabs for different operations */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
              <Tabs value={currentTab} onChange={handleTabChange}>
                <Tab label="Withdraw" icon={<Send />} />
                <Tab label="Deposit (Burn)" icon={<LocalFireDepartment />} />
                {isTeacher && <Tab label="Stake" icon={<TrendingUp />} />}
              </Tabs>
            </Box>

            {/* Tab content */}
            <Card variant="outlined" sx={{ p: 2, mb: 2 }}>
              {currentTab === 0 && renderWithdrawalTab()}
              {currentTab === 1 && renderBurnTab()}
              {currentTab === 2 && isTeacher && renderStakingTab()}
            </Card>
          </Box>
        )}

        {/* Information */}
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2">
            All operations are processed on the Polygon Amoy testnet. 
            {isTeacher ? ' As a teacher, you can also stake TeoCoin to increase your commission rates.' : ''}
          </Typography>
        </Alert>
      </DialogContent>
    </Dialog>
  );
};

export default TeoCoinManager;
