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
    setSuccess(''); // Clear success message when loading
    try {
      console.log('🔄 Loading pending teachers...');
      const res = await fetchPendingTeachers();
      console.log('📊 Pending teachers response:', res.data);
      
      // Handle different response structures
      const teachersData = res.data?.data || res.data || res || [];
      const teachersList = Array.isArray(teachersData) ? teachersData : [];
      
      console.log(`✅ Found ${teachersList.length} pending teachers`);
      setTeachers(teachersList.slice(0, 5)); // Limit to 5 for dashboard card
      setError(''); // Clear any previous errors on success
    } catch (err) {
      console.error('❌ Error loading pending teachers:', err);
      console.error('Response data:', err?.response?.data);
      console.error('Response status:', err?.response?.status);
      
      // If the error is a 404 or no content, treat as empty, not error
      if (err?.response?.status === 404 || err?.response?.status === 204) {
        console.log('ℹ️ No pending teachers found (404/204)');
        setTeachers([]);
        setError(''); // Make sure no error is shown for 404/204
      } else {
        const errorMsg = err?.response?.data?.error || 'Errore nel caricamento dei teacher in attesa';
        setError(errorMsg);
        console.error('Setting error message:', errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Clear any previous states when component mounts
    setError('');
    setSuccess('');
    console.log('🎬 PendingTeachersCard component mounted');
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
        {error && !loading && (
          <Alert variant="danger" className="m-3">{error}</Alert>
        )}
        {success && <Alert variant="success" className="m-3">{success}</Alert>}
        {!loading && !error && teachers.length === 0 && (
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
