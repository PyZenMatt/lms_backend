import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';

const AdminExerciseDetail = () => {
  const { exerciseId } = useParams();
  const [exercise, setExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchExercise = async () => {
      const res = await fetch(`/api/v1/exercises/${exerciseId}/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setExercise(data);
      } else {
        setError('Errore nel caricamento esercizio');
      }
      setLoading(false);
    };
    fetchExercise();
  }, [exerciseId]);

  if (loading) return (
    <div className="admin-loading-container">
      <div className="admin-loading-spinner"></div>
    </div>
  );
  
  if (error) return (
    <div className="admin-exercise-container">
      <div className="admin-exercise-content">
        <div className="admin-error-message">
          <i className="fas fa-exclamation-triangle"></i>
          {error}
        </div>
      </div>
    </div>
  );
  
  if (!exercise) return (
    <div className="admin-exercise-container">
      <div className="admin-exercise-content">
        <div className="admin-no-exercise">Esercizio non trovato.</div>
      </div>
    </div>
  );

  return (
    <div className="admin-exercise-container">
      <div className="admin-exercise-content">
        {/* Admin Badge */}
        <div className="admin-badge">
          <i className="fas fa-crown"></i>
          Visualizzazione Amministratore
        </div>

        {/* Exercise Hero Section */}
        <div className="admin-exercise-hero">
          <h1 className="admin-exercise-title">
            <div className="admin-exercise-icon">
              <i className="fas fa-dumbbell"></i>
            </div>
            {exercise.title}
          </h1>
          <p className="admin-exercise-description">{exercise.description}</p>
        </div>

        {/* Exercise Details */}
        <div className="admin-info-section">
          <h2 className="admin-info-title">
            <i className="fas fa-info-circle"></i>
            Dettagli Esercizio
          </h2>
          <div className="admin-info-content">
            <p><strong>Titolo:</strong> {exercise.title}</p>
            <p><strong>Descrizione:</strong> {exercise.description}</p>
            {exercise.difficulty && <p><strong>Difficoltà:</strong> {exercise.difficulty}</p>}
            {exercise.timeEstimate && <p><strong>Tempo stimato:</strong> {exercise.timeEstimate} minuti</p>}
            {exercise.materials && <p><strong>Materiali:</strong> {exercise.materials}</p>}
            {exercise.instructions && <p><strong>Istruzioni:</strong> {exercise.instructions}</p>}
          </div>
        </div>

        {/* Navigation */}
        <div className="admin-action-buttons">
          <Link to="/dashboard/admin" className="btn-admin-secondary">
            <i className="fas fa-arrow-left"></i>
            Torna alla dashboard admin
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminExerciseDetail;
