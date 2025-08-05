import React, { useEffect, useState } from 'react';
import { Table, Button, Spinner, Alert } from 'react-bootstrap';
import { fetchPendingCourses, approveCourse, rejectCourse } from '../../services/api/admin';
import { Link } from 'react-router-dom';

const PendingCoursesTable = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState({});
  const [success, setSuccess] = useState('');

  const loadCourses = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetchPendingCourses();
      setCourses(res.data);
    } catch (err) {
      setError('Errore nel caricamento dei corsi in attesa');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const handleApprove = async (id) => {
    setActionLoading((prev) => ({ ...prev, [id]: true }));
    setSuccess('');
    setError('');
    try {
      await approveCourse(id);
      setSuccess('Corso approvato!');
      loadCourses();
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
      await rejectCourse(id);
      setSuccess('Corso rifiutato!');
      loadCourses();
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
      <h3>Corsi in attesa di approvazione</h3>
      {success && <Alert variant="success">{success}</Alert>}
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>#</th>
            <th>Titolo</th>
            <th>Docente</th>
            <th>Prezzo</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {courses.length === 0 ? (
            <tr><td colSpan={5} className="text-center">Nessun corso in attesa</td></tr>
          ) : (
            courses.map((c, idx) => (
              <tr key={`course-${c.id || idx}`}>
                <td>{idx + 1}</td>
                <td>
                  <Link to={`/admin/corsi/${c.id}`}>{c.title}</Link>
                </td>
                <td>{c.teacher?.username || '-'}</td>
                <td>{c.price}</td>
                <td>
                  <Button
                    variant="success"
                    size="sm"
                    className="me-2"
                    disabled={actionLoading[c.id]}
                    onClick={() => handleApprove(c.id)}
                  >
                    Approva
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={actionLoading[c.id]}
                    onClick={() => handleReject(c.id)}
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

export default PendingCoursesTable;
