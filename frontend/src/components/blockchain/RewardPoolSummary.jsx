import React from 'react';
import { Card, Row, Col, Badge } from 'react-bootstrap';
import './RewardPoolSummary.scss';

/**
 * Widget to display current reward pool balances and status
 */
const RewardPoolSummary = ({ poolInfo }) => {
  if (!poolInfo) {
    return null;
  }

  const {
    teo_balance,
    matic_balance,
    address,
    warning_threshold,
    critical_threshold,
    status
  } = poolInfo;

  // Determine status badge variant
  const getStatusBadge = (status) => {
    switch (status) {
      case 'ok':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  // Format address for display
  const formatAddress = (address) => {
    if (!address || address.length < 10) return address;
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <Card className="reward-pool-summary">
      <Card.Header>
        <Card.Title as="h5">
          <i className="feather icon-database mr-2"></i>
          Reward Pool Status
        </Card.Title>
        <div className="card-header-right">
          <Badge bg={getStatusBadge(status)} className="status-badge">
            {status.toUpperCase()}
          </Badge>
        </div>
      </Card.Header>
      <Card.Body>
        <Row>
          <Col md={6} className="mb-3">
            <div className="balance-box">
              <h6 className="text-muted">TeoCoin Balance</h6>
              <div className="d-flex align-items-end">
                <h3 className="mb-0 fw-bold text-primary">{teo_balance}</h3>
                <span className="text-muted ml-2">TEO</span>
              </div>
            </div>
          </Col>
          <Col md={6} className="mb-3">
            <div className="balance-box">
              <h6 className="text-muted">MATIC Balance</h6>
              <div className="d-flex align-items-end">
                <h3 className={`mb-0 fw-bold ${status === 'critical' ? 'text-danger' : 'text-primary'}`}>
                  {matic_balance}
                </h3>
                <span className="text-muted ml-2">MATIC</span>
              </div>
              {status === 'warning' && (
                <Badge bg="warning" className="mt-1">
                  Below {warning_threshold} MATIC
                </Badge>
              )}
              {status === 'critical' && (
                <Badge bg="danger" className="mt-1">
                  Below {critical_threshold} MATIC
                </Badge>
              )}
            </div>
          </Col>
        </Row>
        <Row className="mt-3">
          <Col xs={12}>
            <div className="address-info">
              <h6 className="text-muted">Reward Pool Address</h6>
              <div className="d-flex align-items-center">
                <code className="address">{formatAddress(address)}</code>
                <button
                  className="btn btn-light btn-sm ml-2 copy-btn"
                  onClick={() => navigator.clipboard.writeText(address)}
                  title="Copy to clipboard"
                >
                  <i className="feather icon-copy"></i>
                </button>
              </div>
            </div>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default RewardPoolSummary;
