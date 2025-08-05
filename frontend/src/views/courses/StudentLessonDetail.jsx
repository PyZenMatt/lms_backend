import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchUserRole } from '../../services/api/auth';
import api from '../../services/core/axiosClient';

const StudentLessonDetail = () => {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const fetchLesson = async () => {
      try {
        const response = await api.get(`/lessons/${lessonId}/`);
        const data = response.data;
        setLesson(data);
        setCompleted(data.completed || false);
      } catch (error) {
        console.error('Error fetching lesson:', error);
      }
    };
    fetchLesson();
    setLoading(false);
  }, [lessonId]);

  useEffect(() => {
    if (!lessonId) return;
    const fetchExercises = async () => {
      try {
        const response = await api.get(`/lessons/${lessonId}/exercises/`);
        const data = response.data;
        setExercises(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching exercises:', error);
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
    if (completed) return; // Prevent double-click
    
    try {
      setLoading(true);
      await api.post(`/lessons/${lessonId}/mark_complete/`, {});
      
      // After POST, reload the lesson to update all state
      const response = await api.get(`/lessons/${lessonId}/`);
      const lessonData = response.data;
      setLesson(lessonData);
      setCompleted(lessonData.completed || false);
      
      // Show success feedback
      setTimeout(() => {
        setLoading(false);
      }, 500);
      
    } catch (error) {
      console.error('Error marking lesson complete:', error);
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
    </div>
  );
  
  if (!lesson) return (
    <div className="lesson-detail-container">
      <div className="lesson-content">
        <div className="no-lesson">Lezione non trovata.</div>
      </div>
    </div>
  );

  return (
    <div className="lesson-detail-container">
      <div className="lesson-content">
        {/* Hero Section */}
        <div className="lesson-hero">
          <div className="container">
            <h1 className="lesson-title">{lesson.title}</h1>
            <div className="lesson-meta">
              <div className="lesson-duration">
                <i className="fas fa-clock"></i>
                {lesson.duration} min
              </div>
              <div className={`lesson-status ${completed ? 'completed' : ''}`}>
                <i className={`fas ${completed ? 'fa-check-circle' : 'fa-circle'}`}></i>
                {completed ? 'Completata' : 'In corso'}
              </div>
            </div>
          </div>
        </div>

        {/* Video Section */}
        {lesson.video_url && (
          <div className="video-section">
            <h2 className="section-title">
              <i className="fas fa-play-circle"></i>
              Video della lezione
            </h2>
            <div className="video-container">
              <video controls className="lesson-video">
                <source src={lesson.video_url} type="video/mp4" />
                Il tuo browser non supporta il video.
              </video>
            </div>
          </div>
        )}

        {/* Content Section */}
        {lesson.content && (
          <div className="content-section">
            <h2 className="section-title">
              <i className="fas fa-book-open"></i>
              Contenuto della lezione
            </h2>
            <div className="section-content">
              {lesson.content}
            </div>
          </div>
        )}

        {/* Materials Section */}
        {lesson.materials && (
          <div className="content-section">
            <h2 className="section-title">
              <i className="fas fa-tools"></i>
              Materiali
            </h2>
            <div className="section-content">
              {lesson.materials}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="action-buttons">
          {userRole !== 'admin' && (
            <button
              className="btn-primary"
              onClick={handleComplete}
              disabled={completed || loading}
            >
              <i className={`fas ${completed ? 'fa-check' : loading ? 'fa-spinner fa-spin' : 'fa-check-circle'}`}></i>
              {loading ? 'Completamento...' : completed ? 'Lezione completata' : 'Segna come completata'}
            </button>
          )}
          <Link 
            to={lesson?.course_id ? `/corsi/${lesson.course_id}` : (userRole === 'admin' ? "/dashboard/admin" : "/dashboard-studente")} 
            className="btn-secondary"
          >
            <i className="fas fa-arrow-left"></i>
            {lesson?.course_id ? 'Torna al corso' : (userRole === 'admin' ? 'Torna alla dashboard admin' : 'Torna ai miei corsi')}
          </Link>
        </div>

        {/* Exercises Section - visible only if lesson is completed */}
        {completed && (
          <div className="exercises-section">
            <h2 className="section-title">
              <i className="fas fa-dumbbell"></i>
              Esercizi della lezione
            </h2>
            {exercises.length === 0 ? (
              <p className="no-exercises">Nessun esercizio disponibile per questa lezione.</p>
            ) : (
              <div className="exercises-grid">
                {exercises.map(ex => (
                  <div key={ex.id} className="exercise-card">
                    <h3 className="exercise-title">{ex.title}</h3>
                    <p className="exercise-description">{ex.description}</p>
                    <Link to={`/esercizi/${ex.id}`} className="exercise-link">
                      <i className="fas fa-arrow-right"></i>
                      Vai all'esercizio
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentLessonDetail;