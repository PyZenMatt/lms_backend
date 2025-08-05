import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import TeoCoinBalanceWidget from '../components/TeoCoinBalanceWidget';
import TeoCoinWithdrawal from '../components/TeoCoinWithdrawal';

/**
 * TeoCoin Integration Demo Page
 * Shows how the withdrawal components integrate into your platform
 */
const TeoCoinIntegrationDemo = () => {
  const [showWithdrawal, setShowWithdrawal] = React.useState(false);

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <Card className="bg-primary text-white">
            <Card.Body className="text-center">
              <h2>🎉 TeoCoin Withdrawal Integration Demo</h2>
              <p className="mb-0">
                Your TeoCoin withdrawal system is now fully integrated into all dashboards!
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col lg={6} className="mb-4">
          <Card>
            <Card.Header>
              <h5>📱 Dashboard Widget (Full Version)</h5>
              <small className="text-muted">Used in Student & Teacher Dashboards</small>
            </Card.Header>
            <Card.Body>
              <TeoCoinBalanceWidget />
            </Card.Body>
          </Card>
        </Col>

        <Col lg={6} className="mb-4">
          <Card>
            <Card.Header>
              <h5>📱 Dashboard Widget (Compact Version)</h5>
              <small className="text-muted">Used in Admin Dashboard</small>
            </Card.Header>
            <Card.Body>
              <TeoCoinBalanceWidget variant="compact" />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col lg={12} className="mb-4">
          <Card>
            <Card.Header>
              <h5>🚀 Integration Points</h5>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={4}>
                  <div className="text-center p-3 bg-light rounded mb-3">
                    <h6>👨‍🎓 Student Dashboard</h6>
                    <p className="small text-muted">Full widget next to TeoCoin dashboard</p>
                    <code>StudentDashboard.jsx</code>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="text-center p-3 bg-light rounded mb-3">
                    <h6>👨‍🏫 Teacher Dashboard</h6>
                    <p className="small text-muted">Full widget next to staking interface</p>
                    <code>TeacherDashboard.jsx</code>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="text-center p-3 bg-light rounded mb-3">
                    <h6>👨‍💼 Admin Dashboard</h6>
                    <p className="small text-muted">Compact widget for space efficiency</p>
                    <code>AdminDashboard.jsx</code>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col lg={12}>
          <Card>
            <Card.Header>
              <h5>🔗 API Integration Status</h5>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={3}>
                  <div className="text-center p-2">
                    <span className="badge bg-success mb-2 d-block">✅ READY</span>
                    <small>/frontend/api/balance/</small>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="text-center p-2">
                    <span className="badge bg-success mb-2 d-block">✅ READY</span>
                    <small>/blockchain/v2/request-withdrawal/</small>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="text-center p-2">
                    <span className="badge bg-success mb-2 d-block">✅ READY</span>
                    <small>/blockchain/v2/link-wallet/</small>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="text-center p-2">
                    <span className="badge bg-success mb-2 d-block">✅ READY</span>
                    <small>/blockchain/v2/withdrawal-history/</small>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col lg={12}>
          <Card className="bg-light">
            <Card.Body className="text-center">
              <h5>🎯 Test Complete Withdrawal Flow</h5>
              <p className="text-muted">
                Click below to test the full MetaMask withdrawal dialog
              </p>
              <button 
                className="btn btn-primary btn-lg"
                onClick={() => setShowWithdrawal(true)}
              >
                🦊 Test MetaMask Integration
              </button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Full Withdrawal Dialog */}
      <TeoCoinWithdrawal
        open={showWithdrawal}
        onClose={() => setShowWithdrawal(false)}
        userBalance={125.50} // Demo balance
      />
    </Container>
  );
};

export default TeoCoinIntegrationDemo;
