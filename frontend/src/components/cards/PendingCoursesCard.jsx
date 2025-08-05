import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import { fetchPendingCourses, approveCourse, rejectCourse } from '../../services/api/admin';

const PendingCoursesCard = () => {
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
      setCourses(res.data.slice(0, 5)); // Limit to 5 for dashboard card
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

  return (
    <Card className="widget-focus-lg">
      <Card.Header>
        <Card.Title as="h5">
          Corsi in Attesa
          {courses.length > 0 && (
            <Badge bg="warning" className="ms-2">{courses.length}</Badge>
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
        {!loading && courses.length === 0 && (
          <div className="text-center p-3 text-muted">
            <i className="feather icon-check-circle f-40 mb-2 text-success"></i>
            <p>Nessun corso in attesa di approvazione</p>
          </div>
        )}
        {!loading && courses.length > 0 && (
          <Table responsive hover className="recent-users">
            <tbody>
              {courses.map((course, index) => (
                <tr key={course.id} className={index === 0 ? 'unread' : ''}>
                  <td>
                    <div className="d-flex align-items-center">
                      <div className="me-3">
                        <div 
                          className="rounded-circle bg-info text-white d-flex align-items-center justify-content-center"
                          style={{ width: '40px', height: '40px' }}
                        >
                          {course.title?.[0]?.toUpperCase() || 'C'}
                        </div>
                      </div>
                      <div>
                        <h6 className="mb-1">{course.title}</h6>
                        <p className="text-muted mb-0">
                          da {course.teacher?.first_name} {course.teacher?.last_name}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="text-end">
                    <Button
                      variant="outline-success"
                      size="sm"
                      className="me-1"
                      disabled={actionLoading[course.id]}
                      onClick={() => handleApprove(course.id)}
                    >
                      {actionLoading[course.id] ? (
                        <Spinner size="sm" animation="border" />
                      ) : (
                        <i className="feather icon-check"></i>
                      )}
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      disabled={actionLoading[course.id]}
                      onClick={() => handleReject(course.id)}
                    >
                      {actionLoading[course.id] ? (
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

export default PendingCoursesCard;
