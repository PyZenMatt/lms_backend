/**
 * 🎨 Enhanced TeoCoin Wallet with Staking Tiers & Burn Deposits
 * 
 * Complete wallet component for teachers with:
 * - Real database integration
 * - Staking tiers (Basic, Premium, Pro)
 * - Burn deposit functionality
 * - Transaction history
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Spinner, Modal, Form, Alert, Nav, Tab, Table, ProgressBar } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import * as teocoinAPI from '../../services/api/teocoin';
import './EnhancedTeoCoinWallet.css';

const EnhancedTeoCoinWallet = () => {
  const { user } = useAuth();
  const [walletData, setWalletData] = useState({
    balance: 0,
    stakedAmount: 0,
    totalEarned: 0
  });
  const [stakingPositions, setStakingPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Modals
  const [showStakeModal, setShowStakeModal] = useState(false);
  const [showBurnModal, setShowBurnModal] = useState(false);
  
  // Form states
  const [stakeForm, setStakeForm] = useState({
    amount: '',
    tier: 'basic'
  });
  const [burnForm, setBurnForm] = useState({
    txHash: '',
    amount: '',
    metamaskAddress: ''
  });
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    setLoading(true);
    try {
      const [balanceData, stakingData] = await Promise.all([
        teocoinAPI.getWalletBalance(),
        teocoinAPI.getStakingPositions()
      ]);
      
      setWalletData(balanceData);
      setStakingPositions(stakingData.positions || []);
    } catch (error) {
      console.error('Error loading wallet data:', error);
      setError('Failed to load wallet data');
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async () => {
    if (!stakeForm.amount || parseFloat(stakeForm.amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    const tierInfo = teocoinAPI.getStakingTierInfo(stakeForm.tier);
    if (parseFloat(stakeForm.amount) < tierInfo.minAmount) {
      setError(`Minimum amount for ${tierInfo.name} tier is ${tierInfo.minAmount} TEO`);
      return;
    }

    if (parseFloat(stakeForm.amount) > walletData.balance) {
      setError('Insufficient balance');
      return;
    }

    setActionLoading(true);
    setError('');

    try {
      await teocoinAPI.stakeTokens(stakeForm.amount, stakeForm.tier);
      setSuccess('Tokens staked successfully!');
      setStakeForm({ amount: '', tier: 'basic' });
      setShowStakeModal(false);
      await loadWalletData();
    } catch (error) {
      setError(error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnstake = async (stakingId) => {
    setActionLoading(true);
    try {
      await teocoinAPI.unstakeTokens(stakingId);
      setSuccess('Tokens unstaked successfully!');
      await loadWalletData();
    } catch (error) {
      setError(error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBurnDeposit = async () => {
    if (!burnForm.txHash || !burnForm.amount || !burnForm.metamaskAddress) {
      setError('All fields are required for burn deposit');
      return;
    }

    setActionLoading(true);
    setError('');

    try {
      await teocoinAPI.burnDeposit(burnForm.txHash, burnForm.amount, burnForm.metamaskAddress);
      setSuccess('Burn deposit processed successfully!');
      setBurnForm({ txHash: '', amount: '', metamaskAddress: '' });
      setShowBurnModal(false);
      await loadWalletData();
    } catch (error) {
      setError(error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const getStakingTierBadge = (tier) => {
    const tierInfo = teocoinAPI.getStakingTierInfo(tier);
    return <Badge bg={tierInfo.color}>{tierInfo.name}</Badge>;
  };

  const calculateStakingRewards = (amount, apy, days) => {
    return (parseFloat(amount) * (apy / 100) * (days / 365)).toFixed(4);
  };

  return (
    <>
      <Card className="enhanced-teocoin-wallet">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">
                <i className="feather icon-award me-2 text-warning"></i>
                TeoCoin Wallet
                <Badge bg="success" className="ms-2">Enhanced</Badge>
              </h5>
              <p className="text-muted f-w-400 mb-0">
                Complete staking & rewards platform
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
                  Staking
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="deposits">
                  <i className="feather icon-download me-1"></i>
                  Burn Deposits
                </Nav.Link>
              </Nav.Item>
            </Nav>

            <Tab.Content>
              {/* Overview Tab */}
              <Tab.Pane eventKey="overview">
                {/* Balance Display */}
                <div className="wallet-overview mb-4">
                  <div className="row">
                    <div className="col-md-4">
                      <div className="balance-card bg-primary text-white rounded p-3 mb-3">
                        <div className="d-flex justify-content-between align-items-center">
                          <div>
                            <p className="mb-1 opacity-75">Available Balance</p>
                            {loading ? (
                              <div className="d-flex align-items-center">
                                <Spinner animation="border" size="sm" className="me-2" />
                                <h4 className="mb-0">Loading...</h4>
                              </div>
                            ) : (
                              <h3 className="mb-0">{teocoinAPI.formatTeoAmount(walletData.balance)} TEO</h3>
                            )}
                          </div>
                          <i className="feather icon-dollar-sign" style={{ fontSize: '2rem', opacity: 0.7 }}></i>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="balance-card bg-warning text-white rounded p-3 mb-3">
                        <div className="d-flex justify-content-between align-items-center">
                          <div>
                            <p className="mb-1 opacity-75">Staked Amount</p>
                            <h3 className="mb-0">{teocoinAPI.formatTeoAmount(walletData.stakedAmount)} TEO</h3>
                          </div>
                          <i className="feather icon-lock" style={{ fontSize: '2rem', opacity: 0.7 }}></i>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="balance-card bg-success text-white rounded p-3 mb-3">
                        <div className="d-flex justify-content-between align-items-center">
                          <div>
                            <p className="mb-1 opacity-75">Total Earned</p>
                            <h3 className="mb-0">{teocoinAPI.formatTeoAmount(walletData.totalEarned)} TEO</h3>
                          </div>
                          <i className="feather icon-trending-up" style={{ fontSize: '2rem', opacity: 0.7 }}></i>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="quick-actions">
                  <h6 className="mb-3">Quick Actions</h6>
                  <div className="row g-2">
                    <div className="col-6 col-md-3">
                      <Button 
                        variant="primary" 
                        className="w-100"
                        onClick={() => setShowStakeModal(true)}
                        disabled={loading || walletData.balance <= 0}
                      >
                        <i className="feather icon-lock me-1"></i>
                        Stake
                      </Button>
                    </div>
                    <div className="col-6 col-md-3">
                      <Button 
                        variant="warning" 
                        className="w-100"
                        onClick={() => setShowBurnModal(true)}
                        disabled={loading}
                      >
                        <i className="feather icon-download me-1"></i>
                        Burn Deposit
                      </Button>
                    </div>
                    <div className="col-6 col-md-3">
                      <Button 
                        variant="outline-primary" 
                        className="w-100"
                        disabled={loading}
                      >
                        <i className="feather icon-send me-1"></i>
                        Transfer
                      </Button>
                    </div>
                    <div className="col-6 col-md-3">
                      <Button 
                        variant="outline-secondary" 
                        className="w-100"
                        disabled={loading}
                      >
                        <i className="feather icon-download-cloud me-1"></i>
                        Withdraw
                      </Button>
                    </div>
                  </div>
                </div>
              </Tab.Pane>

              {/* Staking Tab */}
              <Tab.Pane eventKey="staking">
                <div className="staking-section">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h6 className="mb-0">Staking Positions</h6>
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => setShowStakeModal(true)}
                    >
                      <i className="feather icon-plus me-1"></i>
                      New Stake
                    </Button>
                  </div>

                  {/* Staking Tiers Info */}
                  <div className="staking-tiers mb-4">
                    <div className="row">
                      {['basic', 'premium', 'pro'].map(tier => {
                        const tierInfo = teocoinAPI.getStakingTierInfo(tier);
                        return (
                          <div key={tier} className="col-md-4 mb-3">
                            <div className="tier-card border rounded p-3">
                              <div className="d-flex justify-content-between align-items-center mb-2">
                                <h6 className="mb-0">{tierInfo.name}</h6>
                                <Badge bg={tierInfo.color}>{tierInfo.apy}% APY</Badge>
                              </div>
                              <p className="text-muted f-12 mb-2">
                                Min: {tierInfo.minAmount} TEO<br/>
                                Lock: {tierInfo.lockPeriod} days
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Active Positions */}
                  {stakingPositions.length > 0 ? (
                    <Table responsive>
                      <thead>
                        <tr>
                          <th>Amount</th>
                          <th>Tier</th>
                          <th>APY</th>
                          <th>Rewards</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stakingPositions.map((position, index) => {
                          const tierInfo = teocoinAPI.getStakingTierInfo(position.tier);
                          const daysStaked = Math.floor((Date.now() - new Date(position.created_at)) / (1000 * 60 * 60 * 24));
                          const estimatedRewards = calculateStakingRewards(position.amount, tierInfo.apy, daysStaked);
                          
                          return (
                            <tr key={index}>
                              <td>{teocoinAPI.formatTeoAmount(position.amount)} TEO</td>
                              <td>{getStakingTierBadge(position.tier)}</td>
                              <td>{tierInfo.apy}%</td>
                              <td>{estimatedRewards} TEO</td>
                              <td>
                                <Badge bg={position.is_locked ? 'warning' : 'success'}>
                                  {position.is_locked ? 'Locked' : 'Unlocked'}
                                </Badge>
                              </td>
                              <td>
                                {!position.is_locked && (
                                  <Button 
                                    variant="outline-danger" 
                                    size="sm"
                                    onClick={() => handleUnstake(position.id)}
                                    disabled={actionLoading}
                                  >
                                    <i className="feather icon-unlock me-1"></i>
                                    Unstake
                                  </Button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Table>
                  ) : (
                    <div className="text-center py-4">
                      <i className="feather icon-lock text-muted" style={{ fontSize: '3rem' }}></i>
                      <p className="text-muted mt-2">No active staking positions</p>
                      <Button variant="primary" onClick={() => setShowStakeModal(true)}>
                        Start Staking
                      </Button>
                    </div>
                  )}
                </div>
              </Tab.Pane>

              {/* Burn Deposits Tab */}
              <Tab.Pane eventKey="deposits">
                <div className="burn-deposits-section">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h6 className="mb-0">Burn Deposits</h6>
                    <Button 
                      variant="warning" 
                      size="sm"
                      onClick={() => setShowBurnModal(true)}
                    >
                      <i className="feather icon-download me-1"></i>
                      New Deposit
                    </Button>
                  </div>

                  <div className="burn-info bg-light rounded p-3 mb-3">
                    <h6 className="mb-2">
                      <i className="feather icon-info me-2"></i>
                      How Burn Deposits Work
                    </h6>
                    <ol className="mb-0 f-12">
                      <li>Send TeoCoin tokens from your MetaMask to the burn address</li>
                      <li>Copy the transaction hash from MetaMask</li>
                      <li>Submit the transaction details here to credit your platform balance</li>
                      <li>Your platform balance will be updated within minutes</li>
                    </ol>
                  </div>
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
            Stake TeoCoin
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Staking Tier</Form.Label>
              <Form.Select
                value={stakeForm.tier}
                onChange={(e) => setStakeForm(prev => ({ ...prev, tier: e.target.value }))}
              >
                {['basic', 'premium', 'pro'].map(tier => {
                  const tierInfo = teocoinAPI.getStakingTierInfo(tier);
                  return (
                    <option key={tier} value={tier}>
                      {tierInfo.name} - {tierInfo.apy}% APY (Min: {tierInfo.minAmount} TEO)
                    </option>
                  );
                })}
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Amount to Stake</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={stakeForm.amount}
                onChange={(e) => setStakeForm(prev => ({ ...prev, amount: e.target.value }))}
                min="0"
                max={walletData.balance}
                step="0.01"
              />
              <Form.Text className="text-muted">
                Available: {teocoinAPI.formatTeoAmount(walletData.balance)} TEO
              </Form.Text>
            </Form.Group>

            {stakeForm.tier && (
              <div className="bg-light p-3 rounded">
                <h6 className="mb-2">Staking Details</h6>
                {(() => {
                  const tierInfo = teocoinAPI.getStakingTierInfo(stakeForm.tier);
                  return (
                    <ul className="mb-0 f-12">
                      <li>APY: {tierInfo.apy}%</li>
                      <li>Lock Period: {tierInfo.lockPeriod} days</li>
                      <li>Minimum Amount: {tierInfo.minAmount} TEO</li>
                    </ul>
                  );
                })()}
              </div>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowStakeModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleStake}
            disabled={actionLoading || !stakeForm.amount}
          >
            {actionLoading ? (
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

      {/* Burn Deposit Modal */}
      <Modal show={showBurnModal} onHide={() => setShowBurnModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="feather icon-download me-2"></i>
            Burn Deposit
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Transaction Hash</Form.Label>
              <Form.Control
                type="text"
                placeholder="0x..."
                value={burnForm.txHash}
                onChange={(e) => setBurnForm(prev => ({ ...prev, txHash: e.target.value }))}
              />
              <Form.Text className="text-muted">
                Copy this from your MetaMask transaction
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Amount (TEO)</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={burnForm.amount}
                onChange={(e) => setBurnForm(prev => ({ ...prev, amount: e.target.value }))}
                min="0"
                step="0.01"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>MetaMask Address</Form.Label>
              <Form.Control
                type="text"
                placeholder="0x..."
                value={burnForm.metamaskAddress}
                onChange={(e) => setBurnForm(prev => ({ ...prev, metamaskAddress: e.target.value }))}
              />
              <Form.Text className="text-muted">
                The address you sent from
              </Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setShowBurnModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="warning" 
            onClick={handleBurnDeposit}
            disabled={actionLoading || !burnForm.txHash || !burnForm.amount || !burnForm.metamaskAddress}
          >
            {actionLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Processing...
              </>
            ) : (
              <>
                <i className="feather icon-download me-1"></i>
                Process Deposit
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default EnhancedTeoCoinWallet;
