import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, Button, Alert, Spinner, Form } from '@/components/ui/legacy-shims';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ReviewDetail = () => {
  const { submissionId, reviewId } = useParams();
  const resolvedId = submissionId || reviewId;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submission, setSubmission] = useState(null);
  const [score, setScore] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchSubmission = async () => {
      try {
        // Usa endpoint /review-detail/ per reviewer, fallback su /submissions/<id>/ per owner
        let res = await fetch(`${API_BASE_URL}/api/v1/submissions/${resolvedId}/review-detail/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (res.status === 403) {
          // Fallback: prova endpoint owner
          res = await fetch(`${API_BASE_URL}/api/v1/submissions/${resolvedId}/`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {}
          });
        }
        if (res.ok) {
          const data = await res.json();
          setSubmission(data);
        } else {
          setError('Errore nel recupero del dettaglio esercizio');
        }
      } catch (e) {
        setError('Errore di rete');
      } finally {
        setLoading(false);
      }
    };
    fetchSubmission();
  }, [resolvedId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess(false);
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${resolvedId}/review/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ score: Number(score) })
      });
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => navigate('/review/assigned'), 1200);
      } else {
        const data = await res.json();
        setError(data.error || "Errore nell'invio della valutazione");
      }
    } catch (e) {
      setError('Errore di rete');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Spinner animation="border" className="mt-4" />;
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (!submission) return null;

  // Trova la review dell'utente corrente (se già inviata)
  const myReview = (submission.reviews || []).find((r) => r.reviewer === submission.current_user);
  const alreadyReviewed = !!myReview && myReview.score !== null && myReview.score !== undefined;

  return (
    <div className="container mt-4">
      <Link to="/review/assigned" className="btn btn-secondary mb-3">
        &larr; Torna alla lista
      </Link>
      <Card>
        <Card.Header>
          <h4>Valutazione esercizio: {submission.exercise && submission.exercise.title}</h4>
        </Card.Header>
        <Card.Body>
          <p>
            <b>Autore:</b> {submission.student && submission.student.username}
          </p>
          <p>
            <b>Soluzione:</b>
          </p>
          <pre className="bg-light p-2" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {submission.content || <i>Nessuna soluzione presente</i>}
          </pre>
          <Form onSubmit={handleSubmit} className="mt-3">
            <Form.Group controlId="score">
              <Form.Label>Voto</Form.Label>
              <Form.Control
                type="number"
                min="1"
                max="10"
                step="1"
                value={score}
                onChange={(e) => setScore(e.target.value)}
                required
                disabled={alreadyReviewed || submitting}
              />
            </Form.Group>
            {alreadyReviewed && (
              <Alert variant="success" className="mt-3">
                Review già inviata. Voto: {myReview.score}
              </Alert>
            )}
            {!alreadyReviewed && (
              <Button type="submit" variant="primary" className="mt-3" disabled={submitting}>
                {submitting ? 'Invio...' : 'Invia valutazione'}
              </Button>
            )}
            {success && (
              <Alert variant="success" className="mt-3">
                Valutazione inviata!
              </Alert>
            )}
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
};

export default ReviewDetail;
