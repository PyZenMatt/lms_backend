import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Alert, Button, Spinner } from 'react-bootstrap';
import { getRewardPoolInfo, getBlockchainTransactions } from '../../services/api/blockchain';
import RewardPoolSummary from '../../components/blockchain/RewardPoolSummary';
import RewardPoolRefill from '../../components/blockchain/RewardPoolRefill';
import ManualTeoCoinTransfer from '../../components/blockchain/ManualTeoCoinTransfer';
import BlockchainTransactions from '../../components/blockchain/BlockchainTransactions';
import MaticUsageChart from '../../components/blockchain/MaticUsageChart';
import './RewardPoolDashboard.scss';

const RewardPoolDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [poolInfo, setPoolInfo] = useState(null);
  const [transactions, setTransactions] = useState([]);
  
  const loadRewardPoolInfo = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await getRewardPoolInfo();
      setPoolInfo(response.data);
      
      // Load recent transactions for the chart
      const txResponse = await getBlockchainTransactions({
        pageSize: 100, // Get more transactions for chart data
      });
      setTransactions(txResponse.data.results || []);
    } catch (err) {
      console.error('Error loading reward pool info:', err);
      setError('Error loading reward pool information. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadRewardPoolInfo();
    
    // Setup auto refresh every 60 seconds
    const refreshInterval = setInterval(() => {
      loadRewardPoolInfo();
    }, 60000);
    
    return () => clearInterval(refreshInterval);
  }, []);
  
  // Handle refill completion - refresh data
  const handleRefillComplete = () => {
    loadRewardPoolInfo();
  };
  
  // Handle manual transfer completion - refresh data
  const handleTransferComplete = () => {
    loadRewardPoolInfo();
  };
  
  if (loading && !poolInfo) {
    return (
      <div className="reward-pool-dashboard loading-state">
        <Card>
          <Card.Body className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="mt-3 text-muted">Loading reward pool dashboard...</p>
          </Card.Body>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="reward-pool-dashboard">
      <Card className="mb-4 border-0 shadow-sm header-card">
        <Card.Body>
          <Row className="align-items-center">
            <Col>
              <h2 className="mb-1">Reward Pool Management</h2>
              <p className="text-muted mb-0">
                Monitor and manage the blockchain reward pool
              </p>
            </Col>
            <Col xs="auto">
              <Button variant="primary" onClick={loadRewardPoolInfo}>
                <i className="feather icon-refresh-cw mr-1"></i>
                Refresh Data
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>
      
      {error && (
        <Alert variant="danger" className="mb-4">
          <i className="feather icon-alert-triangle mr-2"></i>
          {error}
        </Alert>
      )}
      
      {poolInfo && poolInfo.status === 'critical' && (
        <Alert variant="danger" className="mb-4">
          <i className="feather icon-alert-triangle mr-2"></i>
          <strong>Critical MATIC Balance:</strong> The reward pool MATIC balance is below the critical threshold.
          Transactions may fail due to insufficient gas. Please refill the reward pool as soon as possible.
        </Alert>
      )}
      
      {poolInfo && poolInfo.status === 'warning' && (
        <Alert variant="warning" className="mb-4">
          <i className="feather icon-alert-circle mr-2"></i>
          <strong>Low MATIC Balance:</strong> The reward pool MATIC balance is below the warning threshold.
          Consider refilling the reward pool soon to ensure uninterrupted transactions.
        </Alert>
      )}
      
      <Row className="g-3 mb-4">
        <Col lg={8}>
          <RewardPoolSummary poolInfo={poolInfo} />
        </Col>
        <Col lg={4}>
          <RewardPoolRefill onRefillComplete={handleRefillComplete} />
        </Col>
      </Row>
      
      <Row className="g-3 mb-4">
        <Col lg={12}>
          <MaticUsageChart transactions={transactions} />
        </Col>
      </Row>
      
      <Row className="g-3 mb-4">
        <Col lg={4}>
          <ManualTeoCoinTransfer onTransferComplete={handleTransferComplete} />
        </Col>
        <Col lg={8}>
          <Card className="transactions-statistics">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-activity mr-2"></i>
                Transaction Statistics
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={3} sm={6}>
                  <div className="stat-item">
                    <h3 className="mb-1 text-primary">
                      {transactions.filter(tx => 
                        new Date(tx.created_at) > new Date(Date.now() - 24*60*60*1000)
                      ).length}
                    </h3>
                    <p className="text-muted mb-0">Transactions (24h)</p>
                  </div>
                </Col>
                <Col md={3} sm={6}>
                  <div className="stat-item">
                    <h3 className="mb-1 text-success">
                      {transactions.filter(tx => 
                        tx.status === 'confirmed' && 
                        new Date(tx.created_at) > new Date(Date.now() - 7*24*60*60*1000)
                      ).length}
                    </h3>
                    <p className="text-muted mb-0">Confirmed (Week)</p>
                  </div>
                </Col>
                <Col md={3} sm={6}>
                  <div className="stat-item">
                    <h3 className="mb-1 text-warning">
                      {transactions.filter(tx => tx.status === 'pending').length}
                    </h3>
                    <p className="text-muted mb-0">Pending</p>
                  </div>
                </Col>
                <Col md={3} sm={6}>
                  <div className="stat-item">
                    <h3 className="mb-1 text-danger">
                      {transactions.filter(tx => tx.status === 'failed').length}
                    </h3>
                    <p className="text-muted mb-0">Failed</p>
                  </div>
                </Col>
              </Row>
              
              <hr className="my-4" />
              
              <Row>
                <Col md={4} sm={12}>
                  <div className="stat-item">
                    <h5 className="mb-1">Top Transaction Types</h5>
                    <ul className="list-unstyled transaction-types">
                      {Object.entries(
                        transactions.reduce((acc, tx) => {
                          acc[tx.transaction_type] = (acc[tx.transaction_type] || 0) + 1;
                          return acc;
                        }, {})
                      )
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3)
                        .map(([type, count]) => (
                          <li key={type}>
                            <span className="type">{type}</span>
                            <span className="count">{count}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                </Col>
                <Col md={4} sm={12}>
                  <div className="stat-item">
                    <h5 className="mb-1">Avg. Gas Used</h5>
                    <p className="value">
                      {transactions.length > 0
                        ? (
                            transactions
                              .filter(tx => tx.gas_used)
                              .reduce((sum, tx) => sum + Number(tx.gas_used), 0) /
                            transactions.filter(tx => tx.gas_used).length
                          ).toFixed(0)
                        : 0}
                    </p>
                  </div>
                </Col>
                <Col md={4} sm={12}>
                  <div className="stat-item">
                    <h5 className="mb-1">Total MATIC Used (Week)</h5>
                    <p className="value">
                      {transactions
                        .filter(
                          tx =>
                            tx.gas_used &&
                            tx.status === 'confirmed' &&
                            new Date(tx.created_at) > new Date(Date.now() - 7*24*60*60*1000)
                        )
                        .reduce((sum, tx) => {
                          const gasPrice = tx.gas_price || 1;
                          return sum + (Number(tx.gas_used) * Number(gasPrice)) / 1e18;
                        }, 0)
                        .toFixed(6)} MATIC
                    </p>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row className="g-3">
        <Col lg={12}>
          <BlockchainTransactions />
        </Col>
      </Row>
    </div>
  );
};

export default RewardPoolDashboard;
