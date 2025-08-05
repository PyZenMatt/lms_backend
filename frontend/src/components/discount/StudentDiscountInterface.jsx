import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  Alert, 
  Slider, 
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Divider,
  Paper
} from '@mui/material';
import { 
  AccountBalanceWallet, 
  School, 
  LocalOffer, 
  Timer,
  CheckCircle,
  Cancel,
  HourglassEmpty
} from '@mui/icons-material';
import { ethers } from 'ethers';
import { useWeb3Context } from '../../contexts/Web3Context';
import { useNotification } from '../../contexts/NotificationContext';

/**
 * StudentDiscountInterface - Gas-free TeoCoin discount system for students
 * 
 * Features:
 * - Request discounts without paying gas fees
 * - One-click signature pre-approval
 * - Real-time request status tracking
 * - TEO balance and cost calculation
 */
const StudentDiscountInterface = () => {
  const { account, web3Provider, teoBalance, refreshBalance } = useWeb3Context();
  const { showNotification } = useNotification();
  
  // Form state
  const [courseId, setCourseId] = useState('');
  const [coursePrice, setCoursePrice] = useState('');
  const [teacherAddress, setTeacherAddress] = useState('');
  const [discountPercent, setDiscountPercent] = useState(10);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [signatureDialog, setSignatureDialog] = useState(false);
  const [signatureData, setSignatureData] = useState(null);
  const [studentRequests, setStudentRequests] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(false);
  
  // Calculated values
  const [teoCost, setTeoCost] = useState(0);
  const [teacherBonus, setTeacherBonus] = useState(0);
  const [discountValue, setDiscountValue] = useState(0);

  useEffect(() => {
    if (account) {
      loadStudentRequests();
    }
  }, [account]);

  useEffect(() => {
    calculateCosts();
  }, [coursePrice, discountPercent]);

  const calculateCosts = () => {
    if (!coursePrice || coursePrice <= 0) {
      setTeoCost(0);
      setTeacherBonus(0);
      setDiscountValue(0);
      return;
    }

    const price = parseFloat(coursePrice);
    const discount = (price * discountPercent) / 100;
    const teoRequired = (discount * 10); // 1 TEO = 0.10 EUR, so 10 TEO = 1 EUR
    const bonus = (teoRequired * 25) / 100; // 25% bonus

    setDiscountValue(discount);
    setTeoCost(teoRequired);
    setTeacherBonus(bonus);
  };

  const loadStudentRequests = async () => {
    try {
      setLoadingRequests(true);
      const response = await fetch(`/api/discount/student/${account}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setStudentRequests(data.requests || []);
      } else {
        console.error('Failed to load student requests');
      }
    } catch (error) {
      console.error('Error loading student requests:', error);
    } finally {
      setLoadingRequests(false);
    }
  };

  const handleRequestDiscount = async () => {
    if (!account || !web3Provider) {
      showNotification('Please connect your wallet first', 'error');
      return;
    }

    if (!courseId || !coursePrice || !teacherAddress) {
      showNotification('Please fill in all fields', 'error');
      return;
    }

    if (!ethers.utils.isAddress(teacherAddress)) {
      showNotification('Invalid teacher address', 'error');
      return;
    }

    if (teoCost > teoBalance) {
      showNotification(`Insufficient TEO balance. You need ${teoCost} TEO but have ${teoBalance} TEO`, 'error');
      return;
    }

    try {
      setLoading(true);

      // Step 1: Get signature data from backend
      const signatureResponse = await fetch('/api/discount/signature-data/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          student_address: account,
          course_id: parseInt(courseId),
          course_price: parseFloat(coursePrice),
          discount_percent: discountPercent,
        }),
      });

      if (!signatureResponse.ok) {
        throw new Error('Failed to get signature data');
      }

      const sigData = await signatureResponse.json();
      setSignatureData(sigData);
      setSignatureDialog(true);
      
    } catch (error) {
      console.error('Error requesting discount:', error);
      showNotification(error.message || 'Failed to create discount request', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSignAndSubmit = async () => {
    if (!signatureData || !web3Provider) return;

    try {
      setLoading(true);

      // Sign the message with MetaMask
      const signer = web3Provider.getSigner();
      const signature = await signer.signMessage(signatureData.signable_message);

      // Submit the signed request
      const response = await fetch('/api/discount/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          student_address: account,
          teacher_address: teacherAddress,
          course_id: parseInt(courseId),
          course_price: parseFloat(coursePrice),
          discount_percent: discountPercent,
          student_signature: signature,
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showNotification(
          `Discount request created successfully! Request ID: ${result.request_id}`,
          'success'
        );
        
        // Clear form
        setCourseId('');
        setCoursePrice('');
        setTeacherAddress('');
        setDiscountPercent(10);
        
        // Refresh requests list
        await loadStudentRequests();
        
        // Close dialog
        setSignatureDialog(false);
        setSignatureData(null);
        
      } else {
        throw new Error(result.error || 'Failed to create discount request');
      }

    } catch (error) {
      console.error('Error signing and submitting:', error);
      showNotification(error.message || 'Failed to sign and submit request', 'error');
    } finally {
      setLoading(false);
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

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <LocalOffer sx={{ mr: 1, verticalAlign: 'middle' }} />
          TeoCoin Course Discounts
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Get discounts on courses by spending TEoCoin - completely gas-free!
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Request Form */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Request Course Discount
              </Typography>
              
              {/* Current Balance */}
              <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceWallet color="primary" />
                  <Typography variant="body1">
                    <strong>Your TEO Balance:</strong> {teoBalance} TEO
                  </Typography>
                </Box>
              </Paper>

              {/* Form Fields */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Course ID"
                  type="number"
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value)}
                  fullWidth
                  required
                />
                
                <TextField
                  label="Course Price (EUR)"
                  type="number"
                  value={coursePrice}
                  onChange={(e) => setCoursePrice(e.target.value)}
                  fullWidth
                  required
                  inputProps={{ step: '0.01', min: '0' }}
                />
                
                <TextField
                  label="Teacher Wallet Address"
                  value={teacherAddress}
                  onChange={(e) => setTeacherAddress(e.target.value)}
                  fullWidth
                  required
                  placeholder="0x..."
                />

                {/* Discount Slider */}
                <Box>
                  <Typography gutterBottom>
                    Discount Percentage: {discountPercent}%
                  </Typography>
                  <Slider
                    value={discountPercent}
                    onChange={(e, newValue) => setDiscountPercent(newValue)}
                    min={5}
                    max={15}
                    step={5}
                    marks={[
                      { value: 5, label: '5%' },
                      { value: 10, label: '10%' },
                      { value: 15, label: '15%' }
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>

                {/* Cost Breakdown */}
                {coursePrice && (
                  <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Cost Breakdown:
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Typography variant="body2">
                        💰 Discount Value: €{discountValue.toFixed(2)}
                      </Typography>
                      <Typography variant="body2">
                        🪙 Your TEO Cost: {teoCost.toFixed(2)} TEO
                      </Typography>
                      <Typography variant="body2">
                        🎁 Teacher Bonus: {teacherBonus.toFixed(2)} TEO
                      </Typography>
                    </Box>
                  </Paper>
                )}

                <Button
                  variant="contained"
                  size="large"
                  onClick={handleRequestDiscount}
                  disabled={loading || !account || teoCost > teoBalance}
                  startIcon={loading ? <CircularProgress size={20} /> : <School />}
                >
                  {loading ? 'Processing...' : 'Request Discount'}
                </Button>

                {teoCost > teoBalance && (
                  <Alert severity="warning">
                    Insufficient TEO balance. You need {teoCost} TEO but have {teoBalance} TEO.
                  </Alert>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Request History */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Your Discount Requests
              </Typography>
              
              {loadingRequests ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : studentRequests.length === 0 ? (
                <Typography color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                  No discount requests yet
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {studentRequests.map((request) => (
                    <Paper key={request.request_id} sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle2">
                          Request #{request.request_id}
                        </Typography>
                        <Chip
                          icon={getStatusIcon(request.status)}
                          label={getStatusText(request.status)}
                          color={getStatusColor(request.status)}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary">
                        Course #{request.course_id} • {request.discount_percent}% discount
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Cost: {(request.teo_cost / 10**18).toFixed(2)} TEO
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Teacher: {`${request.teacher.slice(0, 6)}...${request.teacher.slice(-4)}`}
                      </Typography>
                      
                      {request.decline_reason && (
                        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                          Reason: {request.decline_reason}
                        </Typography>
                      )}
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Signature Dialog */}
      <Dialog open={signatureDialog} onClose={() => setSignatureDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Sign Discount Request</DialogTitle>
        <DialogContent>
          {signatureData && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                You're about to sign a pre-approval for this discount request. This allows the platform 
                to execute the transfer when your teacher approves, without requiring additional signatures.
              </Alert>
              
              <Typography variant="body1" gutterBottom>
                <strong>Message:</strong> {signatureData.instructions.message}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Cost:</strong> {signatureData.instructions.cost}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {signatureData.instructions.note}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSignatureDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSignAndSubmit}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Signing...' : 'Sign & Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentDiscountInterface;
