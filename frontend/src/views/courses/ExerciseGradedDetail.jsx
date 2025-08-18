import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Badge, Spinner, Alert, Row, Col } from '@/components/ui/legacy-shims';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ExerciseGradedDetail = () => {
  const { submissionId } = useParams();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('access');
        const res = await fetch(`${API_BASE_URL}/api/v1/submissions/${submissionId}/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
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
      return (
        <Badge bg="warning" text="dark">
          In Valutazione
        </Badge>
      );
    }
    return passed ? <Badge bg="success">Approvato</Badge> : <Badge bg="danger">Non Approvato</Badge>;
  };

  if (loading)
    return (
      <div className="graded-loading-container">
        <Spinner animation="border" />
        <p>Caricamento dettagli valutazione...</p>
      </div>
    );

  if (error)
    return (
      <div className="container mt-4">
        <Alert variant="danger">{error}</Alert>
        <Link to="/dashboard-studente" className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground bg-secondary text-secondary-foreground">
          Torna alla Dashboard
        </Link>
      </div>
    );

  if (!submission)
    return (
      <div className="container mt-4">
        <Alert variant="warning">Submission non trovata.</Alert>
        <Link to="/dashboard-studente" className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground bg-secondary text-secondary-foreground">
          Torna alla Dashboard
        </Link>
      </div>
    );

  return (
    <div className="exercise-graded-container">
      <div className="container mt-4">
        {/* Header */}
        <div className="graded-header">
          <h1 className="graded-title">
            <i className="fas fa-chart-line me-2"></i>
            Valutazione Esercizio: {submission.exercise?.title || 'Titolo non disponibile'}
          </h1>
          {getStatusBadge(submission.passed, submission.reviewed)}
        </div>

        <Row>
          <Col lg={8}>
            {/* Exercise Info */}
            <Card className="mb-4">
              <Card.Header>
                <h5>
                  <i className="fas fa-dumbbell me-2"></i>Dettagli Esercizio
                </h5>
              </Card.Header>
              <Card.Body>
                <p>
                  <strong>Titolo:</strong> {submission.exercise?.title || 'N/A'}
                </p>
                <p>
                  <strong>Descrizione:</strong> {submission.exercise?.description || 'N/A'}
                </p>
                <p>
                  <strong>Data Sottomissione:</strong> {new Date(submission.created_at).toLocaleString()}
                </p>
              </Card.Body>
            </Card>

            {/* Your Solution */}
            <Card className="mb-4">
              <Card.Header>
                <h5>
                  <i className="fas fa-code me-2"></i>La Tua Soluzione
                </h5>
              </Card.Header>
              <Card.Body>
                <div className="solution-content">
                  <pre className="bg-light p-3 rounded" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {submission.content || 'Nessuna soluzione disponibile'}
                  </pre>
                </div>
              </Card.Body>
            </Card>

            {/* Reviews */}
            {submission.reviews && submission.reviews.length > 0 && (
              <Card className="mb-4">
                <Card.Header>
                  <h5>
                    <i className="fas fa-star me-2"></i>Valutazioni Ricevute
                  </h5>
                </Card.Header>
                <Card.Body>
                  <Row>
                    {submission.reviews.map((review, index) => (
                      <Col md={6} key={index} className="mb-3">
                        <Card className="review-bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm h-100">
                          <Card.Body>
                            <div className="d-flex justify-content-between align-items-center mb-2">
                              <strong>Valutatore #{index + 1}</strong>
                              {review.score && <Badge bg={review.score >= 6 ? 'success' : 'danger'}>{review.score}/10</Badge>}
                            </div>
                            {review.reviewed_at && (
                              <small className="text-muted">Valutato il: {new Date(review.reviewed_at).toLocaleString()}</small>
                            )}
                            {review.comment && (
                              <div className="mt-2">
                                <p className="mb-0">
                                  <strong>Commento:</strong>
                                </p>
                                <p className="text-muted">{review.comment}</p>
                              </div>
                            )}
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card.Body>
              </Card>
            )}
          </Col>

          <Col lg={4}>
            {/* Score Summary */}
            <Card className="mb-4">
              <Card.Header>
                <h5>
                  <i className="fas fa-trophy me-2"></i>Riepilogo Valutazione
                </h5>
              </Card.Header>
              <Card.Body className="text-center">
                {submission.reviewed ? (
                  <>
                    <div className="score-display">
                      <h2 className={`score-number ${submission.passed ? 'text-success' : 'text-danger'}`}>
                        {submission.average_score ? Math.round(submission.average_score * 10) / 10 : 'N/A'}
                      </h2>
                      <p className="score-label">Punteggio Medio</p>
                    </div>
                    <hr />
                    <div className="result-display">
                      <h4 className={submission.passed ? 'text-success' : 'text-danger'}>
                        {submission.passed ? 'SUPERATO' : 'NON SUPERATO'}
                      </h4>
                      <p className="text-muted">
                        {submission.passed ? "Complimenti! Hai superato l'esercizio." : 'Non hai raggiunto il punteggio minimo (6/10).'}
                      </p>
                    </div>
                    {submission.reward_amount > 0 && (
                      <>
                        <hr />
                        <div className="reward-display">
                          <Badge bg="warning" text="dark" className="fs-6">
                            <i className="fas fa-coins me-1"></i>+{submission.reward_amount} TeoCoin
                          </Badge>
                          <p className="text-muted mt-1">Ricompensa guadagnata!</p>
                        </div>
                      </>
                    )}
                  </>
                ) : (
                  <div className="pending-review">
                    <div className="spinner-border text-warning mb-3" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <h5>Valutazione in corso</h5>
                    <p className="text-muted">
                      I tuoi pari stanno ancora valutando la tua soluzione. Riceverai una notifica quando la valutazione sarà completata.
                    </p>
                    <div className="review-progress">
                      <p>
                        <strong>Valutazioni completate:</strong>
                      </p>
                      <Badge bg="info">{submission.reviews ? submission.reviews.filter((r) => r.score !== null).length : 0} / 3</Badge>
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>

            {/* Actions */}
            <Card>
              <Card.Header>
                <h6>
                  <i className="fas fa-cogs me-2"></i>Azioni
                </h6>
              </Card.Header>
              <Card.Body>
                <div className="d-grid gap-2">
                  {submission.exercise?.id && (
                    <Link to={`/esercizi/${submission.exercise.id}`} className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-outline-primary">
                      <i className="fas fa-eye me-2"></i>
                      Vedi Esercizio
                    </Link>
                  )}
                  <Link to="/dashboard-studente" className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground bg-secondary text-secondary-foreground">
                    <i className="fas fa-arrow-left me-2"></i>
                    Torna alla Dashboard
                  </Link>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default ExerciseGradedDetail;
