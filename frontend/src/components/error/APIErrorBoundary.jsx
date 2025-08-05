/**
 * 🛡️ API Error Boundary
 * 
 * Catches API errors and provides graceful fallbacks
 */

import React from 'react';
import { Alert, Button, Card, Container } from 'react-bootstrap';

class APIErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log error for development
    console.error('🛡️ API Error Boundary caught error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      showDetails: false 
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Container className="mt-4">
          <Card className="border-warning">
            <Card.Header className="bg-warning text-dark">
              <h5 className="mb-0">
                🔧 Development Mode - API Services Unavailable
              </h5>
            </Card.Header>
            <Card.Body>
              <Alert variant="info" className="mb-3">
                <div className="d-flex align-items-start">
                  <div className="me-3" style={{ fontSize: '1.5rem' }}>🎭</div>
                  <div>
                    <strong>Demo Mode Active</strong>
                    <p className="mb-2">
                      The backend services are not available, so we're using sample data 
                      to demonstrate the interface functionality.
                    </p>
                    <small className="text-muted">
                      This is normal in development mode when the Django backend is not running.
                    </small>
                  </div>
                </div>
              </Alert>

              <div className="d-flex gap-2 mb-3">
                <Button 
                  variant="primary" 
                  onClick={this.handleRetry}
                  size="sm"
                >
                  🔄 Retry Connection
                </Button>
                <Button 
                  variant="outline-secondary" 
                  onClick={() => this.setState({ showDetails: !this.state.showDetails })}
                  size="sm"
                >
                  {this.state.showDetails ? 'Hide' : 'Show'} Details
                </Button>
              </div>

              {this.state.showDetails && (
                <Alert variant="light" className="small">
                  <strong>Technical Details:</strong>
                  <pre className="mb-2 mt-2" style={{ fontSize: '0.8rem' }}>
                    {this.state.error && this.state.error.toString()}
                  </pre>
                  <div>
                    <strong>Available Features in Demo Mode:</strong>
                    <ul className="mb-0 mt-1">
                      <li>✅ Dark/Light theme switching</li>
                      <li>✅ UI component demonstrations</li>
                      <li>✅ Mock activity feed</li>
                      <li>✅ Sample staking interface</li>
                      <li>✅ Simulated notifications</li>
                    </ul>
                  </div>
                </Alert>
              )}
            </Card.Body>
          </Card>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default APIErrorBoundary;
