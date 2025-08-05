import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import { fetchPendingTeachers, approveTeacher, rejectTeacher } from '../../services/api/admin';

const PendingTeachersCard = () => {
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
      setTeachers(res.data.slice(0, 5)); // Limit to 5 for dashboard card
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

  return (
    <Card className="widget-focus-lg">
      <Card.Header>
        <Card.Title as="h5">
          Teacher in Attesa 
          {teachers.length > 0 && (
            <Badge bg="warning" className="ms-2">{teachers.length}</Badge>
          )}
        </Card.Title>
      </Card.Header>
      <Card.Body className="px-0 py-2">
        {loading && (
          <div className="text-center p-3">
            <Spinner animation="border" size="sm" />
          </div>
        )}
        {error && <Alert variant="danger" className="m-3">{error}</Alert>}
        {success && <Alert variant="success" className="m-3">{success}</Alert>}
        {!loading && teachers.length === 0 && (
          <div className="text-center p-3 text-muted">
            <i className="feather icon-check-circle f-40 mb-2 text-success"></i>
            <p>Nessun teacher in attesa di approvazione</p>
          </div>
        )}
        {!loading && teachers.length > 0 && (
          <Table responsive hover className="recent-users">
            <tbody>
              {teachers.map((teacher, index) => (
                <tr key={teacher.id} className={index === 0 ? 'unread' : ''}>
                  <td>
                    <div className="d-flex align-items-center">
                      <div className="me-3">
                        <div 
                          className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center"
                          style={{ width: '40px', height: '40px' }}
                        >
                          {teacher.first_name?.[0]?.toUpperCase() || 'T'}
                        </div>
                      </div>
                      <div>
                        <h6 className="mb-1">{teacher.first_name} {teacher.last_name}</h6>
                        <p className="text-muted mb-0">{teacher.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="text-end">
                    <Button
                      variant="outline-success"
                      size="sm"
                      className="me-1"
                      disabled={actionLoading[teacher.id]}
                      onClick={() => handleApprove(teacher.id)}
                    >
                      {actionLoading[teacher.id] ? (
                        <Spinner size="sm" animation="border" />
                      ) : (
                        <i className="feather icon-check"></i>
                      )}
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      disabled={actionLoading[teacher.id]}
                      onClick={() => handleReject(teacher.id)}
                    >
                      {actionLoading[teacher.id] ? (
                        <Spinner size="sm" animation="border" />
                      ) : (
                        <i className="feather icon-x"></i>
                      )}
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

export default PendingTeachersCard;
