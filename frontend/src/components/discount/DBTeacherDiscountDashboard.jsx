import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Button, Row, Col, Table, Tab, Tabs } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

/**
 * DBTeacherDiscountDashboard - DB-based discount management for teachers
 * Manages student discount requests using instant database operations
 */
const DBTeacherDiscountDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    pendingRequests: [],
    completedRequests: [],
    earnings: {
      total: 0,
      monthly: 0,
      requests_processed: 0
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // In a real implementation, you would have specific endpoints for teacher discount management
      // For now, we'll show the concept with available data

      const response = await fetch('/api/v1/teocoin/statistics/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch discount data');
      }

      const data = await response.json();

      setDashboardData({
        pendingRequests: [], // Would come from a specific endpoint
        completedRequests: [], // Would come from a specific endpoint  
        earnings: {
          total: 0,
          monthly: 0,
          requests_processed: 0
        }
      });
    } catch (error) {
      console.error('Error loading discount dashboard:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card className="teacher-discount-dashboard-card">
        <Card.Body className="text-center">
          <Spinner animation="border" variant="primary" />
          <p className="mt-2">Caricamento dashboard sconti...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="teacher-discount-dashboard">
      {/* Header */}
      <div className="dashboard-header mb-3">
        <h5>
          <i className="fas fa-percentage"></i>
          Gestione Sconti TeoCoin
          <Badge bg="success" className="ms-2">DB-Based</Badge>
        </h5>
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <Alert.Heading>Errore</Alert.Heading>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <div className="stat-icon mb-2">
                <i className="fas fa-euro-sign text-success"></i>
              </div>
              <h4>{dashboardData.earnings.total.toFixed(2)} €</h4>
              <small className="text-muted">Guadagni Totali</small>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <div className="stat-icon mb-2">
                <i className="fas fa-calendar-month text-primary"></i>
              </div>
              <h4>{dashboardData.earnings.monthly.toFixed(2)} €</h4>
              <small className="text-muted">Questo Mese</small>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <div className="stat-icon mb-2">
                <i className="fas fa-tasks text-warning"></i>
              </div>
              <h4>{dashboardData.earnings.requests_processed}</h4>
              <small className="text-muted">Richieste Processate</small>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <div className="stat-icon mb-2">
                <i className="fas fa-clock text-info"></i>
              </div>
              <h4>{dashboardData.pendingRequests.length}</h4>
              <small className="text-muted">In Attesa</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Requests Management */}
      <Card>
        <Card.Header>
          <Tabs 
            activeKey={activeTab} 
            onSelect={setActiveTab}
            className="card-header-tabs"
          >
            <Tab eventKey="pending" title={
              <>
                Richieste in Attesa 
                {dashboardData.pendingRequests.length > 0 && (
                  <Badge bg="warning" className="ms-1">
                    {dashboardData.pendingRequests.length}
                  </Badge>
                )}
              </>
            } />
            <Tab eventKey="completed" title="Completate" />
          </Tabs>
        </Card.Header>
        
        <Card.Body>
          {activeTab === 'pending' && (
            <div className="pending-requests">
              {dashboardData.pendingRequests.length === 0 ? (
                <div className="text-center py-5">
                  <i className="fas fa-inbox fa-3x text-muted mb-3"></i>
                  <h5 className="text-muted">Nessuna richiesta in attesa</h5>
                  <p className="text-muted">
                    Le richieste di sconto degli studenti appariranno qui
                  </p>
                </div>
              ) : (
                <Table responsive>
                  <thead>
                    <tr>
                      <th>Studente</th>
                      <th>Corso</th>
                      <th>Prezzo Originale</th>
                      <th>TEO Richiesti</th>
                      <th>Sconto</th>
                      <th>Data Richiesta</th>
                      <th>Azioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.pendingRequests.map((request, index) => (
                      <tr key={request.id || index}>
                        <td>{request.student_name}</td>
                        <td>{request.course_title}</td>
                        <td>{request.original_price} €</td>
                        <td>{request.teo_amount} TEO</td>
                        <td className="text-success">-{request.discount_amount} €</td>
                        <td>{formatDate(request.created_at)}</td>
                        <td>
                          <Button 
                            variant="success" 
                            size="sm" 
                            className="me-1"
                            // onClick={() => approveRequest(request.id)}
                          >
                            Approva
                          </Button>
                          <Button 
                            variant="outline-danger" 
                            size="sm"
                            // onClick={() => declineRequest(request.id)}
                          >
                            Rifiuta
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </div>
          )}

          {activeTab === 'completed' && (
            <div className="completed-requests">
              {dashboardData.completedRequests.length === 0 ? (
                <div className="text-center py-5">
                  <i className="fas fa-check-circle fa-3x text-muted mb-3"></i>
                  <h5 className="text-muted">Nessuna richiesta completata</h5>
                  <p className="text-muted">
                    Le richieste approvate o rifiutate appariranno qui
                  </p>
                </div>
              ) : (
                <Table responsive>
                  <thead>
                    <tr>
                      <th>Studente</th>
                      <th>Corso</th>
                      <th>TEO Utilizzati</th>
                      <th>Sconto Applicato</th>
                      <th>Stato</th>
                      <th>Data Completamento</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.completedRequests.map((request, index) => (
                      <tr key={request.id || index}>
                        <td>{request.student_name}</td>
                        <td>{request.course_title}</td>
                        <td>{request.teo_amount} TEO</td>
                        <td className="text-success">-{request.discount_amount} €</td>
                        <td>
                          <Badge bg={request.status === 'approved' ? 'success' : 'danger'}>
                            {request.status === 'approved' ? 'Approvato' : 'Rifiutato'}
                          </Badge>
                        </td>
                        <td>{formatDate(request.completed_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* System Benefits */}
      <Card className="mt-3">
        <Card.Body>
          <h6>🎯 Vantaggi Sistema DB per Insegnanti</h6>
          <Row>
            <Col md={3}>
              <div className="benefit-item text-center">
                <i className="fas fa-bolt text-warning fa-2x mb-2"></i>
                <strong>Approvazione Istantanea</strong>
                <small className="d-block text-muted">Sconti applicati immediatamente</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item text-center">
                <i className="fas fa-gift text-success fa-2x mb-2"></i>
                <strong>Zero Costi</strong>
                <small className="d-block text-muted">Nessuna gas fee per operazioni</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item text-center">
                <i className="fas fa-chart-line text-primary fa-2x mb-2"></i>
                <strong>Analytics Real-time</strong>
                <small className="d-block text-muted">Statistiche aggiornate in tempo reale</small>
              </div>
            </Col>
            <Col md={3}>
              <div className="benefit-item text-center">
                <i className="fas fa-user-friends text-info fa-2x mb-2"></i>
                <strong>UX Migliorata</strong>
                <small className="d-block text-muted">Esperienza utente fluida</small>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
};

export default DBTeacherDiscountDashboard;
