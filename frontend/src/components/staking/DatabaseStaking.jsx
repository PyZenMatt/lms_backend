/**
 * � Database-Only Staking Component
 * 
 * Handles virtual staking using platform balance only.
 * No MetaMask interaction - pure database operations.
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Modal, Form, Alert, ProgressBar, Badge, Row, Col } from 'react-bootstrap';
import stakingService from '../../services/stakingService';
import { useAuth } from '../../contexts/AuthContext';

const DatabaseStaking = ({ onBalanceUpdate }) => {
  const { user } = useAuth();
  
  // State for real API data
  const [stakingInfo, setStakingInfo] = useState(null);
  const [stakingTiers, setStakingTiers] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Modal states
  const [showStakeModal, setShowStakeModal] = useState(false);
  const [showUnstakeModal, setShowUnstakeModal] = useState(false);
  const [stakeAmount, setStakeAmount] = useState('');
  const [unstakeAmount, setUnstakeAmount] = useState('');
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState('');

  // Check if user is a teacher
  const isTeacher = user?.role === 'teacher';

  // Load staking data on component mount (only for teachers)
  useEffect(() => {
    if (isTeacher) {
      loadStakingData();
    } else {
      setLoading(false);
    }
  }, [isTeacher]);

  const loadStakingData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Load staking info and tiers in parallel
      const [stakingResponse, tiersResponse] = await Promise.all([
        stakingService.getStakingInfo(),
        stakingService.getStakingTiers()
      ]);
      
      setStakingInfo(stakingResponse);
      setStakingTiers(tiersResponse.tiers);
      
    } catch (err) {
      console.error('Error loading staking data:', err);
      setError(err.message || 'Failed to load staking information');
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async () => {
    if (!stakeAmount || parseFloat(stakeAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (parseFloat(stakeAmount) > stakingInfo?.current_balance) {
      setError('Insufficient platform balance');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      const result = await stakingService.stakeTokens(parseFloat(stakeAmount));
      
      setSuccess(`Successfully staked ${stakeAmount} TEO! ${result.tier_upgraded ? `Congratulations! You've been upgraded to ${result.new_tier} tier!` : ''}`);
      setStakeAmount('');
      setShowStakeModal(false);
      
      // Reload staking data
      await loadStakingData();
      
      if (onBalanceUpdate) {
        onBalanceUpdate();
      }
      
    } catch (error) {
      console.error('Staking error:', error);
      setError(error.message || 'Failed to stake tokens');
    } finally {
      setProcessing(false);
    }
  };

  const handleUnstake = async () => {
    if (!unstakeAmount || parseFloat(unstakeAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (parseFloat(unstakeAmount) > stakingInfo?.staked_amount) {
      setError('Insufficient staked balance');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      const result = await stakingService.unstakeTokens(parseFloat(unstakeAmount));
      
      setSuccess(`Successfully unstaked ${unstakeAmount} TEO! ${result.tier_downgraded ? `Your tier has been updated to ${result.new_tier}.` : ''}`);
      setUnstakeAmount('');
      setShowUnstakeModal(false);
      
      // Reload staking data
      await loadStakingData();
      
      if (onBalanceUpdate) {
        onBalanceUpdate();
      }
      
    } catch (error) {
      console.error('Unstaking error:', error);
      setError(error.message || 'Failed to unstake tokens');
    } finally {
      setProcessing(false);
    }
  };

  const getTierInfo = (tierName) => {
    return stakingTiers?.[tierName] || {
      color: 'secondary',
      commission_rate: 50,
      teacher_earnings: 50
    };
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  // Show loading state
  if (loading) {
    return (
      <Card className="database-staking-card">
        <Card.Header className="bg-gradient-primary text-white">
          <h5 className="mb-0">
            <i className="feather icon-database me-2"></i>
            Database Staking
          </h5>
        </Card.Header>
        <Card.Body className="text-center p-4">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-muted">Loading staking information...</p>
        </Card.Body>
      </Card>
    );
  }

  // Show error state
  if (error && !stakingInfo) {
    return (
      <Card className="database-staking-card">
        <Card.Header className="bg-gradient-danger text-white">
          <h5 className="mb-0">
            <i className="feather icon-alert-circle me-2"></i>
            Error Loading Data
          </h5>
        </Card.Header>
        <Card.Body className="text-center p-4">
          <i className="feather icon-wifi-off text-muted" style={{ fontSize: '3rem' }}></i>
          <p className="mt-3 text-muted">{error}</p>
          <Button variant="primary" onClick={loadStakingData}>
            <i className="feather icon-refresh-cw me-2"></i>
            Retry
          </Button>
        </Card.Body>
      </Card>
    );
  }

  const tierInfo = getTierInfo(stakingInfo?.tier);

  // If user is not a teacher, show access denied message
  if (!isTeacher) {
    return (
      <Card className="database-staking-card">
        <Card.Header className="bg-gradient-secondary text-white">
          <h5 className="mb-0">
            <i className="feather icon-lock me-2"></i>
            Staking Not Available
          </h5>
        </Card.Header>
        <Card.Body className="text-center p-4">
          <i className="feather icon-users text-muted" style={{ fontSize: '4rem' }}></i>
          <h4 className="mt-3 mb-3">Students Cannot Stake</h4>
          <p className="text-muted mb-4">
            Staking is exclusively available for teachers to earn commission benefits. 
            As a student, you can use your TEO for course discounts instead.
          </p>
          <div className="alert alert-info">
            <i className="feather icon-info me-2"></i>
            <strong>For Students:</strong> Use your TEO tokens to get discounts on course purchases!
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <>
      <Card className="database-staking-card">
        <Card.Header className="bg-gradient-primary text-white">
          <h5 className="mb-0">
            <i className="feather icon-database me-2"></i>
            Database Staking
            <Badge bg="light" text="dark" className="ms-2">Virtual System</Badge>
          </h5>
        </Card.Header>

        <Card.Body>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError('')}>
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          )}
          {success && (
            <Alert variant="success" dismissible onClose={() => setSuccess('')}>
              <i className="feather icon-check-circle me-2"></i>
              {success}
            </Alert>
          )}

          {/* Current Staking Status */}
          <Row className="mb-4">
            <Col md={6}>
              <div className="text-center p-3 bg-light rounded">
                <h4 className="text-primary mb-1">{formatAmount(stakingInfo?.current_balance)} TEO</h4>
                <p className="text-muted mb-0">Available Balance</p>
              </div>
            </Col>
            <Col md={6}>
              <div className="text-center p-3 bg-light rounded">
                <h4 className="text-success mb-1">{formatAmount(stakingInfo?.staked_amount)} TEO</h4>
                <p className="text-muted mb-0">Staked Balance</p>
              </div>
            </Col>
          </Row>

          {/* Current Tier Display */}
          <div className="tier-display text-center p-3 rounded mb-4" style={{
            background: `linear-gradient(135deg, var(--bs-${tierInfo.color}) 0%, var(--bs-${tierInfo.color}) 100%)`,
            color: tierInfo.color === 'warning' || tierInfo.color === 'light' ? 'var(--bs-dark)' : 'white'
          }}>
            <h3 className="mb-2">
              <i className="feather icon-award me-2"></i>
              {stakingInfo?.tier} Tier
            </h3>
            <p className="mb-1">
              <strong>Platform Commission:</strong> {stakingInfo?.commission_rate}%
            </p>
            <p className="mb-0">
              <strong>Your Earnings:</strong> {stakingInfo?.teacher_earnings_percentage}%
            </p>
          </div>

          {/* Staking Actions */}
          <Row className="mb-4">
            <Col md={6}>
              <div className="d-grid">
                <Button 
                  variant="success" 
                  size="lg"
                  onClick={() => setShowStakeModal(true)}
                  disabled={!stakingInfo?.current_balance || stakingInfo.current_balance <= 0}
                >
                  <i className="feather icon-trending-up me-2"></i>
                  Stake More
                </Button>
              </div>
            </Col>
            <Col md={6}>
              <div className="d-grid">
                <Button 
                  variant="outline-warning" 
                  size="lg"
                  onClick={() => setShowUnstakeModal(true)}
                  disabled={!stakingInfo?.staked_amount || stakingInfo.staked_amount <= 0}
                >
                  <i className="feather icon-trending-down me-2"></i>
                  Unstake
                </Button>
              </div>
            </Col>
          </Row>

          {/* Next Tier Progress */}
          {stakingInfo?.next_tier_requirement && (
            <div className="next-tier-progress">
              <h6 className="mb-3">
                <i className="feather icon-target me-2"></i>
                Progress to Next Tier
              </h6>
              <div className="d-flex justify-content-between mb-2">
                <span className="small">Current: {formatAmount(stakingInfo.staked_amount)} TEO</span>
                <span className="small">Target: {formatAmount(stakingInfo.next_tier_requirement)} TEO</span>
              </div>
              <ProgressBar 
                now={(stakingInfo.staked_amount / stakingInfo.next_tier_requirement) * 100}
                variant="info"
                style={{ height: '8px' }}
              />
              <div className="text-center mt-2">
                <small className="text-muted">
                  Need {formatAmount(stakingInfo.next_tier_needed)} more TEO to upgrade
                </small>
              </div>
            </div>
          )}

          {/* Information Box */}
          <div className="alert alert-info">
            <i className="feather icon-info me-2"></i>
            <strong>Database Staking:</strong> Your TEO is staked virtually within the platform. 
            This affects your commission rates but doesn't involve blockchain transactions.
          </div>
        </Card.Body>
      </Card>

      {/* Stake Modal */}
      <Modal show={showStakeModal} onHide={() => setShowStakeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-trending-up me-2"></i>
            Stake TEO Tokens
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Amount to Stake</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={stakeAmount}
                onChange={(e) => setStakeAmount(e.target.value)}
                min="0"
                max={stakingInfo?.current_balance || 0}
                step="0.01"
              />
              <Form.Text className="text-muted">
                Available: {formatAmount(stakingInfo?.current_balance)} TEO
              </Form.Text>
            </Form.Group>

            <div className="alert alert-warning">
              <i className="feather icon-info me-2"></i>
              Staking will improve your commission rates and tier status.
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowStakeModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="success" 
            onClick={handleStake}
            disabled={processing || !stakeAmount}
          >
            {processing ? (
              <>
                <i className="feather icon-clock me-2"></i>
                Staking...
              </>
            ) : (
              <>
                <i className="feather icon-trending-up me-1"></i>
                Stake {stakeAmount} TEO
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Unstake Modal */}
      <Modal show={showUnstakeModal} onHide={() => setShowUnstakeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-trending-down me-2"></i>
            Unstake TEO Tokens
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Amount to Unstake</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={unstakeAmount}
                onChange={(e) => setUnstakeAmount(e.target.value)}
                min="0"
                max={stakingInfo?.staked_amount || 0}
                step="0.01"
              />
              <Form.Text className="text-muted">
                Staked: {formatAmount(stakingInfo?.staked_amount)} TEO
              </Form.Text>
            </Form.Group>

            <div className="alert alert-warning">
              <i className="feather icon-alert-triangle me-2"></i>
              Unstaking may reduce your tier and increase platform commission rates.
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowUnstakeModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="warning" 
            onClick={handleUnstake}
            disabled={processing || !unstakeAmount}
          >
            {processing ? (
              <>
                <i className="feather icon-clock me-2"></i>
                Unstaking...
              </>
            ) : (
              <>
                <i className="feather icon-trending-down me-1"></i>
                Unstake {unstakeAmount} TEO
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default DatabaseStaking;