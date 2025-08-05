import React from 'react';
import { Container, Typography, Box, Grid, Paper } from '@mui/material';
import TeoCoinBalanceDemo from '../components/TeoCoinBalanceDemo';
import TeoCoinBalanceWidget from '../components/TeoCoinBalanceWidget';

const TeoCoinDemo = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={2} sx={{ p: 3, mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          🚀 TeoCoin Withdrawal System Demo
        </Typography>
        <Typography variant="h6">
          MetaMask integration with Polygon Amoy network
        </Typography>
      </Paper>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h5" gutterBottom>
              📱 Balance Widget (Full)
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Used in Student & Teacher Dashboards
            </Typography>
            <TeoCoinBalanceDemo />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h5" gutterBottom>
              📱 Balance Widget (Compact)
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Used in Admin Dashboard
            </Typography>
            <TeoCoinBalanceWidget variant="compact" />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              ✅ Integration Status
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'white' }}>
                <Typography variant="subtitle2">Student Dashboard</Typography>
                <Typography variant="caption">✅ Integrated</Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'white' }}>
                <Typography variant="subtitle2">Teacher Dashboard</Typography>
                <Typography variant="caption">✅ Integrated</Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'white' }}>
                <Typography variant="subtitle2">Admin Dashboard</Typography>
                <Typography variant="caption">✅ Integrated</Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', borderRadius: 1, color: 'white' }}>
                <Typography variant="subtitle2">API Integration</Typography>
                <Typography variant="caption">⚠️ Demo Mode</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              🎯 How to Test
            </Typography>
            <Box component="ol" sx={{ pl: 2 }}>
              <Typography component="li" gutterBottom>
                Click "Withdraw to MetaMask" on any widget above
              </Typography>
              <Typography component="li" gutterBottom>
                MetaMask withdrawal dialog will open
              </Typography>
              <Typography component="li" gutterBottom>
                Connect your MetaMask wallet (if available)
              </Typography>
              <Typography component="li" gutterBottom>
                Switch to Polygon Amoy testnet automatically
              </Typography>
              <Typography component="li" gutterBottom>
                Enter withdrawal amount and test the flow
              </Typography>
              <Typography component="li" gutterBottom>
                The demo shows the complete UI/UX without backend integration
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TeoCoinDemo;
