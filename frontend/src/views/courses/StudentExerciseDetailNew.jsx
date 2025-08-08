const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge, Form } from 'react-bootstrap';
import { fetchUserRole } from '../../services/api/auth';
import MainCard from '../../components/Card/MainCard';

const StudentExerciseDetailNew = () => {
  const { exerciseId } = useParams();
  const [exercise, setExercise] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [solution, setSolution] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchExercise = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setExercise(data);
        } else {
          setError('Errore nel caricamento esercizio');
        }
      } catch (err) {
        setError('Errore nel caricamento esercizio');
      }
    };
    
    const fetchSubmission = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/my_submission/`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setSubmission(data);
          // Converti i campi del modello in status leggibile
          let status = '';
          if (data.is_approved) {
            status = 'approved';
          } else if (data.reviewed) {
            status = 'rejected';
          } else {
            status = 'in_review';
          }
          setStatus(status);
        } else if (res.status === 404) {
          // 404 significa che l'utente non ha ancora sottomesso una soluzione - questo è normale
          console.log('📝 Nessuna submission esistente trovata - l\'utente può sottomettere');
          setSubmission(null);
          setStatus('');
        } else {
          console.error('❌ Errore nel recupero submission:', res.status);
          setSubmission(null);
          setStatus('');
        }
      } catch (err) {
        // Non è un errore se non c'è submission
        setSubmission(null);
        setStatus('');
      }
    };
    
    fetchExercise();
    fetchSubmission();
    setLoading(false);
  }, [exerciseId]);

  useEffect(() => {
    const fetchRole = async () => {
      try {
        const role = await fetchUserRole();
        setUserRole(role);
      } catch {
        setUserRole('');
      }
    };
    fetchRole();
  }, []);

  const canSubmit = !submission || (!submission.is_approved && submission.reviewed);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    
    try {
      const res = await fetch(`/api/v1/exercises/${exerciseId}/submit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content: solution })
      });
      
      if (res.ok) {
        setStatus('in_review');
        setSubmission({ content: solution, status: 'in_review' });
        setSolution('');
      } else {
        setError('Errore nell\'invio della soluzione');
      }
    } catch (err) {
      setError('Errore nell\'invio della soluzione');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved':
        return { variant: 'success', icon: 'check-circle', text: 'Approvato' };
      case 'rejected':
        return { variant: 'danger', icon: 'x-circle', text: 'Respinto' };
      case 'in_review':
        return { variant: 'warning', icon: 'clock', text: 'In revisione' };
      default:
        return { variant: 'secondary', icon: 'circle', text: 'Non inviato' };
    }
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <Spinner animation="border" variant="primary" />
      </Container>
    );
  }
  
  if (error) {
    return (
      <Container>
        <Row className="justify-content-center">
          <Col md={8}>
            <Alert variant="danger" className="text-center">
              <i className="feather icon-alert-triangle mr-2"></i>
              {error}
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }
  
  if (!exercise) {
    return (
      <Container>
        <Row className="justify-content-center">
          <Col md={8}>
            <Alert variant="warning" className="text-center">
              <i className="feather icon-alert-triangle mr-2"></i>
              Esercizio non trovato
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  const statusBadge = getStatusBadge(submission?.status || status);

  return (
    <Container fluid>
      {/* Header */}
      <Row className="mb-4">
        <Col>
          <MainCard>
            <div className="d-flex justify-content-between align-items-start">
              <div>
                <h1 className="mb-3">
                  <i className="feather icon-target text-primary mr-2"></i>
                  {exercise.title}
                </h1>
                <p className="text-muted mb-3">{exercise.description}</p>
                <Badge 
                  bg={statusBadge.variant} 
                  className="p-2"
                >
                  <i className={`feather icon-${statusBadge.icon} mr-1`}></i>
                  {statusBadge.text}
                </Badge>
              </div>
              
              <Link 
                to={exercise.lesson ? `/lezioni/${exercise.lesson}` : 
                    userRole === 'admin' ? "/dashboard/admin" : 
                    userRole === 'teacher' ? "/dashboard/teacher" : "/dashboard/student"} 
                className="btn btn-outline-primary d-flex align-items-center"
              >
                <i className="feather icon-arrow-left mr-2"></i>
                {exercise.lesson ? 'Torna alla lezione' : 
                 userRole === 'admin' ? 'Torna alla dashboard admin' : 
                 userRole === 'teacher' ? 'Torna alla dashboard docente' : 'Torna alla dashboard studente'}
              </Link>
            </div>
          </MainCard>
        </Col>
      </Row>

      <Row>
        {/* Main Content */}
        <Col lg={8}>
          {/* Submission Status */}
          {submission && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-file-text text-primary mr-2"></i>
                  Stato della Sottomissione
                </h5>
              </Card.Header>
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span className="fw-bold">Stato attuale:</span>
                  <Badge bg={statusBadge.variant} className="p-2">
                    <i className={`feather icon-${statusBadge.icon} mr-1`}></i>
                    {statusBadge.text}
                  </Badge>
                </div>
                
                <div className="bg-light p-3 rounded">
                  <strong className="d-block mb-2">Soluzione inviata:</strong>
                  <pre className="mb-0 text-wrap">{submission.content}</pre>
                </div>
                
                {submission.feedback && (
                  <Alert variant="info" className="mt-3">
                    <strong>Feedback del docente:</strong>
                    <div className="mt-2">{submission.feedback}</div>
                  </Alert>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Solution Form */}
          {canSubmit && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-edit text-primary mr-2"></i>
                  Invia la tua soluzione
                </h5>
              </Card.Header>
              <Card.Body>
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3">
                    <Form.Label className="fw-bold">
                      <i className="feather icon-code mr-2"></i>
                      La tua soluzione
                    </Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={10}
                      value={solution}
                      onChange={e => setSolution(e.target.value)}
                      placeholder="Scrivi qui la tua soluzione..."
                      required
                      style={{ fontFamily: 'Monaco, Consolas, "Courier New", monospace' }}
                    />
                  </Form.Group>
                  
                  <div className="d-flex justify-content-end">
                    <Button 
                      type="submit" 
                      variant="primary"
                      disabled={submitting || !solution.trim()}
                      className="d-flex align-items-center"
                    >
                      {submitting ? (
                        <Spinner animation="border" size="sm" className="mr-2" />
                      ) : (
                        <i className="feather icon-send mr-2"></i>
                      )}
                      {submitting ? 'Invio in corso...' : 'Invia soluzione'}
                    </Button>
                  </div>
                </Form>
              </Card.Body>
            </Card>
          )}

          {/* Cannot Submit Info */}
          {!canSubmit && submission?.is_approved && (
            <Alert variant="success">
              <i className="feather icon-check-circle mr-2"></i>
              <strong>Ottimo lavoro!</strong> La tua soluzione è stata approvata.
            </Alert>
          )}

          {!canSubmit && submission && !submission.is_approved && !submission.reviewed && (
            <Alert variant="info">
              <i className="feather icon-clock mr-2"></i>
              <strong>In attesa di revisione</strong> La tua soluzione è in fase di valutazione.
            </Alert>
          )}
        </Col>

        {/* Sidebar */}
        <Col lg={4}>
          {/* Tips Card */}
          <Card className="border-primary">
            <Card.Header className="bg-primary text-white">
              <h6 className="mb-0">
                <i className="feather icon-lightbulb mr-2"></i>
                Consigli per una buona soluzione
              </h6>
            </Card.Header>
            <Card.Body>
              <ul className="list-unstyled mb-0">
                <li className="mb-2">
                  <i className="feather icon-check text-success mr-2"></i>
                  Leggi attentamente la consegna
                </li>
                <li className="mb-2">
                  <i className="feather icon-check text-success mr-2"></i>
                  Scrivi codice pulito e commentato
                </li>
                <li className="mb-2">
                  <i className="feather icon-check text-success mr-2"></i>
                  Testa la tua soluzione
                </li>
                <li className="mb-0">
                  <i className="feather icon-check text-success mr-2"></i>
                  Chiedi aiuto se necessario
                </li>
              </ul>
            </Card.Body>
          </Card>

          {/* Exercise Info */}
          {exercise.max_score && (
            <Card className="mt-3">
              <Card.Body className="text-center">
                <i className="feather icon-award text-warning mb-2" style={{ fontSize: '2rem' }}></i>
                <h6>Punteggio massimo</h6>
                <h4 className="text-primary mb-0">{exercise.max_score} punti</h4>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default StudentExerciseDetailNew;
