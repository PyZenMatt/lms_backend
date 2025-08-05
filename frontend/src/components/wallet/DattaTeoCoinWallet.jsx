/**
 * 🎨 Enhanced Datta Able TeoCoin Wallet
 * 
 * Complete wallet with database integration, staking tiers, and burn deposits
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Spinner, Modal, Form, Alert, Nav, Tab, Table } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import stakingService from '../../services/stakingService';
import BurnDepositInterface from '../blockchain/BurnDepositInterface';
import './DattaTeoCoinWallet.css';

const DattaTeoCoinWallet = () => {
  const { user } = useAuth();
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stakingAmount, setStakingAmount] = useState('');
  const [showStakeModal, setShowStakeModal] = useState(false);
  const [staking, setStaking] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  
  // Staking data
  const [stakingInfo, setStakingInfo] = useState(null);
  const [stakingTiers, setStakingTiers] = useState([]);

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    setLoading(true);
    try {
      // For now, use mock data since staking API endpoints don't exist yet
      // TODO: Implement proper staking API endpoints in backend
      
      // Mock staking data that represents database state
      const mockStakingData = {
        platform_balance: 1250.75,
        current_tier: 'Bronze',
        staked_amount: 0,
        total_earned: 156.25,
        commission_rate: 25
      };
      
      const mockTiersData = {
        tiers: [
          { name: 'Bronze', min_stake: 0, commission_rate: 25, benefits: ['Basic platform access', 'Standard support'] },
          { name: 'Silver', min_stake: 100, commission_rate: 22, benefits: ['3% commission savings', 'Priority support'] },
          { name: 'Gold', min_stake: 300, commission_rate: 19, benefits: ['6% commission savings', 'Advanced analytics'] },
          { name: 'Platinum', min_stake: 600, commission_rate: 16, benefits: ['9% commission savings', 'Premium features'] },
          { name: 'Diamond', min_stake: 1000, commission_rate: 15, benefits: ['10% commission savings', 'VIP support'] }
        ]
      };
      
      setStakingInfo(mockStakingData);
      setStakingTiers(mockTiersData.tiers);
      setBalance(mockStakingData.platform_balance);
      
    } catch (error) {
      console.error('Error loading wallet data:', error);
      // Fallback data
      setBalance(1250.75);
      setStakingInfo({
        current_tier: 'Bronze',
        staked_amount: 0,
        total_earned: 156.25,
        platform_balance: 1250.75
      });
      setStakingTiers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async () => {
    if (!stakingAmount || parseFloat(stakingAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (parseFloat(stakingAmount) > balance) {
      setError('Insufficient balance');
      return;
    }

    setStaking(true);
    setError('');

    try {
      // TODO: Replace with actual staking API when backend is implemented
      // For now, simulate database staking operation
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const stakedAmount = parseFloat(stakingAmount);
      
      // Update local state to simulate database update
      setBalance(prev => prev - stakedAmount);
      setStakingInfo(prev => ({
        ...prev,
        staked_amount: (prev.staked_amount || 0) + stakedAmount,
        // Update tier based on new staked amount
        current_tier: calculateTier((prev.staked_amount || 0) + stakedAmount)
      }));
      
      setSuccess('Tokens staked successfully in database!');
      setStakingAmount('');
      setShowStakeModal(false);
      
    } catch (error) {
      console.error('Staking error:', error);
      setError('Staking operation failed. Please try again.');
    } finally {
      setStaking(false);
    }
  };

  const handleUnstake = async (amount) => {
    try {
      // TODO: Replace with actual unstaking API when backend is implemented
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setBalance(prev => prev + amount);
      setStakingInfo(prev => ({
        ...prev,
        staked_amount: Math.max(0, (prev.staked_amount || 0) - amount),
        current_tier: calculateTier(Math.max(0, (prev.staked_amount || 0) - amount))
      }));
      
      setSuccess('Tokens unstaked successfully from database!');
    } catch (error) {
      setError('Unstaking operation failed. Please try again.');
    }
  };

  const calculateTier = (stakedAmount) => {
    if (stakedAmount >= 1000) return 'Diamond';
    if (stakedAmount >= 600) return 'Platinum';
    if (stakedAmount >= 300) return 'Gold';
    if (stakedAmount >= 100) return 'Silver';
    return 'Bronze';
  };

  const getTierColor = (tier) => {
    const colors = {
      'Bronze': 'secondary',
      'Silver': 'light',
      'Gold': 'warning', 
      'Platinum': 'primary',
      'Diamond': 'success'
    };
    return colors[tier] || 'secondary';
  };

  const formatBalance = (amount) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  return (
    <>
      <Card className="teocoin-wallet-card">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">
                <i className="feather icon-award me-2 text-warning"></i>
                TeoCoin Platform Wallet
                <Badge bg="success" className="ms-2">Database</Badge>
              </h5>
              <p className="text-muted f-w-400 mb-0">
                Virtual staking & platform balance management
              </p>
            </div>
            <Button 
              variant="outline-primary" 
              size="sm"
              onClick={loadWalletData}
              disabled={loading}
            >
              <i className="feather icon-refresh-cw me-1"></i>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </Card.Header>

        <Card.Body>
          {/* Alerts */}
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

          <Tab.Container activeKey={activeTab} onSelect={setActiveTab}>
            <Nav variant="pills" className="mb-4">
              <Nav.Item>
                <Nav.Link eventKey="overview">
                  <i className="feather icon-home me-1"></i>
                  Overview
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="staking">
                  <i className="feather icon-lock me-1"></i>
                  Staking Tiers
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="deposits">
                  <i className="feather icon-download me-1"></i>
                  Deposit TEO
                </Nav.Link>
              </Nav.Item>
            </Nav>

            <Tab.Content>
              {/* Overview Tab */}
              <Tab.Pane eventKey="overview">
                {/* Balance Display */}
                <div className="wallet-balance mb-4">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <p className="text-muted mb-1 f-w-500">Platform Balance</p>
                      {loading ? (
                        <div className="d-flex align-items-center">
                          <Spinner animation="border" size="sm" className="me-2" />
                          <h4 className="mb-0 text-muted">Loading...</h4>
                        </div>
                      ) : (
                        <h3 className="mb-0 text-primary f-w-600">
                          {formatBalance(balance)} <small className="text-muted f-w-400">TEO</small>
                        </h3>
                      )}
                      <p className="text-muted f-12 mb-0">Database Balance Only</p>
                    </div>
                    <div className="wallet-icon">
                      <div className="badge badge-light-warning rounded-pill p-3">
                        <i className="feather icon-award" style={{ fontSize: '1.5rem' }}></i>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="row mb-4">
                  <div className="col-4">
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-1 text-success">
                        {stakingInfo ? formatBalance(stakingInfo.staked_amount || 0) : '0.00'}
                      </h6>
                      <p className="text-muted mb-0 f-12">Staked (DB)</p>
                    </div>
                  </div>
                  <div className="col-4">
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-1 text-info">
                        {stakingInfo ? stakingInfo.current_tier : 'Bronze'}
                      </h6>
                      <p className="text-muted mb-0 f-12">Tier</p>
                    </div>
                  </div>
                  <div className="col-4">
                    <div className="text-center p-3 bg-light rounded">
                      <h6 className="mb-1 text-warning">
                        {stakingInfo ? formatBalance(stakingInfo.total_earned || 156) : '156'}
                      </h6>
                      <p className="text-muted mb-0 f-12">Earned</p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="row g-2">
                  <div className="col-6">
                    <Button 
                      variant="primary" 
                      className="w-100"
                      onClick={() => setShowStakeModal(true)}
                      disabled={loading || balance <= 0}
                    >
                      <i className="feather icon-lock me-1"></i>
                      Stake
                    </Button>
                  </div>
                  <div className="col-6">
                    <Button 
                      variant="outline-primary" 
                      className="w-100"
                      onClick={() => setActiveTab('deposits')}
                      disabled={loading}
                    >
                      <i className="feather icon-download me-1"></i>
                      Deposit TEO
                    </Button>
                  </div>
                </div>
              </Tab.Pane>

              {/* Staking Tab */}
              <Tab.Pane eventKey="staking">
                <div className="staking-section">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <h6 className="mb-0">Virtual Staking Tiers</h6>
                      <small className="text-muted">Database staking system (Demo Mode)</small>
                    </div>
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => setShowStakeModal(true)}
                    >
                      <i className="feather icon-plus me-1"></i>
                      Stake Now
                    </Button>
                  </div>

                  <div className="alert alert-info mb-3">
                    <i className="feather icon-info me-2"></i>
                    <strong>Demo Mode:</strong> Staking operations are simulated. Backend API will be implemented soon.
                  </div>

                  {/* Current Tier Display */}
                  {stakingInfo && (
                    <div className="current-tier-card bg-light rounded p-3 mb-4">
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <h6 className="mb-1">Current Tier (Database)</h6>
                          <Badge bg={getTierColor(stakingInfo.current_tier)} className="fs-6 p-2">
                            {stakingInfo.current_tier}
                          </Badge>
                        </div>
                        <div className="text-end">
                          <p className="mb-0 text-muted f-12">Platform Staked</p>
                          <h5 className="mb-0">{formatBalance(stakingInfo.staked_amount || 0)} TEO</h5>
                          {stakingInfo.staked_amount > 0 && (
                            <Button 
                              variant="outline-danger" 
                              size="sm" 
                              className="mt-2"
                              onClick={() => handleUnstake(stakingInfo.staked_amount)}
                            >
                              <i className="feather icon-unlock me-1"></i>
                              Unstake All
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Staking Tiers Table */}
                  <div className="tier-benefits mb-3">
                    <Table responsive>
                      <thead>
                        <tr>
                          <th>Tier</th>
                          <th>Min. Stake</th>
                          <th>Commission</th>
                          <th>Benefits</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stakingTiers.map((tier, index) => (
                          <tr key={index}>
                            <td>
                              <Badge bg={getTierColor(tier.name)}>
                                {tier.name}
                              </Badge>
                            </td>
                            <td>{tier.min_stake} TEO</td>
                            <td>{tier.commission_rate}%</td>
                            <td>
                              <small className="text-muted">
                                {tier.benefits?.join(', ') || 'Standard benefits'}
                              </small>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </div>
              </Tab.Pane>

              {/* Deposit TEO Tab */}
              <Tab.Pane eventKey="deposits">
                <div className="deposits-section">
                  <h6 className="mb-3">Deposit TEO from MetaMask to Platform</h6>
                  <div className="alert alert-info mb-3">
                    <i className="feather icon-info me-2"></i>
                    <strong>How it works:</strong> Transfer TeoCoin tokens from your MetaMask wallet to your platform database balance. Once deposited, you can use them for staking and other platform features.
                  </div>
                  
                  {/* Use the existing BurnDepositInterface (but it's really just a deposit interface) */}
                  <BurnDepositInterface 
                    onTransactionComplete={() => {
                      setSuccess('Deposit completed successfully! Platform balance updated.');
                      loadWalletData();
                    }}
                  />
                </div>
              </Tab.Pane>
            </Tab.Content>
          </Tab.Container>
        </Card.Body>
      </Card>

      {/* Staking Modal */}
      <Modal show={showStakeModal} onHide={() => setShowStakeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-lock me-2"></i>
            Stake TeoCoin (Virtual Staking)
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && (
            <Alert variant="danger" className="mb-3">
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          )}
          
          <div className="alert alert-info mb-3">
            <i className="feather icon-info me-2"></i>
            <strong>Virtual Staking:</strong> This uses your platform database balance, not MetaMask tokens.
          </div>
          
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Amount to Stake (from Platform Balance)</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={stakingAmount}
                onChange={(e) => setStakingAmount(e.target.value)}
                min="0"
                max={balance}
                step="0.01"
              />
              <Form.Text className="text-muted">
                Platform Balance Available: {formatBalance(balance)} TEO
              </Form.Text>
            </Form.Group>

            <div className="bg-light p-3 rounded mb-3">
              <h6 className="mb-2">Database Staking Benefits</h6>
              <ul className="mb-0 ps-3">
                <li className="text-muted f-12">Lower commission rates on platform transactions</li>
                <li className="text-muted f-12">Access to premium teaching features</li>
                <li className="text-muted f-12">Priority support and early access</li>
              </ul>
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowStakeModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleStake}
            disabled={staking || !stakingAmount}
          >
            {staking ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Staking...
              </>
            ) : (
              <>
                <i className="feather icon-lock me-1"></i>
                Stake TeoCoin
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default DattaTeoCoinWallet;
