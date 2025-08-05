import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Spinner, Alert } from 'react-bootstrap';
import ExerciseCreateModal from '../../components/modals/ExerciseCreateModal';
import { fetchExercisesForLesson, fetchLessonDetail } from '../../services/api/courses';

const TeacherLessonDetail = () => {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showExerciseModal, setShowExerciseModal] = useState(false);

  useEffect(() => {
    const loadLessonData = async () => {
      try {
        const lessonData = await fetchLessonDetail(lessonId);
        setLesson(lessonData);
      } catch (err) {
        setError('Errore nel caricamento della lezione');
      } finally {
        setLoading(false);
      }
    };
    loadLessonData();
  }, [lessonId]);

  const loadExercises = async () => {
    try {
      const res = await fetchExercisesForLesson(lessonId);
      setExercises(res.data);
    } catch {
      setExercises([]);
    }
  };

  useEffect(() => {
    loadExercises();
    // eslint-disable-next-line
  }, [lessonId]);

  const handleExerciseCreated = () => {
    setShowExerciseModal(false);
    loadExercises();
  };

  if (loading) return <Spinner animation="border" className="m-5" />;
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (!lesson) return <Alert variant="warning">Lezione non trovata.</Alert>;

  return (
    <div className="container mt-4">
      <h2>{lesson.title}</h2>
      <p>Durata: {lesson.duration} min</p>
      <div className="mt-3">{lesson.content}</div>
      <Button className="mt-3" variant="success" onClick={() => setShowExerciseModal(true)}>
        + Crea nuovo esercizio
      </Button>
      <ExerciseCreateModal
        show={showExerciseModal}
        onHide={() => setShowExerciseModal(false)}
        onCreated={handleExerciseCreated}
        lessonId={lessonId}
        courseId={lesson && (lesson.course_id || lesson.course)}
      />
      <div className="mt-4">
        <h4>Esercizi della lezione</h4>
        {exercises.length === 0 ? (
          <p>Nessun esercizio disponibile per questa lezione.</p>
        ) : (
          <ul>
            {exercises.map(ex => (
              <li key={ex.id}>
                <strong>{ex.title}</strong>: {ex.description}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default TeacherLessonDetail;
