import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, Row, Col, Card, Button, Badge, Alert, 
  ProgressBar, Tabs, Tab, Spinner, Accordion 
} from 'react-bootstrap';
import { fetchCourseDetail, fetchLessonsForCourse } from '../../services/api/courses';
import './CoursePreview.css';

const CoursePreview = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const loadCourseData = async () => {
      try {
        setLoading(true);
        
        // Fetch course details
        const courseData = await fetchCourseDetail(courseId);
        setCourse(courseData);
        
        // Fetch lessons
        const lessonsData = await fetchLessonsForCourse(courseId);
        setLessons(lessonsData.data || []);
        
      } catch (err) {
        console.error('Error loading course:', err);
        setError('Errore nel caricamento del corso');
      } finally {
        setLoading(false);
      }
    };

    if (courseId) {
      loadCourseData();
    }
  }, [courseId]);

  const getCategoryColor = (category) => {
    const categoryColors = {
      'Programmazione': '#007bff',
      'Design': '#28a745',
      'Marketing': '#dc3545',
      'Business': '#ffc107',
      'Lingue': '#17a2b8',
      'Arte': '#6f42c1',
      'Musica': '#fd7e14',
      'Salute': '#20c997',
      'Sport': '#e83e8c',
      'Cucina': '#6c757d'
    };
    return categoryColors[category] || '#6c757d';
  };

  const getBadgeVariant = (status) => {
    switch (status?.toLowerCase()) {
      case 'published': return 'success';
      case 'draft': return 'warning';
      case 'archived': return 'secondary';
      default: return 'primary';
    }
  };

  const getCompletionPercentage = () => {
    if (!lessons.length) return 0;
    const completedLessons = lessons.filter(lesson => 
      lesson.exercises && lesson.exercises.length > 0
    ).length;
    return Math.round((completedLessons / lessons.length) * 100);
  };

  const getTotalDuration = () => {
    return lessons.reduce((total, lesson) => {
      return total + (parseInt(lesson.duration) || 30);
    }, 0);
  };

  const getTotalExercises = () => {
    return lessons.reduce((total, lesson) => {
      return total + (lesson.exercises?.length || 0);
    }, 0);
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="text-center">
          <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
          <p className="mt-3 text-muted">Caricamento corso...</p>
        </div>
      </Container>
    );
  }

  if (error || !course) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">
          <Alert.Heading>Errore</Alert.Heading>
          <p>{error || 'Corso non trovato'}</p>
          <Button variant="outline-danger" onClick={() => navigate('/dashboard/teacher')}>
            Torna alla Dashboard
          </Button>
        </Alert>
      </Container>
    );
  }

  return (
    <div className="course-preview">
      {/* Hero Section */}
      <div className="course-hero" style={{
        background: `linear-gradient(135deg, ${getCategoryColor(course.category)}15 0%, ${getCategoryColor(course.category)}05 100%)`,
        borderBottom: `4px solid ${getCategoryColor(course.category)}40`
      }}>
        <Container>
          <Row className="align-items-center py-5">
            <Col lg={8}>
              <div className="d-flex align-items-center mb-3">
                <Button 
                  variant="outline-secondary" 
                  size="sm"
                  onClick={() => navigate('/dashboard/teacher')}
                  className="me-3"
                >
                  <i className="feather icon-arrow-left me-1"></i>
                  Dashboard
                </Button>
                <Badge 
                  className="px-3 py-2"
                  style={{
                    background: getCategoryColor(course.category),
                    color: 'white',
                    borderRadius: '20px',
                    fontSize: '0.9rem'
                  }}
                >
                  {course.category || 'Generale'}
                </Badge>
                <Badge 
                  variant={getBadgeVariant(course.status)}
                  className="ms-2 px-3 py-2"
                  style={{ borderRadius: '20px', fontSize: '0.9rem' }}
                >
                  {course.status || 'Draft'}
                </Badge>
              </div>
              
              <h1 className="display-5 fw-bold mb-3 text-dark">{course.title}</h1>
              <p className="lead text-muted mb-4">{course.description}</p>
              
              <div className="d-flex gap-4 mb-4">
                <div className="text-center">
                  <div className="h4 mb-1 text-primary fw-bold">{lessons.length}</div>
                  <small className="text-muted">Lezioni</small>
                </div>
                <div className="text-center">
                  <div className="h4 mb-1 text-warning fw-bold">{getTotalExercises()}</div>
                  <small className="text-muted">Esercizi</small>
                </div>
                <div className="text-center">
                  <div className="h4 mb-1 text-success fw-bold">{Math.round(getTotalDuration() / 60)}h</div>
                  <small className="text-muted">Durata</small>
                </div>
                <div className="text-center">
                  <div className="h4 mb-1 text-info fw-bold">{course.students_count || 0}</div>
                  <small className="text-muted">Studenti</small>
                </div>
              </div>
              
              <div className="d-flex gap-3">
                <Button 
                  variant="primary"
                  size="lg"
                  onClick={() => navigate(`/teacher/corsi/${courseId}/edit`)}
                  style={{
                    background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                    border: 'none',
                    borderRadius: '25px',
                    boxShadow: '0 4px 15px rgba(4, 169, 245, 0.3)'
                  }}
                >
                  <i className="feather icon-edit me-2"></i>
                  Modifica Corso
                </Button>
                <Button 
                  variant="outline-secondary"
                  size="lg"
                  onClick={() => navigate(`/teacher/corsi/${courseId}/preview`)}
                  style={{ borderRadius: '25px' }}
                >
                  <i className="feather icon-eye me-2"></i>
                  Anteprima Student
                </Button>
              </div>
            </Col>
            
            <Col lg={4}>
              <Card className="course-stats-card border-0 shadow-lg">
                <Card.Body className="p-4">
                  <div className="text-center mb-4">
                    {course.image ? (
                      <img 
                        src={course.image} 
                        alt={course.title}
                        className="course-preview-image rounded-lg"
                        style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                      />
                    ) : (
                      <div 
                        className="course-placeholder-large d-flex align-items-center justify-content-center rounded-lg"
                        style={{
                          width: '100%',
                          height: '200px',
                          background: `linear-gradient(135deg, ${getCategoryColor(course.category)} 0%, ${getCategoryColor(course.category)}99 100%)`
                        }}
                      >
                        <i className="feather icon-book-open text-white" style={{ fontSize: '4rem' }}></i>
                      </div>
                    )}
                  </div>
                  
                  <div className="text-center">
                    <h4 className="text-primary fw-bold mb-1">
                      {parseFloat(course.price || 0).toFixed(2)} TEO
                    </h4>
                    <small className="text-muted">Prezzo del Corso</small>
                  </div>
                  
                  <hr className="my-4" />
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-semibold">Completamento</span>
                      <span className="text-primary fw-bold">{getCompletionPercentage()}%</span>
                    </div>
                    <ProgressBar 
                      now={getCompletionPercentage()} 
                      style={{ height: '8px', borderRadius: '4px' }}
                      variant={getCompletionPercentage() > 70 ? 'success' : getCompletionPercentage() > 40 ? 'warning' : 'danger'}
                    />
                  </div>
                  
                  <div className="course-meta">
                    <div className="d-flex justify-content-between py-2 border-bottom">
                      <span className="text-muted">Livello:</span>
                      <Badge variant="info" style={{ borderRadius: '10px' }}>
                        {course.level || 'Principiante'}
                      </Badge>
                    </div>
                    <div className="d-flex justify-content-between py-2 border-bottom">
                      <span className="text-muted">Durata:</span>
                      <span className="fw-semibold">{course.duration || 'Non specificata'}</span>
                    </div>
                    <div className="d-flex justify-content-between py-2">
                      <span className="text-muted">Certificato:</span>
                      <span className="fw-semibold">
                        {course.certificate ? 
                          <Badge variant="success">Disponibile</Badge> : 
                          <Badge variant="secondary">Non disponibile</Badge>
                        }
                      </span>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </div>

      {/* Content Tabs */}
      <Container className="mt-5">
        <Card className="border-0 shadow-sm">
          <Card.Body className="p-0">
            <Tabs
              activeKey={activeTab}
              onSelect={(k) => setActiveTab(k)}
              className="custom-tabs border-bottom-0"
              style={{ borderBottom: 'none' }}
            >
              <Tab eventKey="overview" title={
                <span><i className="feather icon-info me-2"></i>Panoramica</span>
              }>
                <div className="p-4">
                  <Row>
                    <Col lg={8}>
                      <div className="course-overview">
                        <h4 className="mb-4">Descrizione del Corso</h4>
                        <div className="content-section">
                          <p className="lead">{course.description}</p>
                          
                          {course.learning_objectives && course.learning_objectives.length > 0 && (
                            <div className="mt-4">
                              <h5 className="mb-3">Obiettivi di Apprendimento</h5>
                              <ul className="learning-objectives">
                                {course.learning_objectives.map((objective, index) => (
                                  <li key={index} className="mb-2">
                                    <i className="feather icon-check-circle text-success me-2"></i>
                                    {objective}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {course.prerequisites && (
                            <div className="mt-4">
                              <h5 className="mb-3">Prerequisiti</h5>
                              <p className="text-muted">{course.prerequisites}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </Col>
                    
                    <Col lg={4}>
                      <div className="course-sidebar">
                        <Card className="border-0 bg-light">
                          <Card.Body>
                            <h6 className="mb-3 fw-bold">Statistiche Corso</h6>
                            <div className="stats-grid">
                              <div className="stat-item d-flex justify-content-between py-2">
                                <span className="text-muted">Iscritti:</span>
                                <Badge variant="success">{course.students_count || 0}</Badge>
                              </div>
                              <div className="stat-item d-flex justify-content-between py-2">
                                <span className="text-muted">Visualizzazioni:</span>
                                <Badge variant="info">{course.views || 0}</Badge>
                              </div>
                              <div className="stat-item d-flex justify-content-between py-2">
                                <span className="text-muted">Rating:</span>
                                <div>
                                  <span className="text-warning">★★★★☆</span>
                                  <small className="text-muted ms-1">(4.2)</small>
                                </div>
                              </div>
                            </div>
                          </Card.Body>
                        </Card>
                      </div>
                    </Col>
                  </Row>
                </div>
              </Tab>
              
              <Tab eventKey="curriculum" title={
                <span><i className="feather icon-list me-2"></i>Curriculum</span>
              }>
                <div className="p-4">
                  <div className="d-flex justify-content-between align-items-center mb-4">
                    <h4 className="mb-0">Curriculum del Corso</h4>
                    <Badge variant="primary" className="px-3 py-2" style={{ borderRadius: '15px' }}>
                      {lessons.length} Lezioni
                    </Badge>
                  </div>
                  
                  {lessons.length > 0 ? (
                    <Accordion className="lessons-accordion">
                      {lessons.map((lesson, index) => (
                        <Accordion.Item key={lesson.id} eventKey={index.toString()}>
                          <Accordion.Header>
                            <div className="d-flex align-items-center justify-content-between w-100 me-3">
                              <div className="d-flex align-items-center">
                                <Badge 
                                  className="me-3 px-3 py-2"
                                  style={{
                                    background: 'linear-gradient(135deg, #28a745, #20c997)',
                                    borderRadius: '15px'
                                  }}
                                >
                                  #{index + 1}
                                </Badge>
                                <div>
                                  <h6 className="mb-1">{lesson.title}</h6>
                                  <div className="d-flex gap-3">
                                    <small className="text-muted">
                                      <i className="feather icon-clock me-1"></i>
                                      {lesson.duration || '30'} min
                                    </small>
                                    <small className="text-muted">
                                      <i className="feather icon-target me-1"></i>
                                      {lesson.exercises?.length || 0} esercizi
                                    </small>
                                    <Badge 
                                      variant={lesson.lesson_type === 'video' ? 'warning' : 'info'}
                                      style={{ fontSize: '0.7rem' }}
                                    >
                                      {lesson.lesson_type || 'theory'}
                                    </Badge>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </Accordion.Header>
                          <Accordion.Body>
                            <div className="lesson-content">
                              <p className="mb-3">{lesson.content || 'Contenuto della lezione non specificato.'}</p>
                              
                              {lesson.exercises && lesson.exercises.length > 0 && (
                                <div className="exercises-section">
                                  <h6 className="mb-3 fw-bold text-warning">
                                    <i className="feather icon-target me-2"></i>
                                    Esercizi ({lesson.exercises.length})
                                  </h6>
                                  <div className="exercises-list">
                                    {lesson.exercises.map((exercise, exerciseIndex) => (
                                      <div key={exercise.id} className="exercise-item p-3 mb-2 rounded border">
                                        <div className="d-flex justify-content-between align-items-center">
                                          <div>
                                            <h6 className="mb-1">{exercise.title}</h6>
                                            <div className="d-flex gap-2">
                                              <Badge variant="secondary" style={{ fontSize: '0.75rem' }}>
                                                {exercise.exercise_type || 'practical'}
                                              </Badge>
                                              <Badge variant="info" style={{ fontSize: '0.75rem' }}>
                                                {exercise.difficulty || 'beginner'}
                                              </Badge>
                                              {exercise.time_estimate && (
                                                <Badge variant="warning" style={{ fontSize: '0.75rem' }}>
                                                  {exercise.time_estimate} min
                                                </Badge>
                                              )}
                                            </div>
                                          </div>
                                          <div className="d-flex gap-2">
                                            <Button
                                              variant="outline-primary"
                                              size="sm"
                                              onClick={() => navigate(`/teacher/esercizi/${exercise.id}`)}
                                            >
                                              <i className="feather icon-eye"></i>
                                            </Button>
                                            <Button
                                              variant="outline-secondary"
                                              size="sm"
                                              onClick={() => navigate(`/teacher/esercizi/${exercise.id}/edit`)}
                                            >
                                              <i className="feather icon-edit"></i>
                                            </Button>
                                          </div>
                                        </div>
                                        {exercise.description && (
                                          <p className="mt-2 mb-0 text-muted small">{exercise.description}</p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              <div className="lesson-actions mt-3 pt-3 border-top">
                                <div className="d-flex gap-2">
                                  <Button
                                    variant="outline-primary"
                                    size="sm"
                                    onClick={() => navigate(`/teacher/lezioni/${lesson.id}`)}
                                  >
                                    <i className="feather icon-eye me-1"></i>
                                    Visualizza Lezione
                                  </Button>
                                  <Button
                                    variant="outline-secondary"
                                    size="sm"
                                    onClick={() => navigate(`/teacher/lezioni/${lesson.id}/edit`)}
                                  >
                                    <i className="feather icon-edit me-1"></i>
                                    Modifica Lezione
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </Accordion.Body>
                        </Accordion.Item>
                      ))}
                    </Accordion>
                  ) : (
                    <div className="text-center py-5">
                      <i className="feather icon-book text-muted mb-3" style={{ fontSize: '4rem' }}></i>
                      <h5 className="text-muted mb-3">Nessuna lezione disponibile</h5>
                      <p className="text-muted mb-4">Inizia aggiungendo la prima lezione al tuo corso.</p>
                      <Button 
                        variant="primary"
                        onClick={() => navigate(`/teacher/corsi/${courseId}/lezioni/create`)}
                        style={{
                          background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                          border: 'none',
                          borderRadius: '25px'
                        }}
                      >
                        <i className="feather icon-plus me-2"></i>
                        Crea Prima Lezione
                      </Button>
                    </div>
                  )}
                </div>
              </Tab>
              
              <Tab eventKey="analytics" title={
                <span><i className="feather icon-bar-chart-2 me-2"></i>Analytics</span>
              }>
                <div className="p-4">
                  <h4 className="mb-4">Analytics del Corso</h4>
                  <Row>
                    <Col md={6} lg={3} className="mb-4">
                      <Card className="border-0 bg-primary text-white h-100">
                        <Card.Body className="text-center">
                          <i className="feather icon-users mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <h3 className="mb-1">{course.students_count || 0}</h3>
                          <p className="mb-0">Studenti Iscritti</p>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={6} lg={3} className="mb-4">
                      <Card className="border-0 bg-success text-white h-100">
                        <Card.Body className="text-center">
                          <i className="feather icon-trending-up mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <h3 className="mb-1">{getCompletionPercentage()}%</h3>
                          <p className="mb-0">Tasso Completamento</p>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={6} lg={3} className="mb-4">
                      <Card className="border-0 bg-warning text-white h-100">
                        <Card.Body className="text-center">
                          <i className="feather icon-star mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <h3 className="mb-1">4.2</h3>
                          <p className="mb-0">Rating Medio</p>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={6} lg={3} className="mb-4">
                      <Card className="border-0 bg-info text-white h-100">
                        <Card.Body className="text-center">
                          <i className="feather icon-eye mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <h3 className="mb-1">{course.views || 0}</h3>
                          <p className="mb-0">Visualizzazioni</p>
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>
                  
                  <Card className="border-0 shadow-sm mt-4">
                    <Card.Body>
                      <h5 className="mb-4">Engagement per Lezione</h5>
                      <div className="text-center py-5">
                        <i className="feather icon-bar-chart text-muted mb-3" style={{ fontSize: '3rem' }}></i>
                        <p className="text-muted">Grafici analytics in sviluppo...</p>
                      </div>
                    </Card.Body>
                  </Card>
                </div>
              </Tab>
            </Tabs>
          </Card.Body>
        </Card>
      </Container>
    </div>
  );
};

export default CoursePreview;
