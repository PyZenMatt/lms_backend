import React, { useState, useEffect } from 'react';
import { Card, Alert, Button, Badge, Spinner, Row, Col, Table, Modal } from 'react-bootstrap';

/**
 * Teacher Discount Absorption Dashboard
 * Shows pending opportunities for teachers to absorb student discounts for TEO
 */
const TeacherDiscountAbsorptionDashboard = () => {
  const [pendingAbsorptions, setPendingAbsorptions] = useState([]);
  const [absorptionHistory, setAbsorptionHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedAbsorption, setSelectedAbsorption] = useState(null);
  const [selectedChoice, setSelectedChoice] = useState('');

  // Load data on component mount
  useEffect(() => {
    loadData();
    // Set up interval to refresh pending absorptions every minute
    const interval = setInterval(() => {
      loadPendingAbsorptions();
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadPendingAbsorptions(),
        loadAbsorptionHistory()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const loadPendingAbsorptions = async () => {
    try {
      const response = await fetch('/api/v1/teocoin/teacher/absorptions/pending/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.success) {
        setPendingAbsorptions(data.pending_absorptions);
      } else {
        setError(data.error || 'Errore nel caricamento delle opportunità');
      }
    } catch (error) {
      console.error('Error loading pending absorptions:', error);
      setError('Errore di connessione');
    }
  };

  const loadAbsorptionHistory = async () => {
    try {
      const response = await fetch('/api/v1/teocoin/teacher/absorptions/history/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.success) {
        setAbsorptionHistory(data.history);
        setStats(data.stats);
      } else {
        setError(data.error || 'Errore nel caricamento della cronologia');
      }
    } catch (error) {
      console.error('Error loading absorption history:', error);
      setError('Errore di connessione');
    }
  };

  const handleChoice = async (absorption, choice) => {
    setSelectedAbsorption(absorption);
    setSelectedChoice(choice);
    setShowConfirmModal(true);
  };

  const confirmChoice = async () => {
    try {
      const response = await fetch('/api/v1/teocoin/teacher/absorptions/choose/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          absorption_id: selectedAbsorption.id,
          choice: selectedChoice
        })
      });

      const data = await response.json();
      if (data.success) {
        setSuccess(data.message);
        setShowConfirmModal(false);
        // Refresh data
        loadData();
      } else {
        setError(data.error || 'Errore nella scelta');
      }
    } catch (error) {
      console.error('Error making choice:', error);
      setError('Errore di connessione');
    }
  };

  const formatTimeRemaining = (hours) => {
    if (hours <= 0) return 'Scaduto';
    if (hours >= 24) return `${Math.floor(hours / 24)} giorni`;
    return `${Math.floor(hours)} ore`;
  };

  if (loading) {
    return (
      <Card>
        <Card.Body className="text-center">
          <Spinner animation="border" className="mb-3" />
          <p>Caricamento opportunità di assorbimento...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="teacher-discount-absorption-dashboard">
      {/* Header */}
      <Card className="mb-4">
        <Card.Header className="bg-info text-white">
          <h5 className="mb-0">
            <i className="feather icon-repeat me-2"></i>
            Sistema di Assorbimento Sconti
            <Badge bg="light" text="dark" className="ms-2">Layer 2</Badge>
          </h5>
        </Card.Header>
        <Card.Body>
          <p className="mb-0">
            Quando gli studenti usano TeoCoin per ottenere sconti sui tuoi corsi, puoi scegliere di:
            <br />
            <strong>Opzione A:</strong> Ricevere la normale commissione in EUR
            <br />
            <strong>Opzione B:</strong> Assorbire lo sconto e ricevere i TEO utilizzati + 25% bonus per il tuo staking
          </p>
        </Card.Body>
      </Card>

      {/* Error/Success Messages */}
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" dismissible onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Statistics */}
      {stats && (
        <Row className="mb-4">
          <Col md={3}>
            <Card className="bg-primary text-white">
              <Card.Body>
                <h4>{stats.total_opportunities}</h4>
                <p className="mb-0">Opportunità Totali</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="bg-success text-white">
              <Card.Body>
                <h4>{stats.absorption_rate}%</h4>
                <p className="mb-0">Tasso di Assorbimento</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="bg-warning text-white">
              <Card.Body>
                <h4>€{stats.total_eur_earned}</h4>
                <p className="mb-0">EUR Guadagnati</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="bg-info text-white">
              <Card.Body>
                <h4>{stats.total_teo_earned} TEO</h4>
                <p className="mb-0">TEO Assorbiti</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Pending Absorptions */}
      <Card className="mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h6 className="mb-0">
            <i className="feather icon-clock me-2"></i>
            Opportunità in Attesa ({pendingAbsorptions.length})
          </h6>
          <Button variant="outline-primary" size="sm" onClick={loadPendingAbsorptions}>
            <i className="feather icon-refresh-cw me-1"></i>
            Aggiorna
          </Button>
        </Card.Header>
        <Card.Body>
          {pendingAbsorptions.length === 0 ? (
            <p className="text-muted mb-0">Nessuna opportunità in attesa</p>
          ) : (
            <div className="absorption-opportunities">
              {pendingAbsorptions.map((absorption) => (
                <Card key={absorption.id} className="mb-3 border-warning">
                  <Card.Body>
                    <Row>
                      <Col md={8}>
                        <h6 className="text-primary">{absorption.course.title}</h6>
                        <p className="mb-2">
                          <strong>Studente:</strong> {absorption.student.username} ({absorption.student.email})
                          <br />
                          <strong>Sconto applicato:</strong> {absorption.discount.percentage}% 
                          ({absorption.discount.teo_used} TEO = €{absorption.discount.eur_amount})
                        </p>
                        
                        <div className="options-comparison">
                          <Row>
                            <Col md={6}>
                              <div className="option-card bg-light p-3 rounded">
                                <h6 className="text-secondary">Opzione A - Standard</h6>
                                <div><strong>€{absorption.options.option_a.teacher_eur}</strong></div>
                                <small className="text-muted">Commissione normale</small>
                              </div>
                            </Col>
                            <Col md={6}>
                              <div className="option-card bg-success bg-opacity-10 p-3 rounded border border-success">
                                <h6 className="text-success">Opzione B - Assorbi Sconto</h6>
                                <div>
                                  <strong>€{absorption.options.option_b.teacher_eur}</strong> + 
                                  <strong className="text-success"> {absorption.options.option_b.teacher_teo} TEO</strong>
                                </div>
                                <small className="text-muted">Include bonus 25%</small>
                              </div>
                            </Col>
                          </Row>
                        </div>
                      </Col>
                      
                      <Col md={4} className="text-end">
                        <div className="mb-3">
                          <Badge bg="warning" className="mb-2">
                            Scade in: {formatTimeRemaining(absorption.timing.hours_remaining)}
                          </Badge>
                        </div>
                        
                        <div className="choice-buttons">
                          <Button 
                            variant="outline-secondary" 
                            size="sm" 
                            className="me-2 mb-2"
                            onClick={() => handleChoice(absorption, 'refuse')}
                          >
                            💰 Scegli EUR
                          </Button>
                          <Button 
                            variant="success" 
                            size="sm"
                            className="mb-2"
                            onClick={() => handleChoice(absorption, 'absorb')}
                          >
                            🪙 Assorbi TEO
                          </Button>
                        </div>
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* History */}
      <Card>
        <Card.Header>
          <h6 className="mb-0">
            <i className="feather icon-list me-2"></i>
            Cronologia Assorbimenti (Ultimi 30 giorni)
          </h6>
        </Card.Header>
        <Card.Body>
          {absorptionHistory.length === 0 ? (
            <p className="text-muted mb-0">Nessuna cronologia disponibile</p>
          ) : (
            <Table responsive size="sm">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Corso</th>
                  <th>Studente</th>
                  <th>Sconto</th>
                  <th>Scelta</th>
                  <th>EUR</th>
                  <th>TEO</th>
                </tr>
              </thead>
              <tbody>
                {absorptionHistory.map((absorption) => (
                  <tr key={absorption.id}>
                    <td>{new Date(absorption.created_at).toLocaleDateString()}</td>
                    <td>{absorption.course_title}</td>
                    <td>{absorption.student_username}</td>
                    <td>{absorption.discount_percentage}%</td>
                    <td>
                      <Badge bg={
                        absorption.status === 'absorbed' ? 'success' : 
                        absorption.status === 'refused' ? 'secondary' : 'warning'
                      }>
                        {absorption.status === 'absorbed' ? 'TEO' : 
                         absorption.status === 'refused' ? 'EUR' : 'Scaduto'}
                      </Badge>
                    </td>
                    <td>€{absorption.final_teacher_eur}</td>
                    <td>{absorption.final_teacher_teo} TEO</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Confirmation Modal */}
      <Modal show={showConfirmModal} onHide={() => setShowConfirmModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Conferma Scelta</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedAbsorption && (
            <div>
              <p><strong>Corso:</strong> {selectedAbsorption.course.title}</p>
              <p><strong>Sconto:</strong> {selectedAbsorption.discount.percentage}% ({selectedAbsorption.discount.teo_used} TEO)</p>
              
              {selectedChoice === 'absorb' ? (
                <Alert variant="success">
                  <strong>Hai scelto di assorbire lo sconto:</strong>
                  <br />
                  Riceverai: €{selectedAbsorption.options.option_b.teacher_eur} + {selectedAbsorption.options.option_b.teacher_teo} TEO
                </Alert>
              ) : (
                <Alert variant="secondary">
                  <strong>Hai scelto la commissione standard:</strong>
                  <br />
                  Riceverai: €{selectedAbsorption.options.option_a.teacher_eur}
                </Alert>
              )}
              
              <p>Sei sicuro di questa scelta?</p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConfirmModal(false)}>
            Annulla
          </Button>
          <Button 
            variant={selectedChoice === 'absorb' ? 'success' : 'primary'} 
            onClick={confirmChoice}
          >
            Conferma
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TeacherDiscountAbsorptionDashboard;
