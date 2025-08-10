import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Row, Col, Card, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import { fetchCourseDetail, fetchLessonsForCourse } from '../../services/api/courses';
import MainCard from '../../components/Card/MainCard';
import { Helmet } from 'react-helmet';

const TeacherCourseDetail = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const handleBackToDashboard = () => navigate('/dashboard/teacher');
  const handleEditCourse = () => navigate(`/teacher/courses/${courseId}/edit`);

  useEffect(() => {
    let isMounted = true;
    const loadCourseData = async () => {
      try {
        setLoading(true);
        setError('');
        const courseData = await fetchCourseDetail(courseId);
        const lessonsData = await fetchLessonsForCourse(courseId);
        if (!isMounted) return;
        setCourse(courseData);
        setLessons(lessonsData || []);
      } catch (err) {
        if (!isMounted) return;
        setError('Errore nel caricamento del corso.');
      } finally {
        if (!isMounted) return;
        setLoading(false);
      }
    };
    loadCourseData();
    return () => {
      isMounted = false;
    };
  }, [courseId]);

  return (
    <>
      <Helmet>
        <title>SchoolPlatform Teacher Course Detail</title>
      </Helmet>

      {loading ? (
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
          <Spinner animation="border" variant="primary" />
          <span className="ms-3">Caricamento corso...</span>
        </div>
      ) : error ? (
        <div className="container mt-4">
          <Alert variant="danger">
            <Alert.Heading>Errore</Alert.Heading>
            <p>{error}</p>
            <Button variant="outline-danger" onClick={handleBackToDashboard}>
              Torna alla Dashboard
            </Button>
          </Alert>
        </div>
      ) : !course ? (
        <div className="container mt-4">
          <Alert variant="warning">
            <Alert.Heading>Corso non trovato</Alert.Heading>
            <p>Il corso richiesto non è stato trovato.</p>
            <Button variant="outline-warning" onClick={handleBackToDashboard}>
              Torna alla Dashboard
            </Button>
          </Alert>
        </div>
      ) : (
        <div className="container mt-4">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <Button variant="outline-secondary" onClick={handleBackToDashboard} className="mb-2">
                <i className="feather icon-arrow-left me-2"></i>
                Torna alla Dashboard
              </Button>
              <h2 className="mb-0">{course.title}</h2>
              <p className="text-muted">Gestione corso - Vista Teacher</p>
            </div>
            <div>
              <Button variant="primary" onClick={handleEditCourse} className="me-2">
                <i className="feather icon-edit me-2"></i>
                Modifica Corso
              </Button>
            </div>
          </div>

          <Row>
            <Col lg={8}>
              <MainCard title="Informazioni Corso">
                <div className="course-info">
                  <div className="mb-3">
                    <h5>Descrizione</h5>
                    <p>{course.description || 'Nessuna descrizione disponibile'}</p>
                  </div>
                  <div className="mb-3">
                    <h5>Dettagli</h5>
                    <Row>
                      <Col md={6}>
                        <p>
                          <strong>Prezzo:</strong> {course.price_eur} EUR
                        </p>
                        <p>
                          <strong>Categoria:</strong> {course.category || 'Non specificata'}
                        </p>
                      </Col>
                      <Col md={6}>
                        <p>
                          <strong>Creato il:</strong> {course.created_at ? new Date(course.created_at).toLocaleDateString('it-IT') : '-'}
                        </p>
                        <p>
                          <strong>Stato:</strong>
                          <Badge bg={course.is_active ? 'success' : 'warning'} className="ms-2">
                            {course.is_active ? 'Attivo' : 'Inattivo'}
                          </Badge>
                        </p>
                      </Col>
                    </Row>
                  </div>

                  {course.cover_image && (
                    <div className="mb-3">
                      <h5>Immagine di copertina</h5>
                      <img src={course.cover_image} alt={course.title} className="img-fluid rounded" style={{ maxHeight: '300px' }} />
                    </div>
                  )}
                </div>
              </MainCard>
            </Col>

            <Col lg={4}>
              <MainCard title="Statistiche">
                <div className="stats-info">
                  <div className="stat-item mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Lezioni:</span>
                      <Badge bg="info">{lessons.length}</Badge>
                    </div>
                  </div>
                  <div className="stat-item mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Studenti iscritti:</span>
                      <Badge bg="success">{course.enrolled_students || 0}</Badge>
                    </div>
                  </div>
                  <div className="stat-item mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Prezzo:</span>
                      <Badge bg="primary">{course.price_eur} EUR</Badge>
                    </div>
                  </div>
                </div>
              </MainCard>
            </Col>
          </Row>

          <Row className="mt-4">
            <Col lg={12}>
              <MainCard title={`Lezioni (${lessons.length})`}>
                {lessons.length === 0 ? (
                  <div className="container mt-4 text-center">
                    <i className="feather icon-book" style={{ fontSize: '3rem', color: '#999', marginBottom: '1rem' }}></i>
                    <h4 className="mb-3">Nessuna lezione</h4>
                    <p className="text-muted mb-4">Questo corso non ha ancora lezioni</p>
                    <Button variant="primary" onClick={() => navigate('/dashboard/teacher')}>
                      <i className="feather icon-plus me-2"></i>
                      Aggiungi Lezione
                    </Button>
                  </div>
                ) : (
                  <div className="lessons-list">
                    {lessons.map((lesson, index) => (
                      <Card key={lesson.id} className="mb-3">
                        <Card.Body>
                          <div className="d-flex align-items-center justify-content-between">
                            <div className="d-flex align-items-center">
                              <div className="lesson-number me-3">
                                <span className="badge bg-success rounded-circle">{index + 1}</span>
                              </div>
                              <div>
                                <h6 className="mb-1">{lesson.title}</h6>
                                <p className="text-muted small mb-0">
                                  {lesson.description ? `${lesson.description.substring(0, 100)}...` : 'Nessuna descrizione'}
                                </p>
                              </div>
                            </div>
                            <div className="lesson-actions">
                              <Link to={`/lezioni-docente/${lesson.id}`} className="btn btn-outline-primary btn-sm me-2">
                                <i className="feather icon-eye me-1"></i>
                                Visualizza
                              </Link>
                              <Button variant="outline-secondary" size="sm" onClick={() => navigate(`/teacher/lezioni/${lesson.id}/edit`)}>
                                <i className="feather icon-edit"></i>
                              </Button>
                            </div>
                          </div>
                        </Card.Body>
                      </Card>
                    ))}
                  </div>
                )}
              </MainCard>
            </Col>
          </Row>
        </div>
      )}
    </>
  );
};

export default TeacherCourseDetail;
