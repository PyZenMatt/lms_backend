import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Table, Alert, Spinner, Button } from 'react-bootstrap';
import api from '../../services/core/axiosClient';

const AssignedReviewsList = () => {
  const [assigned, setAssigned] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAssigned = async () => {
      try {
        const res = await api.get('/reviews/assigned/');
        const data = res.data;
        setAssigned(Array.isArray(data) ? data : []);
      } catch (e) {
        setAssigned([]);
        setError('Errore nel caricamento delle assegnazioni');
      } finally {
        setLoading(false);
      }
    };
    fetchAssigned();
  }, []);

  if (loading) return <Spinner animation="border" className="mt-4" />;
  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <div className="container mt-4">
      <h2>Esercizi da valutare</h2>
      <Link to="/dashboard/student" className="btn btn-secondary mb-3">
        &larr; Torna alla dashboard
      </Link>
      {assigned.length === 0 ? (
        <Alert variant="info">Nessun esercizio da valutare al momento.</Alert>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>#</th>
              <th>Titolo esercizio</th>
              <th>Studente autore</th>
              <th>Data assegnazione</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {assigned.map((item, idx) => (
              <tr key={item.submission_pk}>
                <td>{idx + 1}</td>
                <td>{item.exercise_title}</td>
                <td>{item.student_username || '-'}</td>
                <td>{item.assigned_at ? new Date(item.assigned_at).toLocaleString() : '-'}</td>
                <td>
                  <Button as={Link} to={`/review/${item.submission_pk}`} variant="primary" size="sm">
                    Valuta
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
};

export default AssignedReviewsList;
