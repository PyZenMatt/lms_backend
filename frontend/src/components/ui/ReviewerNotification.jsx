import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge } from 'react-bootstrap';

const ReviewerNotification = () => {
  const [assigned, setAssigned] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchAssigned = async () => {
      try {
        const res = await fetch('/api/v1/reviews/assigned/', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setAssigned(Array.isArray(data) ? data : []);
        } else {
          setError('Errore nel recupero delle review assegnate');
        }
      } catch (e) {
        setError('Errore di rete');
      } finally {
        setLoading(false);
      }
    };
    fetchAssigned();
  }, []);

  if (loading) return null;
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (assigned.length === 0) return null;

  return (
    <Alert variant="info" className="d-flex align-items-center justify-content-between">
      <span>
        <Badge bg="warning" text="dark" className="me-2">{assigned.length}</Badge>
        Hai {assigned.length} esercizi da valutare!
      </span>
      <Link to="/review/assigned" className="btn btn-sm btn-primary ms-3">Vai alla lista review</Link>
    </Alert>
  );
};

export default ReviewerNotification;
