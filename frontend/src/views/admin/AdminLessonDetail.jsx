import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const AdminLessonDetail = () => {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchLesson = async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/lessons/${lessonId}/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setLesson(data);
    };
    fetchLesson();
    setLoading(false);
  }, [lessonId]);

  useEffect(() => {
    if (!lessonId) return;
    const token = localStorage.getItem('token') || localStorage.getItem('access');
    const fetchExercises = async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/lessons/${lessonId}/exercises/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setExercises(Array.isArray(data) ? data : []);
    };
    fetchExercises();
  }, [lessonId]);

  if (loading) return <div>Caricamento...</div>;
  if (!lesson) return <div>Lezione non trovata.</div>;

  return (
    <div className="container mt-4">
      <h2>{lesson.title}</h2>
      <p>Durata: {lesson.duration} min</p>
      {lesson.video_url && (
        <video controls width="100%">
          <source src={lesson.video_url} type="video/mp4" />
          <track kind="captions" srcLang="en" label="English (auto)" />
          Il tuo browser non supporta il video.
        </video>
      )}
      <div className="mt-3">{lesson.content}</div>
      <div className="mt-3">{lesson.materials}</div>
      <Link to="/dashboard/admin" className="btn btn-secondary mt-3">
        Torna alla dashboard admin
      </Link>
      <div className="mt-4">
        <h4>Esercizi della lezione</h4>
        {exercises.length === 0 ? (
          <p>Nessun esercizio disponibile per questa lezione.</p>
        ) : (
          <ul>
            {exercises.map((ex) => (
              <li key={ex.id}>
                <Link to={`/admin/esercizi/${ex.id}`}>
                  <strong>{ex.title}</strong>
                </Link>
                : {ex.description}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default AdminLessonDetail;
