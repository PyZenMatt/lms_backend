import React, { useEffect, useState } from 'react';
import { Table, Button, Spinner, Alert } from 'react-bootstrap';
import { fetchPendingTeachers, approveTeacher, rejectTeacher } from '../../services/api/admin';

const PendingTeachersTable = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState({});
  const [success, setSuccess] = useState('');

  const loadTeachers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetchPendingTeachers();
      setTeachers(res.data);
    } catch (err) {
      setError('Errore nel caricamento dei teacher in attesa');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeachers();
  }, []);

  const handleApprove = async (id) => {
    setActionLoading((prev) => ({ ...prev, [id]: true }));
    setSuccess('');
    setError('');
    try {
      await approveTeacher(id);
      setSuccess('Teacher approvato!');
      loadTeachers();
    } catch {
      setError('Errore durante l\'approvazione');
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: false }));
    }
  };

  const handleReject = async (id) => {
    setActionLoading((prev) => ({ ...prev, [id]: true }));
    setSuccess('');
    setError('');
    try {
      await rejectTeacher(id);
      setSuccess('Teacher rifiutato!');
      loadTeachers();
    } catch {
      setError('Errore durante il rifiuto');
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (loading) return <Spinner animation="border" className="m-5" />;
  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <div className="mt-4">
      <h3>Teacher in attesa di approvazione</h3>
      {success && <Alert variant="success">{success}</Alert>}
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>#</th>
            <th>Username</th>
            <th>Email</th>
            <th>Nome</th>
            <th>Cognome</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {teachers.length === 0 ? (
            <tr><td colSpan={6} className="text-center">Nessun teacher in attesa</td></tr>
          ) : (
            teachers.map((t, idx) => (
              <tr key={`teacher-${t.id || idx}`}>
                <td>{idx + 1}</td>
                <td>{t.username}</td>
                <td>{t.email}</td>
                <td>{t.first_name}</td>
                <td>{t.last_name}</td>
                <td>
                  <Button
                    variant="success"
                    size="sm"
                    className="me-2"
                    disabled={actionLoading[t.id]}
                    onClick={() => handleApprove(t.id)}
                  >
                    Approva
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={actionLoading[t.id]}
                    onClick={() => handleReject(t.id)}
                  >
                    Rifiuta
                  </Button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </div>
  );
};

export default PendingTeachersTable;
