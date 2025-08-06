import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge } from 'react-bootstrap';
import { fetchUserRole } from '../../services/api/auth';
import api from '../../services/core/axiosClient';
import MainCard from '../../components/Card/MainCard';

const StudentLessonDetailNew = () => {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const fetchLesson = async () => {
      try {
        console.log('🔍 StudentLessonDetailNew - lessonId from params:', lessonId, 'type:', typeof lessonId);
        
        // Ensure lessonId is a string/number, not an object
        const cleanLessonId = lessonId?.toString() || lessonId;
        console.log('🔧 Cleaned lessonId:', cleanLessonId);
        
        const response = await api.get(`/lessons/${cleanLessonId}/`);
        const data = response.data;
        console.log('📚 Lesson data received:', data);
        setLesson(data);
        setCompleted(data.completed || false);
      } catch (error) {
        console.error('❌ Error fetching lesson:', error);
      }
    };
    fetchLesson();
    setLoading(false);
  }, [lessonId]);

  useEffect(() => {
    if (!lessonId) return;
    const fetchExercises = async () => {
      try {
        console.log('🏋️ Fetching exercises for lessonId:', lessonId, 'type:', typeof lessonId);
        
        // Ensure lessonId is a string/number, not an object
        const cleanLessonId = lessonId?.toString() || lessonId;
        console.log('🔧 Cleaned lessonId for exercises:', cleanLessonId);
        
        const response = await api.get(`/lessons/${cleanLessonId}/exercises/`);
        const data = response.data;
        console.log('📝 Exercises data received:', data);
        setExercises(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('❌ Error fetching exercises:', error);
        setExercises([]);
      }
    };
    fetchExercises();
  }, [lessonId]);

  useEffect(() => {
    const fetchRole = async () => {
      try {
        const role = await fetchUserRole();
        setUserRole(role);
      } catch {
        setUserRole('');
      }
    };
    fetchRole();
  }, []);

  const handleComplete = async () => {
    if (completed || actionLoading) return;
    
    try {
      setActionLoading(true);
      await api.post(`/lessons/${lessonId}/mark_complete/`, {});
      
      const response = await api.get(`/lessons/${lessonId}/`);
      const lessonData = response.data;
      setLesson(lessonData);
      setCompleted(lessonData.completed || false);
      
      setTimeout(() => {
        setActionLoading(false);
      }, 500);
      
    } catch (error) {
      console.error('Error marking lesson complete:', error);
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <Spinner animation="border" variant="primary" />
      </Container>
    );
  }
  
  if (!lesson) {
    return (
      <Container>
        <Row className="justify-content-center">
          <Col md={8}>
            <Alert variant="warning" className="text-center">
              <i className="feather icon-alert-triangle mr-2"></i>
              Lezione non trovata
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container fluid>
      {/* Hero Section */}
      <Row className="mb-4">
        <Col>
          <MainCard>
            <div className="d-flex justify-content-between align-items-start">
              <div>
                <h1 className="mb-3">{lesson.title}</h1>
                <div className="d-flex align-items-center gap-3 mb-3">
                  {lesson.duration && (
                    <Badge bg="light" text="dark" className="p-2">
                      <i className="feather icon-clock mr-1"></i>
                      {lesson.duration} min
                    </Badge>
                  )}
                  <Badge 
                    bg={completed ? 'success' : 'warning'} 
                    className="p-2"
                  >
                    <i className={`feather ${completed ? 'icon-check-circle' : 'icon-play-circle'} mr-1`}></i>
                    {completed ? 'Completata' : 'In corso'}
                  </Badge>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="d-flex gap-2">
                {userRole !== 'admin' && (
                  <Button
                    variant={completed ? 'success' : 'primary'}
                    onClick={handleComplete}
                    disabled={completed || actionLoading}
                    className="d-flex align-items-center"
                  >
                    {actionLoading ? (
                      <Spinner animation="border" size="sm" className="mr-2" />
                    ) : (
                      <i className={`feather ${completed ? 'icon-check' : 'icon-check-circle'} mr-2`}></i>
                    )}
                    {actionLoading ? 'Completamento...' : completed ? 'Completata' : 'Completa lezione'}
                  </Button>
                )}
                
                <Link 
                  to={lesson?.course_id ? `/corsi/${lesson.course_id}` : 
                      userRole === 'admin' ? "/dashboard/admin" : 
                      userRole === 'teacher' ? "/dashboard/teacher" : "/dashboard/student"} 
                  className="btn btn-outline-primary d-flex align-items-center"
                >
                  <i className="feather icon-arrow-left mr-2"></i>
                  {lesson?.course_id ? 'Torna al corso' : 
                   userRole === 'admin' ? 'Torna alla dashboard admin' : 
                   userRole === 'teacher' ? 'Torna alla dashboard docente' : 'Torna alla dashboard studente'}
                </Link>
              </div>
            </div>
          </MainCard>
        </Col>
      </Row>

      <Row>
        {/* Main Content */}
        <Col lg={8}>
          {/* Video Section */}
          {lesson.video_file_url && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-play-circle text-primary mr-2"></i>
                  Video della lezione
                </h5>
              </Card.Header>
              <Card.Body className="p-0">
                <div className="ratio ratio-16x9">
                  <video controls className="rounded-bottom">
                    <source src={lesson.video_file_url} type="video/mp4" />
                    Il tuo browser non supporta il video.
                  </video>
                </div>
              </Card.Body>
            </Card>
          )}

          {/* Content Section */}
          {lesson.content && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-book-open text-primary mr-2"></i>
                  Contenuto della lezione
                </h5>
              </Card.Header>
              <Card.Body>
                <div className="lesson-content" dangerouslySetInnerHTML={{ __html: lesson.content }} />
              </Card.Body>
            </Card>
          )}

          {/* Materials Section */}
          {lesson.materials && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-package text-primary mr-2"></i>
                  Materiali
                </h5>
              </Card.Header>
              <Card.Body>
                <div className="materials-content" dangerouslySetInnerHTML={{ __html: lesson.materials }} />
              </Card.Body>
            </Card>
          )}
        </Col>

        {/* Sidebar */}
        <Col lg={4}>
          {/* Exercises Section */}
          {completed && (
            <Card>
              <Card.Header>
                <h5 className="mb-0">
                  <i className="feather icon-target text-primary mr-2"></i>
                  Esercizi della lezione
                </h5>
              </Card.Header>
              <Card.Body>
                {exercises.length === 0 ? (
                  <Alert variant="info" className="mb-0">
                    <i className="feather icon-info mr-2"></i>
                    Nessun esercizio disponibile per questa lezione.
                  </Alert>
                ) : (
                  <div className="d-grid gap-3">
                    {exercises.map(ex => (
                      <Card key={ex.id} className="border">
                        <Card.Body className="p-3">
                          <h6 className="card-title mb-2">{ex.title}</h6>
                          <p className="card-text text-muted mb-3 small">{ex.description}</p>
                          <Link 
                            to={`/esercizi/${ex.id}`} 
                            className="btn btn-sm btn-primary w-100"
                          >
                            <i className="feather icon-arrow-right mr-1"></i>
                            Vai all'esercizio
                          </Link>
                        </Card.Body>
                      </Card>
                    ))}
                  </div>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Progress Info */}
          {!completed && (
            <Card className="border-warning">
              <Card.Body className="text-center">
                <i className="feather icon-info text-warning mb-3" style={{ fontSize: '2rem' }}></i>
                <h6>Completa la lezione</h6>
                <p className="text-muted small mb-0">
                  Una volta completata la lezione, potrai accedere agli esercizi
                </p>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default StudentLessonDetailNew;
