const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchUserRole } from '../../services/api/auth';

const StudentCourseDetail = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const fetchCourse = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const res = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setCourse(data);
    };
    const fetchLessons = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const res = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}/lessons/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setLessons(Array.isArray(data) ? data : []);
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
      <div className="student-course-detail">
        <div className="loading-container">
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }
  
  if (!course) {
    return (
      <div className="student-course-detail">
        <div className="error-container">
          <h3>Corso non trovato</h3>
          <p>Il corso che stai cercando non esiste o non è più disponibile.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="student-course-detail">
      {/* Floating Decorative Elements */}
      <div className="floating-decoration deco-1"></div>
      <div className="floating-decoration deco-2"></div>
      <div className="floating-decoration deco-3"></div>

      {/* Course Hero Section */}
      <div className="course-hero">
        <div className="container">
          <div className="course-header-info">
            <div className="course-cover">
              {course.cover ? (
                <img 
                  src={course.cover.startsWith('http') ? course.cover : `http://127.0.0.1:8000${course.cover}`} 
                  alt={course.title} 
                  style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '16px'}}
                />
              ) : (
                <i className="feather icon-book-open"></i>
              )}
            </div>
            <h1 className="course-title">{course.title}</h1>
            <p className="course-description">{course.description}</p>
            <div className="course-teacher">
              <i className="feather icon-user"></i>
              <strong>Docente:</strong> {course.teacher?.username || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Course Stats */}
      <div className="container">
        <div className="course-stats">
          <div className="course-stat-card">
            <div className="stat-icon">
              <i className="feather icon-play-circle"></i>
            </div>
            <div className="stat-value">{lessons.length}</div>
            <div className="stat-label">Lezioni</div>
          </div>
          
          <div className="course-stat-card">
            <div className="stat-icon">
              <i className="feather icon-clock"></i>
            </div>
            <div className="stat-value">
              {lessons.reduce((total, lesson) => total + (lesson.duration || 0), 0)}
            </div>
            <div className="stat-label">Minuti Totali</div>
          </div>
          
          <div className="course-stat-card">
            <div className="stat-icon">
              <i className="feather icon-award"></i>
            </div>
            <div className="stat-value">
              {course.difficulty || 'Intermedio'}
            </div>
            <div className="stat-label">Livello</div>
          </div>
          
          <div className="course-stat-card">
            <div className="stat-icon">
              <i className="feather icon-users"></i>
            </div>
            <div className="stat-value">
              {course.enrolled_students_count || 0}
            </div>
            <div className="stat-label">Studenti</div>
          </div>
        </div>

        {/* Lessons Content */}
        <div className="course-content">
          <div className="lessons-section">
            <h3 className="lessons-title">
              <i className="feather icon-list"></i>
              Lezioni del Corso
            </h3>
            
            {lessons.length === 0 ? (
              <div className="text-center p-5 bg-light border border-2 border-secondary border-opacity-25 rounded" style={{ borderStyle: 'dashed' }}>
                <i className="feather icon-book text-primary mb-3" style={{ fontSize: '4rem', display: 'block' }}></i>
                <h4 className="text-dark mb-3">Nessuna lezione disponibile</h4>
                <p className="text-muted">Le lezioni per questo corso non sono ancora state pubblicate.</p>
              </div>
            ) : (
              <div className="lessons-grid">
                {lessons.map((lesson, index) => (
                  <Link 
                    key={lesson.id} 
                    to={`/lezioni/${lesson.id}`} 
                    className="lesson-card"
                  >
                    <div className="lesson-number">
                      {lesson.order || index + 1}
                    </div>
                    <h4 className="lesson-title">{lesson.title}</h4>
                    <div className="lesson-meta">
                      {lesson.duration && (
                        <span>
                          <i className="feather icon-clock"></i>
                          {lesson.duration} min
                        </span>
                      )}
                      {lesson.type && (
                        <span>
                          <i className="feather icon-video"></i>
                          {lesson.type}
                        </span>
                      )}
                    </div>
                    <div className="lesson-progress">
                      <div 
                        className="lesson-progress-bar" 
                        style={{width: `${Math.random() * 100}%`}}
                      ></div>
                    </div>
                    <span className={`lesson-status ${Math.random() > 0.7 ? 'completed' : Math.random() > 0.4 ? 'in-progress' : 'not-started'}`}>
                      {Math.random() > 0.7 ? 'Completata' : Math.random() > 0.4 ? 'In Corso' : 'Da Iniziare'}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="navigation-section">
            <Link 
              to={userRole === 'admin' ? "/dashboard/admin" : "/dashboard-studente"} 
              className="btn-back"
            >
              <i className="feather icon-arrow-left"></i>
              {userRole === 'admin' ? 'Torna alla dashboard admin' : 'Torna ai miei corsi'}
            </Link>
          </div>
        </div>
      </div>

      {completed && (
        <div className="container">
          <div className="lessons-section">
            <h4 className="lessons-title">
              <i className="feather icon-target"></i>
              Esercizi della lezione
            </h4>
            {exercises.length === 0 ? (
              <div className="text-center p-5 bg-light border border-2 border-secondary border-opacity-25 rounded" style={{ borderStyle: 'dashed' }}>
                <p className="text-muted">Nessun esercizio disponibile per questa lezione.</p>
              </div>
            ) : (
              <div className="lessons-grid">
                {exercises.map(ex => (
                  <div key={ex.id} className="lesson-card">
                    <h4 className="lesson-title">{ex.title}</h4>
                    <p className="text-muted mb-3">{ex.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentCourseDetail;