import React, { useEffect, useState } from 'react';
import { Card, Spinner, Alert, Button, Table, Badge } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { fetchAssignedReviews } from '../../services/api/reviews';

const StudentAssignedReviewsWidget = () => {
  const [assigned, setAssigned] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setErr('');
      try {
        const res = await fetchAssignedReviews();
        setAssigned(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        setErr('Errore nel caricamento delle review assegnate');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <Card className="border-0 shadow-sm">
      <Card.Header className="bg-light border-0 d-flex justify-content-between align-items-center">
        <Card.Title as="h5" className="mb-0">
          Peer Review assegnate
          {assigned.length > 0 && (
            <Badge bg="warning" text="dark" className="ms-2">
              {assigned.length}
            </Badge>
          )}
        </Card.Title>
        <Button variant="outline-primary" size="sm" onClick={() => navigate('/review/assigned')}>
          Vai alla lista
        </Button>
      </Card.Header>
      <Card.Body>
        {loading ? (
          <div className="text-center py-3">
            <Spinner animation="border" />
          </div>
        ) : err ? (
          <Alert variant="danger">{err}</Alert>
        ) : assigned.length === 0 ? (
          <Alert variant="info" className="mb-0">
            Nessuna review assegnata
          </Alert>
        ) : (
          <Table hover responsive size="sm" className="mb-0">
            <thead>
              <tr>
                <th>#</th>
                <th>Esercizio</th>
                <th>Studente</th>
                <th>Assegnata</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {assigned.map((item, idx) => (
                <tr key={item.submission_pk || item.id || idx}>
                  <td>{idx + 1}</td>
                  <td>{item.exercise_title || 'Esercizio'}</td>
                  <td>{item.student_username || item.student || '-'}</td>
                  <td>{item.assigned_at ? new Date(item.assigned_at).toLocaleString('it-IT') : '-'}</td>
                  <td>
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => navigate(`/review/${item.submission_pk || item.submission_id || item.id}`)}
                    >
                      Valuta
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card.Body>
    </Card>
  );
};

export default StudentAssignedReviewsWidget;
