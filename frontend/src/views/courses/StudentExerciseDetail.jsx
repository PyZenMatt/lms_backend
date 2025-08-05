const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const StudentExerciseDetail = () => {
  const { exerciseId } = useParams();
  const [exercise, setExercise] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [solution, setSolution] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchExercise = async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setExercise(data);
      } else {
        setError('Errore nel caricamento esercizio');
      }
    };
    const fetchSubmission = async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/my_submission/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setSubmission(data);
        setStatus(data.status || '');
      } else {
        setSubmission(null);
        setStatus('');
      }
    };
    fetchExercise();
    fetchSubmission();
    setLoading(false);
  }, [exerciseId]);

  // Mostra il form solo se non c'è una sottomissione o se la precedente è respinta
  const canSubmit = !submission || submission.status === 'rejected';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const res = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/submit/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ content: solution })
    });
    if (res.ok) {
      setStatus('in_review');
      setSubmission({ content: solution, status: 'in_review' });
    } else {
      setError('Errore nell\'invio della soluzione');
    }
  };

  if (loading) return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
    </div>
  );
  
  if (error) return (
    <div className="exercise-detail-container">
      <div className="exercise-content">
        <div className="error-message">
          <i className="fas fa-exclamation-triangle"></i>
          {error}
        </div>
      </div>
    </div>
  );
  
  if (!exercise) return (
    <div className="exercise-detail-container">
      <div className="exercise-content">
        <div className="no-exercise">Esercizio non trovato.</div>
      </div>
    </div>
  );

  return (
    <div className="exercise-detail-container">
      <div className="exercise-content">
        {/* Exercise Hero Section */}
        <div className="exercise-hero">
          <h1 className="exercise-title">
            <div className="exercise-icon">
              <i className="fas fa-dumbbell"></i>
            </div>
            {exercise.title}
          </h1>
          <p className="exercise-description">{exercise.description}</p>
        </div>

        {/* Submission Status */}
        {submission && (
          <div className="submission-status">
            <div className="status-header">
              <h2 className="status-title">
                <i className="fas fa-clipboard-check"></i>
                Stato della Sottomissione
              </h2>
              <span className={`status-badge ${submission.status || status}`}>
                <i className={`fas ${
                  (submission.status || status) === 'approved' ? 'fa-check-circle' :
                  (submission.status || status) === 'rejected' ? 'fa-times-circle' :
                  'fa-clock'
                }`}></i>
                {submission.status || status}
              </span>
            </div>
            <div className="submission-content">
              <strong>Soluzione inviata:</strong>
              <div className="submission-text">{submission.content}</div>
            </div>
          </div>
        )}

        {/* Solution Form */}
        {canSubmit && (
          <div className="solution-form">
            <h2 className="form-title">
              <i className="fas fa-code"></i>
              Invia la tua soluzione
            </h2>
            
            {/* Tips Section */}
            <div className="tips-section">
              <h3 className="tips-title">
                <i className="fas fa-lightbulb"></i>
                Consigli per una buona soluzione
              </h3>
              <ul className="tips-list">
                <li>Leggi attentamente la consegna dell'esercizio</li>
                <li>Scrivi codice pulito e ben commentato</li>
                <li>Testa la tua soluzione prima di inviarla</li>
                <li>Non esitare a chiedere aiuto se hai dubbi</li>
              </ul>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="solution" className="form-label">
                  <i className="fas fa-keyboard"></i>
                  La tua soluzione
                </label>
                <textarea
                  id="solution"
                  className="form-textarea"
                  value={solution}
                  onChange={e => setSolution(e.target.value)}
                  placeholder="Scrivi qui la tua soluzione..."
                  required
                />
              </div>
              
              <div className="action-buttons">
                <button type="submit" className="btn-primary">
                  <i className="fas fa-paper-plane"></i>
                  Invia soluzione
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Navigation */}
        <div className="action-buttons">
          <Link 
            to={exercise.lesson ? `/lezioni/${exercise.lesson}` : '/dashboard-studente'} 
            className="btn-secondary"
          >
            <i className="fas fa-arrow-left"></i>
            {exercise.lesson ? 'Torna alla lezione' : 'Torna alla dashboard'}
          </Link>
        </div>
      </div>
    </div>
  );
};

export default StudentExerciseDetail;