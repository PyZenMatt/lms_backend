import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Spinner, Badge } from 'react-bootstrap';
import stakingService from '../../services/stakingService';
import { useAuth } from '../../contexts/AuthContext';
import './TeoCoinBalanceWidget.scss';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const TeoCoinBalanceWidget = ({ variant = 'default', onWithdrawalClick }) => {
  const { user } = useAuth();
  const [stakingInfo, setStakingInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pendingWithdrawals, setPendingWithdrawals] = useState(0);

  // Check if user is a teacher or admin
  const isTeacher = user?.role === 'teacher';
  const isAdmin = user?.role === 'admin';
  const isStudent = user?.role === 'student' || (!isTeacher && !isAdmin);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      setError('');

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      if (isTeacher) {
        // Use the staking service to get balance data for teachers only
        console.log('🔄 TeoCoinBalanceWidget: Fetching staking info for teacher');
        const response = await stakingService.getStakingInfo();
        setStakingInfo(response);

        // Get pending withdrawals for teachers and admins too
        try {
          const withdrawalResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/history/`, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (withdrawalResponse.ok) {
            const withdrawalData = await withdrawalResponse.json();
            if (withdrawalData.success) {
              const pending = withdrawalData.withdrawals?.filter((w) => w.status === 'pending' || w.status === 'processing').length || 0;
              setPendingWithdrawals(pending);
            }
          }
        } catch (withdrawalErr) {
          console.warn('Failed to load pending withdrawals:', withdrawalErr);
        }
      } else if (isAdmin) {
        // For admins, use the student balance API (no staking access)
        console.log('🔄 TeoCoinBalanceWidget: Fetching balance for admin (using student endpoint)');
        const balanceResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/balance/`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!balanceResponse.ok) {
          throw new Error(`Admin balance API error! status: ${balanceResponse.status}`);
        }

        const balanceData = await balanceResponse.json();

        // Extract balance data correctly for admins (similar to students)
        const adminBalance = balanceData.success && balanceData.balance ? parseFloat(balanceData.balance.available || 0) : 0;

        setStakingInfo({
          current_balance: adminBalance,
          staked_amount: 0, // Admins can't stake
          tier: 'Admin',
          commission_rate: null,
          teacher_earnings_percentage: null
        });

        // Get pending withdrawals for admin
        try {
          const withdrawalResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/history/`, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (withdrawalResponse.ok) {
            const withdrawalData = await withdrawalResponse.json();
            if (withdrawalData.success) {
              const pending = withdrawalData.withdrawals?.filter((w) => w.status === 'pending' || w.status === 'processing').length || 0;
              setPendingWithdrawals(pending);
            }
          }
        } catch (withdrawalErr) {
          console.warn('Failed to load pending withdrawals for admin:', withdrawalErr);
        }
      } else {
        // For students, use the new student balance API
        const balanceResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/balance/`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!balanceResponse.ok) {
          throw new Error(`Student balance API error! status: ${balanceResponse.status}`);
        }

        const balanceData = await balanceResponse.json();

        // Extract balance data correctly for students
        const studentBalance = balanceData.success && balanceData.balance ? parseFloat(balanceData.balance.available || 0) : 0;

        setStakingInfo({
          current_balance: studentBalance,
          staked_amount: 0, // Students can't stake
          tier: null,
          commission_rate: null,
          teacher_earnings_percentage: null
        });

        // Get pending withdrawals for both students and teachers
        try {
          const withdrawalResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/withdrawals/history/`, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (withdrawalResponse.ok) {
            const withdrawalData = await withdrawalResponse.json();
            if (withdrawalData.success) {
              const pending = withdrawalData.withdrawals?.filter((w) => w.status === 'pending' || w.status === 'processing').length || 0;
              setPendingWithdrawals(pending);
            }
          }
        } catch (withdrawalErr) {
          console.warn('Failed to load pending withdrawals:', withdrawalErr);
        }
      }
    } catch (err) {
      console.error('Failed to fetch balance:', err);
      if (err.message.includes('only available for teachers')) {
        // Try to get student balance using student API
        try {
          const token = localStorage.getItem('accessToken');
          const balanceResponse = await fetch(`${API_BASE_URL}/api/v1/teocoin/student/balance/`, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (balanceResponse.ok) {
            const balanceData = await balanceResponse.json();
            const studentBalance = balanceData.success && balanceData.balance ? parseFloat(balanceData.balance.available || 0) : 0;

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
            <Button variant="outline-light" size="sm" onClick={fetchBalance} disabled={loading} title="Refresh balance">
              {loading ? <Spinner animation="border" size="sm" /> : <i className="feather icon-refresh-cw"></i>}
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
            {isAdmin && (
              <div className="col-md-8">
                <div className="text-center p-3 bg-light rounded">
                  <h6 className="text-muted mb-1 small">Admin Access</h6>
                  <p className="text-warning mb-0">
                    <i className="feather icon-shield me-2"></i>
                    Full platform control and withdrawal management
                  </p>
                </div>
              </div>
            )}
            {!(isTeacher || isAdmin) && (
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
            <div
              className="text-center p-3 rounded mb-4"
              style={{
                background: 'linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(40, 167, 69, 0.05) 100%)'
              }}
            >
              <div className="d-flex align-items-center justify-content-center mb-2">
                <i className="feather icon-award text-success me-2" style={{ fontSize: '1.5rem' }}></i>
                <h5 className="text-success mb-0">{stakingInfo.tier} Tier</h5>
              </div>
              <p className="text-muted small mb-0">
                Earning {stakingInfo.teacher_earnings_percentage}% • Platform takes {stakingInfo.commission_rate}%
              </p>
            </div>
          )}

          {/* Admin Information */}
          {isAdmin && (
            <div
              className="text-center p-3 rounded mb-4"
              style={{
                background: 'linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%)'
              }}
            >
              <div className="d-flex align-items-center justify-content-center mb-2">
                <i className="feather icon-shield text-warning me-2" style={{ fontSize: '1.5rem' }}></i>
                <h5 className="text-warning mb-0">Administrator Access</h5>
              </div>
              <p className="text-muted small mb-0">Manage platform withdrawals and oversee all TeoCoin operations</p>
            </div>
          )}

          {/* Student Information */}
          {!(isTeacher || isAdmin) && (
            <div
              className="text-center p-3 rounded mb-4"
              style={{
                background: 'linear-gradient(135deg, rgba(23, 162, 184, 0.1) 0%, rgba(23, 162, 184, 0.05) 100%)'
              }}
            >
              <div className="d-flex align-items-center justify-content-center mb-2">
                <i className="feather icon-percent text-info me-2" style={{ fontSize: '1.5rem' }}></i>
                <h5 className="text-info mb-0">Student Account</h5>
              </div>
              <p className="text-muted small mb-0">Use your TEO tokens to get discounts on course purchases</p>
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

          {/* Withdrawal Button */}
          <div className="d-grid mb-3">
            {pendingWithdrawals >= 3 && (
              <Alert variant="warning" className="mb-2">
                <small>
                  <i className="feather icon-clock me-1"></i>
                  You have {pendingWithdrawals} pending withdrawals. Please wait before making new requests.
                </small>
              </Alert>
            )}
            <Button
              variant="success"
              size="sm"
              onClick={() => onWithdrawalClick && onWithdrawalClick()}
              disabled={loading || !stakingInfo?.current_balance || stakingInfo.current_balance <= 0 || pendingWithdrawals >= 3}
            >
              <i className="feather icon-send me-2"></i>
              Withdraw to MetaMask
              {pendingWithdrawals > 0 && pendingWithdrawals < 3 && (
                <Badge bg="light" text="dark" className="ms-2 small">
                  {pendingWithdrawals} pending
                </Badge>
              )}
            </Button>
          </div>

          {/* Information Text */}
          <div className="alert alert-info">
            <i className="feather icon-info me-2"></i>
            <small>
              {isTeacher
                ? 'Manage your TeoCoin: withdraw to MetaMask, stake for higher commissions, or deposit from MetaMask'
                : isAdmin
                  ? 'Manage your TeoCoin: withdraw to MetaMask, process withdrawals, or deposit from MetaMask'
                  : 'Manage your TeoCoin: withdraw to MetaMask, use for course discounts, or deposit from MetaMask'}
            </small>
          </div>
        </Card.Body>
      </Card>
    </>
  );
};

export default TeoCoinBalanceWidget;
