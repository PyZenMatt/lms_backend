/**
 * TeoCoin Manager Demo Page
 *
 * Page to test the new unified TeoCoin component
 */

import React, { useState } from 'react';
import { Container, Typography, Button, Box, Paper } from '@mui/material';
import TeoCoinManager from '../components/TeoCoinManager';

const TeoCoinManagerDemo = () => {
  const [managerOpen, setManagerOpen] = useState(false);
  const [userBalance] = useState(150.75); // Mock balance for demo

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        🪙 TeoCoin Manager Demo
      </Typography>

      <Typography variant="subtitle1" align="center" color="textSecondary" sx={{ mb: 4 }}>
        Unified component for all TeoCoin operations: Withdraw, Burn/Deposit, and Staking
      </Typography>

      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          🎯 Features Demonstration
        </Typography>

        <Box component="ul" sx={{ pl: 2, mb: 3 }}>
          <Typography component="li" gutterBottom>
            <strong>Withdrawal:</strong> Database → MetaMask (mints new tokens)
          </Typography>
          <Typography component="li" gutterBottom>
            <strong>Burn/Deposit:</strong> MetaMask → Database (burns tokens, credits balance)
          </Typography>
          <Typography component="li" gutterBottom>
            <strong>Staking:</strong> Database → Staked (only for teachers)
          </Typography>
          <Typography component="li" gutterBottom>
            <strong>Unified Interface:</strong> One component for all roles (Student, Teacher, Admin)
          </Typography>
        </Box>

        <Box textAlign="center">
          <Button
            variant="contained"
            size="large"
            onClick={() => setManagerOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary) 100%)',
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              borderRadius: 2
            }}
          >
            Open TeoCoin Manager
          </Button>
        </Box>
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📋 Testing Instructions
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <Typography component="li" gutterBottom>
            Click "Open TeoCoin Manager" to launch the unified component
          </Typography>
          <Typography component="li" gutterBottom>
            Connect your MetaMask wallet (Polygon Amoy testnet)
          </Typography>
          <Typography component="li" gutterBottom>
            Test different tabs: Withdraw, Deposit (Burn), and Stake (if teacher)
          </Typography>
          <Typography component="li" gutterBottom>
            Verify that balances update correctly after operations
          </Typography>
        </Box>
      </Paper>

      <TeoCoinManager open={managerOpen} onClose={() => setManagerOpen(false)} userBalance={userBalance} />
    </Container>
  );
};

export default TeoCoinManagerDemo;
