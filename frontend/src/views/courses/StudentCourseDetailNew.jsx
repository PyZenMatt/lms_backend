import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';
import { fetchUserRole } from '../../services/api/auth';
import api from '../../services/core/axiosClient';
import MainCard from '../../components/Card/MainCard';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const StudentCourseDetailNew = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        console.log('🔍 Fetching course:', courseId);
        const response = await api.get(`/courses/${courseId}/`);
        console.log('📚 Course data:', response.data);
        setCourse(response.data);
      } catch (error) {
        console.error('❌ Error fetching course:', error);
      }
    };

    const fetchLessons = async () => {
      try {
        console.log('🔍 Fetching lessons for course:', courseId);
        const response = await api.get(`/courses/${courseId}/lessons/`);
        console.log('📋 Lessons data:', response.data);
        setLessons(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error('❌ Error fetching lessons:', error);
        setLessons([]);
      }
    };

    const fetchRole = async () => {
      try {
        const role = await fetchUserRole();
        setUserRole(role);
      } catch {
        setUserRole('');
      }
    };

    fetchCourse();
    fetchLessons();
    fetchRole();
    setLoading(false);
  }, [courseId]);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <Alert variant="warning" className="text-center" style={{ maxWidth: '500px' }}>
          <h3 className="alert-heading">Corso non trovato</h3>
          <p>Il corso che stai cercando non esiste o non è più disponibile.</p>
        </Alert>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      {/* Course Hero Section */}
      <div className="bg-primary text-white py-4 mb-4">
        <div className="container">
          <div className="text-center">
            <div className="mb-3" style={{ maxWidth: '200px', margin: '0 auto' }}>
              {course.cover ? (
                <img
                  src={course.cover.startsWith('http') ? course.cover : `http://127.0.0.1:8000${course.cover}`}
                  alt={course.title}
                  className="img-fluid rounded"
                  style={{ border: '4px solid #fff', boxShadow: '0 10px 20px rgba(0,0,0,0.1)' }}
                />
              ) : (
                <div
                  className="d-flex justify-content-center align-items-center bg-primary-light rounded"
                  style={{ height: '200px', width: '200px' }}
                >
                  <i className="feather icon-book-open" style={{ fontSize: '4rem' }}></i>
                </div>
              )}
            </div>
            <h1 className="mb-2">{course.title}</h1>
            <p className="text-white-50 mb-3">{course.description}</p>
            <div className="d-inline-block px-3 py-1 rounded bg-primary-light">
              <i className="feather icon-user mr-1"></i>
              <strong>Docente:</strong> {course.teacher?.username || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      <div className="container">
        {/* Course Stats */}
        <Row className="mb-4">
          <Col sm={6} md={3} className="mb-3">
            <Card className="shadow-sm h-100">
              <Card.Body className="text-center">
                <div className="d-flex justify-content-center align-items-center mb-3">
                  <div
                    className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center"
                    style={{ width: '60px', height: '60px' }}
                  >
                    <i className="feather icon-play-circle" style={{ fontSize: '1.5rem' }}></i>
                  </div>
                </div>
                <h3 className="mb-1">{lessons.length}</h3>
                <p className="text-muted mb-0 small text-uppercase">Lezioni</p>
              </Card.Body>
            </Card>
          </Col>

          <Col sm={6} md={3} className="mb-3">
            <Card className="shadow-sm h-100">
              <Card.Body className="text-center">
                <div className="d-flex justify-content-center align-items-center mb-3">
                  <div
                    className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center"
                    style={{ width: '60px', height: '60px' }}
                  >
                    <i className="feather icon-clock" style={{ fontSize: '1.5rem' }}></i>
                  </div>
                </div>
                <h3 className="mb-1">{lessons.reduce((total, lesson) => total + (lesson.duration || 0), 0)}</h3>
                <p className="text-muted mb-0 small text-uppercase">Minuti Totali</p>
              </Card.Body>
            </Card>
          </Col>

          <Col sm={6} md={3} className="mb-3">
            <Card className="shadow-sm h-100">
              <Card.Body className="text-center">
                <div className="d-flex justify-content-center align-items-center mb-3">
                  <div
                    className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center"
                    style={{ width: '60px', height: '60px' }}
                  >
                    <i className="feather icon-award" style={{ fontSize: '1.5rem' }}></i>
                  </div>
                </div>
                <h3 className="mb-1">{course.difficulty || 'Intermedio'}</h3>
                <p className="text-muted mb-0 small text-uppercase">Livello</p>
              </Card.Body>
            </Card>
          </Col>

          <Col sm={6} md={3} className="mb-3">
            <Card className="shadow-sm h-100">
              <Card.Body className="text-center">
                <div className="d-flex justify-content-center align-items-center mb-3">
                  <div
                    className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center"
                    style={{ width: '60px', height: '60px' }}
                  >
                    <i className="feather icon-users" style={{ fontSize: '1.5rem' }}></i>
                  </div>
                </div>
                <h3 className="mb-1">{course.enrolled_students_count || 0}</h3>
                <p className="text-muted mb-0 small text-uppercase">Studenti</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Lessons Content */}
        <Row>
          <Col md={12}>
            <MainCard
              title={
                <span>
                  <i className="feather icon-list text-primary mr-2"></i>
                  Lezioni del Corso
                </span>
              }
            >
              {lessons.length === 0 ? (
                <div
                  className="text-center p-5 bg-light border border-2 border-secondary border-opacity-25 rounded"
                  style={{ borderStyle: 'dashed' }}
                >
                  <i className="feather icon-book text-primary mb-3" style={{ fontSize: '4rem', display: 'block' }}></i>
                  <h4 className="text-dark mb-3">Nessuna lezione disponibile</h4>
                  <p className="text-muted">Le lezioni per questo corso non sono ancora state pubblicate.</p>
                </div>
              ) : (
                <Row>
                  {lessons.map((lesson, index) => (
                    <Col md={6} xl={4} key={lesson.id} className="mb-3">
                      <Card className="shadow-sm h-100">
                        <Card.Body className="position-relative">
                          <div className="position-absolute" style={{ top: '10px', right: '10px' }}>
                            <div
                              className="badge badge-primary rounded-circle"
                              style={{ width: '30px', height: '30px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                            >
                              {lesson.order || index + 1}
                            </div>
                          </div>
                          <h5 className="mb-3 pr-4">{lesson.title}</h5>

                          <div className="d-flex mb-3 text-muted small">
                            {lesson.duration && (
                              <div className="mr-3">
                                <i className="feather icon-clock mr-1"></i>
                                {lesson.duration} min
                              </div>
                            )}
                            {lesson.type && (
                              <div>
                                <i className="feather icon-video mr-1"></i>
                                {lesson.type}
                              </div>
                            )}
                          </div>

                          <div className="progress mb-3" style={{ height: '4px' }}>
                            <div className="progress-bar bg-primary" style={{ width: `${Math.random() * 100}%` }}></div>
                          </div>

                          {Math.random() > 0.7 ? (
                            <div className="badge badge-success">Completata</div>
                          ) : Math.random() > 0.4 ? (
                            <div className="badge badge-warning">In Corso</div>
                          ) : (
                            <div className="badge badge-light">Da Iniziare</div>
                          )}

                          <div className="mt-3">
                            <Link to={`/lezioni/${lesson.id}`} className="btn btn-primary btn-sm">
                              Visualizza Lezione
                            </Link>
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              )}
            </MainCard>
          </Col>
        </Row>

        {/* Navigation */}
        <Row className="mt-4 mb-5">
          <Col className="text-center">
            <Link
              to={userRole === 'admin' ? '/dashboard/admin' : userRole === 'teacher' ? '/dashboard/teacher' : '/dashboard/student'}
              className="btn btn-primary"
            >
              <i className="feather icon-arrow-left mr-2"></i>
              {userRole === 'admin'
                ? 'Torna alla dashboard admin'
                : userRole === 'teacher'
                  ? 'Torna alla dashboard docente'
                  : 'Torna alla dashboard studente'}
            </Link>
          </Col>
        </Row>

        {completed && (
          <Row className="mb-4">
            <Col md={12}>
              <MainCard
                title={
                  <span>
                    <i className="feather icon-target text-primary mr-2"></i>
                    Esercizi della lezione
                  </span>
                }
              >
                {exercises.length === 0 ? (
                  <div
                    className="text-center p-5 bg-light border border-2 border-secondary border-opacity-25 rounded"
                    style={{ borderStyle: 'dashed' }}
                  >
                    <p className="text-muted">Nessun esercizio disponibile per questa lezione.</p>
                  </div>
                ) : (
                  <Row>
                    {exercises.map((ex) => (
                      <Col md={6} xl={4} key={ex.id} className="mb-3">
                        <Card className="shadow-sm h-100">
                          <Card.Body>
                            <h5 className="mb-3">{ex.title}</h5>
                            <p className="text-muted mb-3">{ex.description}</p>
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                )}
              </MainCard>
            </Col>
          </Row>
        )}
      </div>
    </div>
  );
};

export default StudentCourseDetailNew;
