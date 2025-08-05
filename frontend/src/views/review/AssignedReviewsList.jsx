const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Table, Alert, Spinner, Button } from 'react-bootstrap';

const AssignedReviewsList = () => {
  const [assigned, setAssigned] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchAssigned = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/reviews/assigned/`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          // Recupera anche lo username dello studente autore se presente
          setAssigned(Array.isArray(data) ? data : []);
        } else {
          setAssigned([]);
        }
      } catch (e) {
        setAssigned([]);
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
      <Link to="/dashboard/student" className="btn btn-secondary mb-3">&larr; Torna alla dashboard</Link>
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
