import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Tab, Tabs, Button, Badge, Alert, Spinner } from 'react-bootstrap';
import axiosClient from '../../services/core/axiosClient';

const TeacherAbsorptionDashboard = () => {
  const [activeTab, setActiveTab] = useState('pending');
  const [pendingAbsorptions, setPendingAbsorptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPendingAbsorptions = async () => {
    try {
      setLoading(true);
      const response = await axiosClient.get('/teocoin/teacher/absorptions/');
      
      if (response.data && response.data.success) {
        setPendingAbsorptions(response.data.pending_absorptions || []);
        setError(null);
      } else {
        setError('Errore nel caricamento delle richieste');
      }
    } catch (err) {
      setError('Errore di connessione');
      setPendingAbsorptions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'pending') {
      fetchPendingAbsorptions();
    }
  }, [activeTab]);

  const handleChoice = async (absorptionId, choice) => {
    try {
      // Map frontend choice to API expected values
      const apiChoice = choice === 'A' ? 'refuse' : 'absorb'; // A = EUR (refuse discount), B = TEO (absorb discount)
      
      const response = await axiosClient.post('/teocoin/teacher/choice/', {
        absorption_id: absorptionId,
        choice: apiChoice
      });

      if (response.data && response.data.success) {
        await fetchPendingAbsorptions();
        setError(null);
      } else {
        setError('Errore nella scelta');
      }
    } catch (err) {
      console.error('Errore nella scelta:', err);
      setError('Errore di connessione');
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="text-center py-4">
          <Spinner animation="border" />
        </div>
      );
    }

    if (error) {
      return <Alert variant="danger">{error}</Alert>;
    }

    if (!pendingAbsorptions.length) {
      return (
        <Alert variant="info">
          <h6>Nessuna richiesta in attesa</h6>
          <p>Non ci sono richieste di assorbimento discount in attesa.</p>
        </Alert>
      );
    }

    return (
      <div>
        {pendingAbsorptions.map((absorption) => (
          <Card key={absorption.id} className="mb-3">
            <Card.Body>
              <Row>
                <Col md={8}>
                  <h6>Corso: {absorption.course?.title || absorption.course_title || `Corso ID: ${absorption.course?.id}`}</h6>
                  <p>Studente: {absorption.student?.username || absorption.student_name}</p>
                  <p>Sconto: {absorption.discount?.percentage || absorption.discount_percentage}%</p>
                  
                  <Row className="mt-3">
                    <Col sm={6}>
                      <div className="p-2 bg-light rounded">
                        <strong>Opzione A - EUR</strong>
                        <br />
                        <span>€{absorption.options?.option_a?.teacher_eur || absorption.option_a_amount || 'N/A'}</span>
                      </div>
                    </Col>
                    <Col sm={6}>
                      <div className="p-2 bg-light rounded">
                        <strong>Opzione B - TEO</strong>
                        <br />
                        <span>{absorption.options?.option_b?.teacher_teo || absorption.option_b_amount || 'N/A'} TEO</span>
                      </div>
                    </Col>
                  </Row>
                </Col>
                
                <Col md={4}>
                  <div className="d-grid gap-2">
                    <Button variant="primary" size="sm" onClick={() => handleChoice(absorption.id, 'A')}>
                      Scegli Opzione A
                    </Button>
                    <Button variant="success" size="sm" onClick={() => handleChoice(absorption.id, 'B')}>
                      Scegli Opzione B
                    </Button>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <Container fluid>
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h4>Gestione Commissioni TeoCoin</h4>
              <p>Gestisci le richieste di assorbimento discount TeoCoin</p>
            </Card.Header>
            <Card.Body>
              <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
                <Tab
                  eventKey="pending"
                  title={
                    <span>
                      In Attesa
                      {pendingAbsorptions.length > 0 && (
                        <Badge bg="warning" className="ms-2">
                          {pendingAbsorptions.length}
                        </Badge>
                      )}
                    </span>
                  }
                >
                  {renderContent()}
                </Tab>
                
                <Tab eventKey="history" title="Storico">
                  <Alert variant="info">Storico in arrivo...</Alert>
                </Tab>
              </Tabs>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default TeacherAbsorptionDashboard;
