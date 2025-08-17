import React, { useState } from 'react';
import { Card, Badge, Button, Row, Col, Collapse, ProgressBar, InputGroup } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import './CoursesTable.scss';

const CoursesTable = ({
  courses = [],
  showActions = true,
  onCreateLesson,
  showCreateCourse = false,
  onCreateCourse,
  expandedCourse,
  onExpandCourse,
  courseLessons = {},
  onCreateExercise,
  lessonExercises = {},
  loadingExercises = {},
  onLoadExercises,
  onViewCourse,
  onViewLesson,
  onEditCourse,
  onEditLesson,
  onViewExercise,
  onEditExercise,
  onViewLessons // Nuova prop per visualizzare le lezioni di un corso
}) => {
  const navigate = useNavigate();

  // Fallbacks per azioni se non passate
  const handleEditCourse = (courseId) => {
    if (onEditCourse) {
      onEditCourse(courseId);
    } else {
      navigate(`/teacher/corsi/${courseId}/edit`);
    }
  };
  const handleViewLessons = (courseId) => {
    if (onViewLessons) {
      onViewLessons(courseId);
    } else {
      // Fallback: espande il corso per mostrare le lezioni
      if (onExpandCourse) {
        onExpandCourse(courseId);
      }
    }
  };

  const handleCreateLesson = (courseId) => {
    if (onCreateLesson) {
      onCreateLesson(courseId);
    } else {
      navigate(`/teacher/corsi/${courseId}/lezioni/nuova`);
    }
  };
  const handleEditLesson = (lesson) => {
    if (onEditLesson) {
      onEditLesson(lesson);
    } else {
      navigate(`/teacher/lezioni/${lesson.id}/edit`);
    }
  };
  const handleCreateExercise = (lesson) => {
    if (onCreateExercise) {
      onCreateExercise(lesson);
    } else {
      navigate(`/teacher/lezioni/${lesson.id}/esercizi/nuovo`);
    }
  };
  const handleEditExercise = (exerciseId) => {
    if (onEditExercise) {
      onEditExercise(exerciseId);
    } else {
      navigate(`/teacher/esercizi/${exerciseId}/edit`);
    }
  };
  const [expandedLessons, setExpandedLessons] = useState({});

  const handleToggleLesson = (lessonId) => {
    setExpandedLessons((prev) => ({
      ...prev,
      [lessonId]: !prev[lessonId]
    }));
  };

  const formatPrice = (price) => {
    if (!price) return '0';
    return parseFloat(price).toFixed(2);
  };

  const getBadgeVariant = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'published':
      case 'active':
        return 'success';
      case 'draft':
        return 'warning';
      case 'archived':
        return 'secondary';
      default:
        return 'primary';
    }
  };

  const getCategoryColor = (category) => {
    const categoryColors = {
      Programmazione: '#007bff',
      Design: '#28a745',
      Marketing: '#dc3545',
      Business: '#ffc107',
      Lingue: '#17a2b8',
      Arte: '#6f42c1',
      Musica: '#fd7e14',
      Salute: '#20c997',
      Sport: '#e83e8c',
      Cucina: '#6c757d'
    };
    return categoryColors[category] || '#6c757d';
  };

  const getCompletionPercentage = (course) => {
    if (!course.lessons || course.lessons.length === 0) return 0;
    const totalLessons = course.lessons.length;
    const completedLessons = course.lessons.filter((lesson) => lesson.exercises && lesson.exercises.length > 0).length;
    return Math.round((completedLessons / totalLessons) * 100);
  };

  if (!courses || courses.length === 0) {
    return (
      <div className="courses-grid-modern">
        <div className="empty-state text-center py-5">
          <div className="mb-4">
            <i className="feather icon-book-open" style={{ fontSize: '4rem', color: '#6c757d' }}></i>
          </div>
          <h4 className="mb-3 text-muted">Nessun corso trovato</h4>
          <p className="text-muted mb-4">Inizia creando il tuo primo corso per condividere le tue conoscenze!</p>
          {showCreateCourse && (
            <Button
              variant="primary"
              size="lg"
              className="px-4 py-2"
              onClick={onCreateCourse}
              style={{
                background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                border: 'none',
                borderRadius: '25px',
                boxShadow: '0 4px 15px rgba(4, 169, 245, 0.3)'
              }}
            >
              <i className="feather icon-plus me-2"></i>
              Crea il tuo primo corso
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="courses-grid-modern">
      {showCreateCourse && (
        <Card className="create-course-card mb-4 border-0 shadow-sm">
          <Card.Body
            className="text-center py-5"
            style={{
              background: 'linear-gradient(135deg, rgba(4, 169, 245, 0.05) 0%, rgba(29, 233, 182, 0.05) 100%)',
              borderRadius: '15px'
            }}
          >
            <div className="mb-4">
              <i
                className="feather icon-plus-circle"
                style={{
                  fontSize: '3rem',
                  color: '#04a9f5',
                  filter: 'drop-shadow(0 4px 8px rgba(4, 169, 245, 0.3))'
                }}
              ></i>
            </div>
            <h5 className="mb-3 fw-bold">Crea Nuovo Corso</h5>
            <p className="text-muted mb-4">Condividi le tue conoscenze creando un corso professionale</p>
            <Button
              variant="success"
              size="lg"
              className="px-4 py-2"
              onClick={onCreateCourse}
              style={{
                background: 'linear-gradient(135deg, #28a745, #20c997)',
                border: 'none',
                borderRadius: '25px',
                boxShadow: '0 4px 15px rgba(40, 167, 69, 0.3)'
              }}
            >
              <i className="feather icon-plus me-2"></i>
              Crea Corso
            </Button>
          </Card.Body>
        </Card>
      )}

      <Row>
        {courses.map((course) => {
          const completionRate = getCompletionPercentage(course);
          const isExpanded = expandedCourse === course.id;

          return (
            <Col lg={6} xl={4} key={course.id} className="mb-4">
              <Card className="course-card h-100 border-0 shadow-sm">
                {/* Course Image/Header */}
                <div className="course-image-container position-relative">
                  {course.image ? (
                    <img src={course.image} alt={course.title} className="course-image" />
                  ) : (
                    <div
                      className="course-placeholder"
                      style={{
                        background: `linear-gradient(135deg, ${getCategoryColor(course.category)} 0%, ${getCategoryColor(course.category)}99 100%)`
                      }}
                    >
                      <i className="feather icon-book-open"></i>
                    </div>
                  )}

                  <div className="position-absolute top-0 start-0 m-3">
                    <Badge
                      className="category-badge px-3 py-2"
                      style={{
                        background: `${getCategoryColor(course.category)}dd`,
                        color: 'white',
                        borderRadius: '15px'
                      }}
                    >
                      {course.category || 'Generale'}
                    </Badge>
                  </div>

                  <div className="position-absolute top-0 end-0 m-3">
                    <Button
                      className="expand-btn"
                      size="sm"
                      onClick={() => onExpandCourse && onExpandCourse(isExpanded ? null : course.id)}
                    >
                      <i className={`feather icon-chevron-${isExpanded ? 'up' : 'down'}`}></i>
                    </Button>
                  </div>
                </div>

                <Card.Body className="course-header">
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div className="flex-grow-1">
                      <h6 className="course-title mb-2">{course.title}</h6>
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <Badge variant={getBadgeVariant(course.status)} className="course-type-badge" style={{ borderRadius: '10px' }}>
                          {course.status || 'Draft'}
                        </Badge>
                        <button
                          type="button"
                          className="btn p-0 text-muted lessons-badge border-0 bg-transparent"
                          onClick={() => handleViewLessons(course.id)}
                          style={{
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            borderRadius: '4px',
                            fontSize: '0.875rem'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = '#f8f9fa';
                            e.target.style.color = '#007bff';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = 'transparent';
                            e.target.style.color = '#6c757d';
                          }}
                          title={`Clicca per vedere le ${course.lessons?.length || 0} lezioni`}
                        >
                          <i className="feather icon-play-circle me-1"></i>
                          {course.lessons?.length || 0} lezioni
                        </button>
                      </div>
                    </div>
                    <div className="text-end">
                      <div className="price-info">
                        <div className="price-tag text-primary fw-bold">€{formatPrice(course.price_eur || course.price)} EUR</div>
                        {course.teocoin_price && (
                          <div className="teocoin-price text-success small">{formatPrice(course.teocoin_price)} TEO</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {course.description && (
                    <p
                      className="course-description mb-3"
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                      }}
                    >
                      {course.description}
                    </p>
                  )}

                  {/* Course Progress */}
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-1">
                      <small className="text-muted fw-semibold">Completamento Corso</small>
                      <small className="text-primary fw-bold">{completionRate}%</small>
                    </div>
                    <ProgressBar
                      now={completionRate}
                      style={{ height: '6px', borderRadius: '3px' }}
                      variant={completionRate > 70 ? 'success' : completionRate > 40 ? 'warning' : 'danger'}
                    />
                  </div>

                  <div className="course-stats mb-3">
                    <Row className="text-center g-2">
                      <Col>
                        <button
                          type="button"
                          className="stat-item p-2 bg-light rounded border-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center"
                          onClick={() => handleViewLessons(course.id)}
                          style={{
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            backgroundColor: '#f8f9fa'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = '#e3f2fd';
                            e.target.style.transform = 'scale(1.02)';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = '#f8f9fa';
                            e.target.style.transform = 'scale(1)';
                          }}
                          title={`Clicca per vedere le ${course.lessons?.length || 0} lezioni`}
                        >
                          <div className="stat-value text-primary fw-bold">{course.lessons?.length || 0}</div>
                          <small className="stat-label text-muted d-block">Lezioni</small>
                        </button>
                      </Col>
                      <Col>
                        <div className="stat-item p-2 bg-light rounded">
                          <div className="stat-value text-success fw-bold">{course.students_count || 0}</div>
                          <small className="stat-label text-muted d-block">Studenti</small>
                        </div>
                      </Col>
                    </Row>
                  </div>

                  {/* Quick Actions */}
                  <div className="course-actions d-flex gap-2">
                    <Button
                      variant="outline-secondary"
                      size="sm"
                      className="flex-fill"
                      onClick={() => handleEditCourse(course.id)}
                      style={{ borderRadius: '12px' }}
                    >
                      <i className="feather icon-edit me-1"></i>
                      Modifica
                    </Button>
                    {onCreateLesson && (
                      <Button variant="success" size="sm" onClick={() => handleCreateLesson(course.id)} title="Crea nuova lezione">
                        <i className="feather icon-plus"></i>
                      </Button>
                    )}
                  </div>
                </Card.Body>

                {/* Expanded Content - Lessons */}
                <Collapse in={isExpanded}>
                  <div className="course-expanded-content">
                    <div className="p-3">
                      <div className="d-flex justify-content-between align-items-center mb-3">
                        <h6 className="mb-0 fw-bold text-dark">
                          <i className="feather icon-list me-2 text-primary"></i>
                          Lezioni del Corso
                        </h6>
                        {onCreateLesson && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleCreateLesson(course.id)}
                            style={{
                              background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                              border: 'none',
                              borderRadius: '15px'
                            }}
                          >
                            <i className="feather icon-plus me-1"></i>
                            Nuova Lezione
                          </Button>
                        )}
                      </div>

                      {course.lessons && course.lessons.length > 0 ? (
                        <div className="lessons-grid">
                          {course.lessons.map((lesson, lessonIndex) => (
                            <Card key={lesson.id} className="lesson-card mb-3 border-0 shadow-sm">
                              <Card.Body className="p-3">
                                <button
                                  type="button"
                                  className="lesson-header cursor-pointer btn-reset"
                                  onClick={() => handleToggleLesson(lesson.id)}
                                  style={{ background: 'none', border: 'none', padding: 0, width: '100%', textAlign: 'left' }}
                                >
                                  <div className="d-flex justify-content-between align-items-center">
                                    <div className="flex-grow-1">
                                      <div className="d-flex align-items-center mb-2">
                                        <Badge
                                          className="me-2 px-2 py-1"
                                          style={{
                                            background: 'linear-gradient(135deg, #28a745, #20c997)',
                                            borderRadius: '10px'
                                          }}
                                        >
                                          #{lessonIndex + 1}
                                        </Badge>
                                        <h6 className="lesson-title mb-0">{lesson.title}</h6>
                                      </div>
                                      <div className="lesson-stats d-flex gap-3">
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
                                          className="px-2 py-1"
                                          style={{ fontSize: '0.7rem', borderRadius: '8px' }}
                                        >
                                          {lesson.lesson_type || 'theory'}
                                        </Badge>
                                      </div>
                                    </div>
                                    <div className="lesson-actions d-flex align-items-center gap-2">
                                      {showActions && (
                                        <>
                                          <Button
                                            variant="outline-primary"
                                            size="sm"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              onViewLesson && onViewLesson(lesson);
                                            }}
                                          >
                                            <i className="feather icon-eye"></i>
                                          </Button>
                                          <Button
                                            variant="outline-secondary"
                                            size="sm"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleEditLesson(lesson);
                                            }}
                                          >
                                            <i className="feather icon-edit"></i>
                                          </Button>
                                        </>
                                      )}
                                      <i className={`feather icon-chevron-${expandedLessons[lesson.id] ? 'up' : 'down'} text-muted`}></i>
                                    </div>
                                  </div>
                                </button>

                                <Collapse in={expandedLessons[lesson.id]}>
                                  <div
                                    className="exercises-section mt-3 p-3 rounded"
                                    style={{
                                      background: 'linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%)',
                                      border: '2px solid rgba(255, 193, 7, 0.2)'
                                    }}
                                  >
                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                      <h6 className="mb-0 fw-bold text-dark">
                                        <i className="feather icon-target me-2 text-warning"></i>
                                        Esercizi della Lezione
                                      </h6>
                                      <Button
                                        variant="warning"
                                        size="sm"
                                        onClick={() =>
                                          handleCreateExercise({
                                            ...lesson,
                                            course_id: course.id,
                                            course: course.id
                                          })
                                        }
                                        style={{ borderRadius: '15px' }}
                                      >
                                        <i className="feather icon-plus me-1"></i>
                                        {lesson.exercises?.length === 0 ? 'Primo Esercizio' : 'Aggiungi'}
                                      </Button>
                                    </div>

                                    {lesson.exercises && lesson.exercises.length > 0 ? (
                                      <div className="exercises-list">
                                        {lesson.exercises.map((exercise, exerciseIndex) => (
                                          <div
                                            key={exercise.id}
                                            className="exercise-item d-flex justify-content-between align-items-center p-2 mb-2 rounded"
                                            style={{ background: 'rgba(255, 255, 255, 0.7)' }}
                                          >
                                            <div className="flex-grow-1">
                                              <div className="d-flex align-items-center mb-1">
                                                <Badge
                                                  className="me-2 px-2 py-1"
                                                  style={{
                                                    background: 'linear-gradient(135deg, #ffc107, #fd7e14)',
                                                    color: '#000',
                                                    borderRadius: '8px'
                                                  }}
                                                >
                                                  Ex.{exerciseIndex + 1}
                                                </Badge>
                                                <h6 className="mb-0" style={{ fontSize: '0.9rem' }}>
                                                  {exercise.title}
                                                </h6>
                                              </div>
                                              <div className="d-flex gap-2">
                                                <Badge variant="secondary" style={{ fontSize: '0.7rem', borderRadius: '8px' }}>
                                                  {exercise.exercise_type || 'practical'}
                                                </Badge>
                                                <Badge variant="info" style={{ fontSize: '0.7rem', borderRadius: '8px' }}>
                                                  {exercise.difficulty || 'beginner'}
                                                </Badge>
                                              </div>
                                            </div>
                                            {showActions && (
                                              <div className="d-flex gap-1">
                                                <Button
                                                  variant="outline-primary"
                                                  size="sm"
                                                  onClick={() => onViewExercise && onViewExercise(exercise.id)}
                                                >
                                                  <i className="feather icon-eye"></i>
                                                </Button>
                                                <Button
                                                  variant="outline-secondary"
                                                  size="sm"
                                                  onClick={() => handleEditExercise(exercise.id)}
                                                >
                                                  <i className="feather icon-edit"></i>
                                                </Button>
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    ) : (
                                      <div className="text-center py-3">
                                        <i className="feather icon-target text-muted mb-2" style={{ fontSize: '2rem' }}></i>
                                        <p className="text-muted mb-3">Nessun esercizio creato</p>
                                        {onCreateExercise && (
                                          <Button
                                            variant="warning"
                                            size="sm"
                                            onClick={() =>
                                              onCreateExercise({
                                                ...lesson,
                                                course_id: course.id,
                                                course: course.id
                                              })
                                            }
                                            style={{ borderRadius: '15px' }}
                                          >
                                            <i className="feather icon-plus me-1"></i>
                                            Crea Primo Esercizio
                                          </Button>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </Collapse>
                              </Card.Body>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-4">
                          <i className="feather icon-book text-muted mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <p className="text-muted mb-3">Nessuna lezione creata per questo corso</p>
                          {onCreateLesson && (
                            <Button
                              variant="primary"
                              onClick={() => onCreateLesson(course.id)}
                              style={{
                                background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                                border: 'none',
                                borderRadius: '15px'
                              }}
                            >
                              <i className="feather icon-plus me-2"></i>
                              Crea Prima Lezione
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Collapse>
              </Card>
            </Col>
          );
        })}
      </Row>
    </div>
  );
};

export default CoursesTable;
