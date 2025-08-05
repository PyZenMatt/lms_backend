import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Alert, 
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Paper,
  TextField,
  Tabs,
  Tab,
  Badge,
  Divider
} from '@mui/material';
import { 
  School, 
  CheckCircle, 
  Cancel, 
  HourglassEmpty,
  Timer,
  AccountBalanceWallet,
  TrendingUp,
  Assignment,
  MonetizationOn
} from '@mui/icons-material';
import { useWeb3Context } from '../../contexts/Web3Context';
import { useNotification } from '../../contexts/NotificationContext';
import { 
  getTeacherRequests, 
  approveDiscountRequest, 
  declineDiscountRequest,
  formatTeoAmount,
  getDiscountStatusName
} from '../../services/api/teocoinDiscount';

/**
 * TeacherDiscountDashboard - Manage student discount requests
 * 
 * Features:
 * - View and manage pending discount requests
 * - One-click approval/decline (platform pays gas)
 * - Real-time earnings tracking
 * - Request history and analytics
 */
const TeacherDiscountDashboard = () => {
  const { account, teoBalance, refreshBalance } = useWeb3Context();
  const { showNotification } = useNotification();
  
  // State
  const [teacherRequests, setTeacherRequests] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [completedRequests, setCompletedRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Dialog state
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [declineDialog, setDeclineDialog] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [declineReason, setDeclineReason] = useState('');
  
  // Analytics
  const [analytics, setAnalytics] = useState({
    totalEarnings: 0,
    totalRequests: 0,
    approvalRate: 0,
    monthlyEarnings: 0
  });

  useEffect(() => {
    if (account) {
      loadTeacherRequests();
    }
  }, [account]);

  useEffect(() => {
    calculateAnalytics();
  }, [teacherRequests]);

  const loadTeacherRequests = async () => {
    try {
      setLoading(true);
      const data = await getTeacherRequests(account);
      
      if (data.success) {
        const requests = data.requests || [];
        setTeacherRequests(requests);
        
        // Separate pending and completed requests
        const pending = requests.filter(r => r.status === 0);
        const completed = requests.filter(r => r.status !== 0);
        
        setPendingRequests(pending);
        setCompletedRequests(completed);
      } else {
        console.error('Failed to load teacher requests');
        showNotification('Failed to load discount requests', 'error');
      }
    } catch (error) {
      console.error('Error loading teacher requests:', error);
      showNotification('Error loading discount requests', 'error');
    } finally {
      setLoading(false);
    }
  };

  const calculateAnalytics = () => {
    const approved = teacherRequests.filter(r => r.status === 1);
    const totalEarnings = approved.reduce((sum, r) => sum + (r.teacher_bonus / 10**18), 0);
    const approvalRate = teacherRequests.length > 0 ? (approved.length / teacherRequests.length) * 100 : 0;
    
    // Calculate monthly earnings (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const monthlyApproved = approved.filter(r => 
      new Date(r.created_at) >= thirtyDaysAgo
    );
    const monthlyEarnings = monthlyApproved.reduce((sum, r) => sum + (r.teacher_bonus / 10**18), 0);
    
    setAnalytics({
      totalEarnings,
      totalRequests: teacherRequests.length,
      approvalRate,
      monthlyEarnings
    });
  };

  const handleApprove = async (request) => {
    setSelectedRequest(request);
    setApprovalDialog(true);
  };

  const handleDecline = async (request) => {
    setSelectedRequest(request);
    setDeclineDialog(true);
  };

  const confirmApproval = async () => {
    if (!selectedRequest) return;

    try {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: true });

      const result = await approveDiscountRequest(selectedRequest.request_id, account);

      if (result.success) {
        showNotification(
          `✅ TEO Tokens Accepted! You earned ${formatTeoAmount(selectedRequest.teacher_bonus)} TEO bonus. 
          Total received: ${formatTeoAmount(selectedRequest.teo_cost + selectedRequest.teacher_bonus)} TEO for staking.`,
          'success'
        );
        
        // Refresh data
        await loadTeacherRequests();
        await refreshBalance();
        
      } else {
        throw new Error(result.error || 'Failed to approve request');
      }

    } catch (error) {
      console.error('Error approving request:', error);
      showNotification(error.message || 'Failed to approve request', 'error');
    } finally {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: false });
      setApprovalDialog(false);
      setSelectedRequest(null);
    }
  };

  const confirmDecline = async () => {
    if (!selectedRequest) return;

    try {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: true });

      const reason = declineReason.trim() || 'Teacher chose full EUR commission';
      const result = await declineDiscountRequest(selectedRequest.request_id, account, reason);

      if (result.success) {
        showNotification(
          `💰 Full EUR Commission Chosen! You will receive your full commission. 
          Student keeps the discount (platform absorbed the cost).`, 
          'info'
        );
        
        // Refresh data
        await loadTeacherRequests();
        
      } else {
        throw new Error(result.error || 'Failed to decline request');
      }

    } catch (error) {
      console.error('Error declining request:', error);
      showNotification(error.message || 'Failed to decline request', 'error');
    } finally {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: false });
      setDeclineDialog(false);
      setSelectedRequest(null);
      setDeclineReason('');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 0: return <HourglassEmpty color="warning" />;
      case 1: return <CheckCircle color="success" />;
      case 2: return <Cancel color="error" />;
      case 3: return <Timer color="disabled" />;
      default: return <HourglassEmpty />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 0: return 'Pending';
      case 1: return 'Approved';
      case 2: return 'Declined';
      case 3: return 'Expired';
      default: return 'Unknown';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 0: return 'warning';
      case 1: return 'success';
      case 2: return 'error';
      case 3: return 'default';
      default: return 'default';
    }
  };

  const formatTimeRemaining = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diff = deadlineDate.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m remaining`;
  };

  const renderRequestCard = (request, showActions = false) => (
    <Paper key={request.request_id} sx={{ p: 3, mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Request #{request.request_id}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Course #{request.course_id}
          </Typography>
        </Box>
        <Chip
          icon={getStatusIcon(request.status)}
          label={getStatusText(request.status)}
          color={getStatusColor(request.status)}
        />
      </Box>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Student</Typography>
          <Typography variant="body1">
            {`${request.student.slice(0, 6)}...${request.student.slice(-4)}`}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Discount</Typography>
          <Typography variant="body1">
            {request.discount_percent}% (€{(request.course_price * request.discount_percent / 10000).toFixed(2)})
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Student Pays</Typography>
          <Typography variant="body1">
            {(request.teo_cost / 10**18).toFixed(2)} TEO
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Your Bonus</Typography>
          <Typography variant="body1" color="success.main">
            +{(request.teacher_bonus / 10**18).toFixed(2)} TEO
          </Typography>
        </Grid>
      </Grid>

      {request.status === 0 && (
        <Typography variant="body2" color="warning.main" sx={{ mb: 2 }}>
          ⏰ {formatTimeRemaining(request.deadline)}
        </Typography>
      )}

      {request.decline_reason && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Decline Reason:</strong> {request.decline_reason}
        </Alert>
      )}

      {showActions && request.status === 0 && (
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleApprove(request)}
            disabled={actionLoading[request.request_id]}
            startIcon={actionLoading[request.request_id] ? <CircularProgress size={20} /> : <CheckCircle />}
          >
            🪙 Accept TEO
          </Button>
          <Button
            variant="outlined"
            color="warning"
            onClick={() => handleDecline(request)}
            disabled={actionLoading[request.request_id]}
            startIcon={<Cancel />}
          >
            💰 Keep EUR
          </Button>
        </Box>
      )}
    </Paper>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <School sx={{ mr: 1, verticalAlign: 'middle' }} />
          Teacher Discount Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Manage student discount requests and track your TeoCoin earnings
        </Typography>
      </Box>

      {/* Analytics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MonetizationOn color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.totalEarnings.toFixed(2)} TEO</Typography>
                  <Typography variant="body2" color="text.secondary">Total Earnings</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assignment color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.totalRequests}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Requests</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.approvalRate.toFixed(1)}%</Typography>
                  <Typography variant="body2" color="text.secondary">Approval Rate</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalanceWallet color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.monthlyEarnings.toFixed(2)} TEO</Typography>
                  <Typography variant="body2" color="text.secondary">This Month</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Requests Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab
              label={
                <Badge badgeContent={pendingRequests.length} color="warning">
                  Pending Requests
                </Badge>
              }
            />
            <Tab label="Request History" />
          </Tabs>
        </Box>

        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* Pending Requests Tab */}
              {selectedTab === 0 && (
                <Box>
                  {pendingRequests.length === 0 ? (
                    <Typography color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                      No pending discount requests
                    </Typography>
                  ) : (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Pending Approval ({pendingRequests.length})
                      </Typography>
                      {pendingRequests.map(request => renderRequestCard(request, true))}
                    </Box>
                  )}
                </Box>
              )}

              {/* History Tab */}
              {selectedTab === 1 && (
                <Box>
                  {completedRequests.length === 0 ? (
                    <Typography color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                      No completed requests yet
                    </Typography>
                  ) : (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Request History ({completedRequests.length})
                      </Typography>
                      {completedRequests.map(request => renderRequestCard(request, false))}
                    </Box>
                  )}
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Approval Dialog */}
      <Dialog open={approvalDialog} onClose={() => setApprovalDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Approve Discount Request</DialogTitle>
        <DialogContent>
          {selectedRequest && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                ✅ <strong>Student already received {selectedRequest.discount_percent}% discount and enrolled!</strong>
              </Alert>
              
              <Alert severity="success" sx={{ mb: 2 }}>
                <strong>🪙 Accept TEO Tokens (Staking Strategy):</strong>
                <ul>
                  <li>You'll receive: {formatTeoAmount(selectedRequest.teo_cost)} TEO from student</li>
                  <li>Plus 25% bonus: {formatTeoAmount(selectedRequest.teacher_bonus)} TEO from reward pool</li>
                  <li>Total TEO: {formatTeoAmount(selectedRequest.teo_cost + selectedRequest.teacher_bonus)} TEO for staking</li>
                  <li>Your EUR commission will be reduced to absorb the discount cost</li>
                  <li>Stake TEO to increase your future commission rates!</li>
                </ul>
                <em>Platform pays all gas fees automatically.</em>
              </Alert>
              
              <Typography variant="body1">
                <strong>Course:</strong> #{selectedRequest.course_id}
              </Typography>
              <Typography variant="body1">
                <strong>Student:</strong> {selectedRequest.student}
              </Typography>
              <Typography variant="body1">
                <strong>Discount:</strong> {selectedRequest.discount_percent}%
              </Typography>
              <Typography variant="body1" color="success.main">
                <strong>🎯 Choose TEO for Staking:</strong> {formatTeoAmount(selectedRequest.teo_cost + selectedRequest.teacher_bonus)} TEO total
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={confirmApproval}
            variant="contained"
            color="success"
            startIcon={<CheckCircle />}
          >
            🪙 Accept TEO Tokens
          </Button>
        </DialogActions>
      </Dialog>

      {/* Decline Dialog */}
      <Dialog open={declineDialog} onClose={() => setDeclineDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>💰 Keep Full EUR Commission</DialogTitle>
        <DialogContent>
          {selectedRequest && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                ✅ <strong>Student already received {selectedRequest.discount_percent}% discount and enrolled!</strong>
              </Alert>
              
              <Alert severity="warning" sx={{ mb: 2 }}>
                <strong>💰 Keep Full EUR Commission (Safe Strategy):</strong>
                <ul>
                  <li>You'll receive your full EUR commission</li>
                  <li>Student keeps the discount (platform absorbs the cost)</li>
                  <li>TEO tokens return to reward pool</li>
                  <li>No staking opportunity, but guaranteed EUR payment</li>
                </ul>
              </Alert>
              
              <Typography variant="body1" gutterBottom>
                <strong>Course:</strong> #{selectedRequest.course_id}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Student:</strong> {selectedRequest.student}
              </Typography>
              
              <TextField
                label="Optional note for student"
                multiline
                rows={3}
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                fullWidth
                sx={{ mt: 2 }}
                placeholder="e.g., 'Preferring EUR payment this time' or leave blank..."
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeclineDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={confirmDecline}
            variant="contained"
            color="warning"
            startIcon={<Cancel />}
          >
            💰 Keep Full EUR
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeacherDiscountDashboard;
