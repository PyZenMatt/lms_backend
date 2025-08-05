import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  AccountBalanceWallet,
  Send,
  Refresh
} from '@mui/icons-material';
import TeoCoinWithdrawal from '../TeoCoinWithdrawal';

const TeoCoinBalanceDemo = () => {
  const [balance, setBalance] = useState(125.50); // Demo balance
  const [loading, setLoading] = useState(false);
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);
  const [alert, setAlert] = useState(null);

  const showAlert = (message, severity = 'info') => {
    setAlert({ message, severity });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleRefresh = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setBalance(Math.random() * 200 + 50); // Random balance for demo
      setLoading(false);
      showAlert('Balance refreshed!', 'success');
    }, 1000);
  };

  return (
    <>
      {alert && (
        <Alert severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}
      
      <Card elevation={3}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <AccountBalanceWallet color="primary" fontSize="large" />
              <Typography variant="h6" color="primary">
                TeoCoin Wallet Demo
              </Typography>
            </Box>
            <Button
              variant="outlined"
              onClick={handleRefresh}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
            >
              Refresh
            </Button>
          </Box>

          <Box mb={3}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              Available Balance
            </Typography>
            <Typography variant="h4" color="primary" fontWeight="bold">
              {balance.toFixed(2)} TEO
            </Typography>
          </Box>

          <Button
            variant="contained"
            fullWidth
            onClick={() => setWithdrawalOpen(true)}
            startIcon={<Send />}
            size="large"
            disabled={loading}
          >
            Withdraw to MetaMask
          </Button>

          <Box mt={2}>
            <Typography variant="caption" color="textSecondary">
              Demo: Withdraw your TeoCoin earnings to MetaMask wallet on Polygon Amoy network
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <TeoCoinWithdrawal
        open={withdrawalOpen}
        onClose={() => setWithdrawalOpen(false)}
        userBalance={balance}
      />
    </>
  );
};

export default TeoCoinBalanceDemo;
