import React, { memo, useMemo, useCallback, useState } from 'react';
import { Button, Spinner, Collapse } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import '../../assets/css/components/CourseCard.css';

// Memoized lesson item component for better performance
const LessonItem = memo(({ lesson, order, teacherMode }) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = useCallback(() => setIsHovered(true), []);
  const handleMouseLeave = useCallback(() => setIsHovered(false), []);

  return (
    <div className="d-flex align-items-center p-2 border-bottom">
      <span className="badge bg-primary me-3 rounded-circle course-card-lesson-number">
        {order}
      </span>
      <div className="flex-grow-1">
        {teacherMode ? (
          <Link 
            to={`/lezioni-docente/${lesson.id}`}
            className={`text-decoration-none fw-medium ${isHovered ? 'text-primary' : 'text-dark'}`}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            {lesson.title}
          </Link>
        ) : (
          <span className="fw-medium text-dark">
            {lesson.title}
          </span>
        )}
        {lesson.duration && (
          <small className="text-muted ms-2">
            ({lesson.duration} min)
          </small>
        )}
      </div>
    </div>
  );
});

LessonItem.displayName = 'LessonItem';

const CourseCard = memo(({
  course,
  expanded,
  onExpand,
  lessons = [],
  loadingLessons = false,
  teacherMode = false,
  showActions = false,
  onEdit,
  onDelete,
  className = ''
}) => {
  // Memoized course stats
  const courseStats = useMemo(() => ({
    progress: course.progress || 0,
    duration: course.duration || 0,
    lessons: course.lessons_count || lessons.length || 0,
    difficulty: course.difficulty || 'Beginner'
  }), [course, lessons.length]);

  // Memoized course image
  const courseImage = useMemo(() => {
    return course.image || course.thumbnail || '/api/placeholder/300/200';
  }, [course.image, course.thumbnail]);

  // Memoized course link
  const courseLink = useMemo(() => {
    if (teacherMode) {
      return `/corsi-docente/${course.id}`;
    }
    return `/course/${course.id}`;
  }, [course.id, teacherMode]);

  // Handle expand toggle
  const handleExpandToggle = useCallback(() => {
    if (onExpand) {
      onExpand(course.id);
    }
  }, [onExpand, course.id]);

  // Handle action buttons
  const handleEdit = useCallback(() => {
    if (onEdit) onEdit(course);
  }, [onEdit, course]);

  const handleDelete = useCallback(() => {
    if (onDelete) onDelete(course);
  }, [onDelete, course]);

  return (
    <div className={`card h-100 shadow-sm ${className}`}>
      {/* Course Image */}
      <div className="position-relative">
        <img 
          src={courseImage} 
          alt={course?.title || 'Corso'}
          loading="lazy"
          className="card-img-top course-card-image"
        />
        <div className="position-absolute top-0 end-0 m-2">
          <span className="badge bg-success d-flex align-items-center">
            <i className="feather icon-trending-up me-1"></i>
            {courseStats.difficulty}
          </span>
        </div>
      </div>

      {/* Course Content */}
      <div className="card-body d-flex flex-column">
        {/* Course Header */}
        <div className="mb-3">
          <h5 className="card-title mb-2">
            <Link to={courseLink} className="text-decoration-none text-primary">
              {course?.title || 'Titolo non disponibile'}
            </Link>
          </h5>
          {course?.teacher_name && (
            <p className="text-muted mb-0 d-flex align-items-center">
              <i className="feather icon-user me-1"></i>
              {course.teacher_name}
            </p>
          )}
        </div>

        {/* Course Description */}
        {course?.description && (
          <p className="card-text text-muted mb-3">
            {course.description.length > 100 
              ? `${course.description.substring(0, 100)}...` 
              : course.description
            }
          </p>
        )}

        {/* Course Stats */}
        <div className="d-flex flex-wrap gap-3 mb-3">
          <small className="text-muted d-flex align-items-center">
            <i className="feather icon-play-circle me-1 text-success"></i>
            {courseStats.lessons} lezioni
          </small>
          {courseStats.duration > 0 && (
            <small className="text-muted d-flex align-items-center">
              <i className="feather icon-clock me-1 text-info"></i>
              {courseStats.duration} min
            </small>
          )}
          {courseStats.progress > 0 && (
            <small className="text-muted d-flex align-items-center">
              <i className="feather icon-trending-up me-1 text-warning"></i>
              {courseStats.progress}% completato
            </small>
          )}
        </div>

        {/* Progress Bar */}
        {courseStats.progress > 0 && (
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-1">
              <small className="text-muted">Progresso</small>
              <small className="text-muted">{courseStats.progress}%</small>
            </div>
            <div className="progress course-card-progress">
              <div 
                className="progress-bar bg-primary"
                style={{ width: `${courseStats.progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Course Actions */}
        <div className="mt-auto">
          <div className="d-flex gap-2 mb-2">
            <Link 
              to={courseLink}
              className="btn btn-primary flex-grow-1"
            >
              <i className="feather icon-play me-1"></i>
              {teacherMode ? 'Gestisci' : 'Accedi al Corso'}
            </Link>

            {/* Lessons Toggle */}
            {courseStats.lessons > 0 && (
              <Button 
                onClick={handleExpandToggle}
                variant="outline-secondary"
                size="sm"
              >
                <i className={`feather icon-${expanded ? 'chevron-up' : 'chevron-down'}`}></i>
              </Button>
            )}
          </div>

          {/* Teacher Actions */}
          {showActions && (
            <div className="d-flex gap-2">
              <Button 
                onClick={handleEdit}
                variant="outline-primary"
                size="sm"
                className="flex-grow-1"
              >
                <i className="feather icon-edit-2 me-1"></i>
                Modifica
              </Button>
              <Button 
                onClick={handleDelete}
                variant="outline-danger"
                size="sm"
                className="flex-grow-1"
              >
                <i className="feather icon-trash-2 me-1"></i>
                Elimina
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Lessons Collapse */}
      <Collapse in={expanded}>
        <div className="card-footer bg-light">
          <div className="mb-2">
            <h6 className="mb-3 d-flex align-items-center">
              <i className="feather icon-list me-2 text-primary"></i>
              Lezioni del Corso
            </h6>
          </div>
          
          {loadingLessons ? (
            <div className="text-center py-3">
              <Spinner size="sm" className="me-2" />
              <span className="text-muted">Caricamento lezioni...</span>
            </div>
          ) : lessons.length > 0 ? (
            <div className="list-group list-group-flush">
              {lessons.map((lesson, index) => (
                <LessonItem
                  key={lesson.id}
                  lesson={lesson}
                  order={index + 1}
                  teacherMode={teacherMode}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-3 text-muted">
              <i className="feather icon-book-open d-block mb-2 course-card-empty-icon"></i>
              <p className="mb-0">Nessuna lezione disponibile</p>
            </div>
          )}
        </div>
      </Collapse>
    </div>
  );
});

CourseCard.displayName = 'CourseCard';

export default CourseCard;