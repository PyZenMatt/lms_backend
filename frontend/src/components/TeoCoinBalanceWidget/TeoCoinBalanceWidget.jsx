const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Spinner, Badge } from 'react-bootstrap';
import TeoCoinManager from '../TeoCoinManager';
import stakingService from '../../services/stakingService';
import { useAuth } from '../../contexts/AuthContext';
import './TeoCoinBalanceWidget.scss';

const TeoCoinBalanceWidget = ({ variant = 'default' }) => {
  const { user } = useAuth();
  const [stakingInfo, setStakingInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);
  const [pendingWithdrawals, setPendingWithdrawals] = useState(0);

  // Check if user is a teacher
  const isTeacher = user?.role === 'teacher';

  const fetchBalance = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      if (isTeacher) {
        // Use the staking service to get balance data for teachers
        const response = await stakingService.getStakingInfo();
        setStakingInfo(response);
      } else {
        // For students, use the new student balance API
        const balanceResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/balance/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!balanceResponse.ok) {
          throw new Error(`Student balance API error! status: ${balanceResponse.status}`);
        }

        const balanceData = await balanceResponse.json();
        
        // Extract balance data correctly for students
        const studentBalance = balanceData.success && balanceData.balance 
          ? parseFloat(balanceData.balance.available || 0)
          : 0;

        setStakingInfo({
          current_balance: studentBalance,
          staked_amount: 0,   // Students can't stake
          tier: null,
          commission_rate: null,
          teacher_earnings_percentage: null
        });
      }
      
      // TODO: Get pending withdrawals from withdrawal API when available
      setPendingWithdrawals(0);
      
    } catch (err) {
      console.error('Failed to fetch balance:', err);
      if (err.message.includes('only available for teachers')) {
        // Try to get student balance using student API
        try {
          const token = localStorage.getItem('accessToken');
          const balanceResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/balance/`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          if (balanceResponse.ok) {
            const balanceData = await balanceResponse.json();
            const studentBalance = balanceData.success && balanceData.balance 
              ? parseFloat(balanceData.balance.available || 0)
              : 0;

            setStakingInfo({
              current_balance: studentBalance,
              staked_amount: 0,
              tier: null,
              commission_rate: null,
              teacher_earnings_percentage: null
            });
          } else {
            throw new Error('Failed to load student balance');
          }
        } catch (studentErr) {
          console.error('Failed to load student balance:', studentErr);
          setError('Failed to load balance information');
        }
      } else {
        setError('Failed to load balance information');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
    // Refresh balance every 30 seconds
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleWithdrawalClose = () => {
    setWithdrawalOpen(false);
    fetchBalance(); // Refresh balance after withdrawal
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  const totalBalance = (stakingInfo?.current_balance || 0) + (stakingInfo?.staked_amount || 0);

  if (variant === 'compact') {
    return (
      <>
        <Card className="teocoin-balance-widget-compact border-0 shadow-sm">
          <Card.Body className="p-3">
            <div className="d-flex align-items-center justify-content-between">
              <div className="d-flex align-items-center">
                <div className="me-3">
                  <i className="feather icon-dollar-sign text-primary" style={{ fontSize: '1.5rem' }}></i>
                </div>
                <div>
                  <h6 className="text-muted mb-1 small">TeoCoin Balance</h6>
                  {loading ? (
                    <div className="d-flex align-items-center">
                      <Spinner animation="border" size="sm" className="me-2" />
                      <span className="text-muted">Loading...</span>
                    </div>
                  ) : (
                    <h5 className="text-primary mb-0">{formatAmount(stakingInfo?.current_balance)} TEO</h5>
                  )}
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setWithdrawalOpen(true)}
                disabled={loading || !stakingInfo?.current_balance || stakingInfo.current_balance <= 0}
              >
                <i className="feather icon-send me-1"></i>
                Withdraw
              </Button>
            </div>
            {pendingWithdrawals > 0 && (
              <div className="mt-2">
                <Badge bg="warning" className="small">
                  {formatAmount(pendingWithdrawals)} TEO pending
                </Badge>
              </div>
            )}
          </Card.Body>
        </Card>

        <TeoCoinWithdrawal
          open={withdrawalOpen}
          onClose={handleWithdrawalClose}
          userBalance={stakingInfo?.current_balance || 0}
        />
      </>
    );
  }

  return (
    <>
      <Card className="teocoin-balance-widget border-0 shadow-sm">
        <Card.Header className="bg-gradient-success text-white border-0">
          <div className="d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center">
              <i className="feather icon-dollar-sign me-2" style={{ fontSize: '1.5rem' }}></i>
              <h5 className="mb-0">TeoCoin Wallet</h5>
            </div>
            <Button
              variant="outline-light"
              size="sm"
              onClick={fetchBalance}
              disabled={loading}
              title="Refresh balance"
            >
              {loading ? (
                <Spinner animation="border" size="sm" />
              ) : (
                <i className="feather icon-refresh-cw"></i>
              )}
            </Button>
          </div>
        </Card.Header>

        <Card.Body>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError('')}>
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          )}

          {/* Balance Overview */}
          <div className="row mb-4">
            <div className="col-md-4">
              <div className="text-center p-3 bg-light rounded">
                <h6 className="text-muted mb-1 small">Available</h6>
                {loading ? (
                  <div className="d-flex justify-content-center">
                    <Spinner animation="border" size="sm" />
                  </div>
                ) : (
                  <h4 className="text-success mb-0">{formatAmount(stakingInfo?.current_balance)} TEO</h4>
                )}
              </div>
            </div>
            {isTeacher && (
              <>
                <div className="col-md-4">
                  <div className="text-center p-3 bg-light rounded">
                    <h6 className="text-muted mb-1 small">Staked</h6>
                    {loading ? (
                      <div className="d-flex justify-content-center">
                        <Spinner animation="border" size="sm" />
                      </div>
                    ) : (
                      <h4 className="text-primary mb-0">{formatAmount(stakingInfo?.staked_amount)} TEO</h4>
                    )}
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="text-center p-3 bg-light rounded">
                    <h6 className="text-muted mb-1 small">Total Owned</h6>
                    {loading ? (
                      <div className="d-flex justify-content-center">
                        <Spinner animation="border" size="sm" />
                      </div>
                    ) : (
                      <h4 className="text-warning mb-0">{formatAmount(totalBalance)} TEO</h4>
                    )}
                  </div>
                </div>
              </>
            )}
            {!isTeacher && (
              <div className="col-md-8">
                <div className="text-center p-3 bg-light rounded">
                  <h6 className="text-muted mb-1 small">Usage</h6>
                  <p className="text-info mb-0">
                    <i className="feather icon-percent me-2"></i>
                    Use for course discounts
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Current Tier Display - Teachers only */}
          {stakingInfo && isTeacher && (
            <div className="text-center p-3 rounded mb-4" style={{
              background: 'linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(40, 167, 69, 0.05) 100%)'
            }}>
              <div className="d-flex align-items-center justify-content-center mb-2">
                <i className="feather icon-award text-success me-2" style={{ fontSize: '1.5rem' }}></i>
                <h5 className="text-success mb-0">{stakingInfo.tier} Tier</h5>
              </div>
              <p className="text-muted small mb-0">
                Earning {stakingInfo.teacher_earnings_percentage}% • Platform takes {stakingInfo.commission_rate}%
              </p>
            </div>
          )}

          {/* Student Information */}
          {!isTeacher && (
            <div className="text-center p-3 rounded mb-4" style={{
              background: 'linear-gradient(135deg, rgba(23, 162, 184, 0.1) 0%, rgba(23, 162, 184, 0.05) 100%)'
            }}>
              <div className="d-flex align-items-center justify-content-center mb-2">
                <i className="feather icon-percent text-info me-2" style={{ fontSize: '1.5rem' }}></i>
                <h5 className="text-info mb-0">Student Account</h5>
              </div>
              <p className="text-muted small mb-0">
                Use your TEO tokens to get discounts on course purchases
              </p>
            </div>
          )}

          {pendingWithdrawals > 0 && (
            <div className="mb-3">
              <Badge bg="warning" className="d-flex align-items-center justify-content-center p-2">
                <i className="feather icon-clock me-2"></i>
                {formatAmount(pendingWithdrawals)} TEO pending withdrawal
              </Badge>
            </div>
          )}

          {/* TeoCoin Manager Button */}
          <div className="d-grid mb-3">
            <Button
              variant="success"
              size="lg"
              onClick={() => setWithdrawalOpen(true)}
              disabled={loading || !stakingInfo?.current_balance || stakingInfo.current_balance <= 0}
            >
              <i className="feather icon-send me-2"></i>
              Manage TeoCoin
            </Button>
          </div>

          {/* Information Text */}
          <div className="alert alert-info">
            <i className="feather icon-info me-2"></i>
            <small>
              {isTeacher 
                ? "Manage your TeoCoin: withdraw to MetaMask, stake for higher commissions, or deposit from MetaMask"
                : "Manage your TeoCoin: withdraw to MetaMask, use for course discounts, or deposit from MetaMask"
              }
            </small>
          </div>
        </Card.Body>
      </Card>

      <TeoCoinManager
        open={withdrawalOpen}
        onClose={handleWithdrawalClose}
        userBalance={stakingInfo?.current_balance || 0}
      />
    </>
  );
};

export default TeoCoinBalanceWidget;
