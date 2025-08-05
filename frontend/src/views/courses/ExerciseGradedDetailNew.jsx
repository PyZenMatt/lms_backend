const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Badge, Spinner, Alert, Row, Col } from 'react-bootstrap';
import MainCard from '../../components/Card/MainCard';

const ExerciseGradedDetailNew = () => {
  const { submissionId } = useParams();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('access');
        const res = await fetch(`${API_BASE_URL}/api/v1/submissions/${submissionId}/`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        
        if (res.ok) {
          const data = await res.json();
          setSubmission(data);
        } else {
          setError('Submission non trovata o non hai i permessi per visualizzarla.');
        }
      } catch (err) {
        setError('Errore nel caricamento della submission.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubmission();
  }, [submissionId]);

  const getStatusBadge = (passed, reviewed) => {
    if (!reviewed) {
      return <Badge bg="warning" text="dark">In Valutazione</Badge>;
    }
    return passed ? 
      <Badge bg="success">Approvato</Badge> : 
      <Badge bg="danger">Non Approvato</Badge>;
  };

  if (loading) return (
    <div className="d-flex flex-column justify-content-center align-items-center" style={{ minHeight: '300px' }}>
      <Spinner animation="border" variant="primary" />
      <p className="mt-3">Caricamento dettagli valutazione...</p>
    </div>
  );

  if (error) return (
    <div className="container mt-4">
      <Alert variant="danger">{error}</Alert>
      <Link to="/dashboard-studente" className="btn btn-secondary">
        Torna alla Dashboard
      </Link>
    </div>
  );

  if (!submission) return (
    <div className="container mt-4">
      <Alert variant="warning">Submission non trovata.</Alert>
      <Link to="/dashboard-studente" className="btn btn-secondary">
        Torna alla Dashboard
      </Link>
    </div>
  );

  return (
    <div className="page-wrapper">
      <div className="container mt-4">
        {/* Header */}
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h2 className="mb-0">
            <i className="feather icon-check-circle mr-2"></i>
            Valutazione Esercizio: {submission.exercise?.title || 'Titolo non disponibile'}
          </h2>
          {getStatusBadge(submission.passed, submission.reviewed)}
        </div>

        <Row>
          <Col lg={8}>
            {/* Exercise Info */}
            <MainCard
              title={<span><i className="feather icon-clipboard mr-2"></i>Dettagli Esercizio</span>}
              className="mb-4"
            >
              <p><strong>Titolo:</strong> {submission.exercise?.title || 'N/A'}</p>
              <p><strong>Descrizione:</strong> {submission.exercise?.description || 'N/A'}</p>
              <p className="mb-0"><strong>Data Sottomissione:</strong> {new Date(submission.created_at).toLocaleString()}</p>
            </MainCard>

            {/* Your Solution */}
            <MainCard
              title={<span><i className="feather icon-code mr-2"></i>La Tua Soluzione</span>}
              className="mb-4"
            >
              <pre className="bg-light p-3 rounded" style={{whiteSpace: 'pre-wrap', wordBreak: 'break-word'}}>
                {submission.content || 'Nessuna soluzione disponibile'}
              </pre>
            </MainCard>

            {/* Reviews */}
            {submission.reviews && submission.reviews.length > 0 && (
              <MainCard
                title={<span><i className="feather icon-star mr-2"></i>Valutazioni Ricevute</span>}
                className="mb-4"
              >
                <Row>
                  {submission.reviews.map((review, index) => (
                    <Col md={6} key={index} className="mb-3">
                      <Card className="shadow-sm h-100">
                        <Card.Body>
                          <div className="d-flex justify-content-between align-items-center mb-2">
                            <strong>Valutatore #{index + 1}</strong>
                            {review.score && (
                              <Badge bg={review.score >= 6 ? 'success' : 'danger'}>
                                {review.score}/10
                              </Badge>
                            )}
                          </div>
                          {review.reviewed_at && (
                            <small className="text-muted">
                              Valutato il: {new Date(review.reviewed_at).toLocaleString()}
                            </small>
                          )}
                          {review.comment && (
                            <div className="mt-2">
                              <p className="mb-0"><strong>Commento:</strong></p>
                              <p className="text-muted mb-0">{review.comment}</p>
                            </div>
                          )}
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </MainCard>
            )}
          </Col>

          <Col lg={4}>
            {/* Score Summary */}
            <MainCard
              title={<span><i className="feather icon-award mr-2"></i>Riepilogo Valutazione</span>}
              className="mb-4"
            >
              <div className="text-center">
                {submission.reviewed ? (
                  <>
                    <div className="mb-3">
                      <h1 className={submission.passed ? 'text-success' : 'text-danger'} style={{ fontSize: '3rem' }}>
                        {submission.average_score ? Math.round(submission.average_score * 10) / 10 : 'N/A'}
                      </h1>
                      <p className="text-muted mb-0">Punteggio Medio</p>
                    </div>
                    <hr />
                    <div className="mb-3">
                      <h4 className={submission.passed ? 'text-success' : 'text-danger'}>
                        {submission.passed ? 'SUPERATO' : 'NON SUPERATO'}
                      </h4>
                      <p className="text-muted mb-0">
                        {submission.passed ? 
                          'Complimenti! Hai superato l\'esercizio.' : 
                          'Non hai raggiunto il punteggio minimo (6/10).'}
                      </p>
                    </div>
                    {submission.reward_amount > 0 && (
                      <>
                        <hr />
                        <div>
                          <Badge bg="warning" text="dark" className="px-3 py-2" style={{ fontSize: '1rem' }}>
                            <i className="feather icon-dollar-sign mr-1"></i>
                            +{submission.reward_amount} TeoCoin
                          </Badge>
                          <p className="text-muted mt-2 mb-0">Ricompensa guadagnata!</p>
                        </div>
                      </>
                    )}
                  </>
                ) : (
                  <div>
                    <Spinner animation="border" variant="warning" className="mb-3" />
                    <h5>Valutazione in corso</h5>
                    <p className="text-muted">
                      I tuoi pari stanno ancora valutando la tua soluzione. 
                      Riceverai una notifica quando la valutazione sarà completata.
                    </p>
                    <div>
                      <p><strong>Valutazioni completate:</strong></p>
                      <Badge bg="info" className="px-3 py-2">
                        {submission.reviews ? submission.reviews.filter(r => r.score !== null).length : 0} / 3
                      </Badge>
                    </div>
                  </div>
                )}
              </div>
            </MainCard>

            {/* Actions */}
            <MainCard
              title={<span><i className="feather icon-settings mr-2"></i>Azioni</span>}
            >
              <div className="d-grid gap-2">
                {submission.exercise?.id && (
                  <Link 
                    to={`/esercizi/${submission.exercise.id}`} 
                    className="btn btn-outline-primary"
                  >
                    <i className="feather icon-eye mr-2"></i>
                    Vedi Esercizio
                  </Link>
                )}
                <Link 
                  to="/dashboard-studente" 
                  className="btn btn-secondary"
                >
                  <i className="feather icon-arrow-left mr-2"></i>
                  Torna alla Dashboard
                </Link>
              </div>
            </MainCard>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default ExerciseGradedDetailNew;
