import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
// Import reali (se esistono) al posto dei placeholder:
// import LessonList from '@/features/lessons/components/LessonList';
// import LessonForm from '@/features/lessons/components/LessonForm';
// import Modal from '@/components/ui/Modal';

// Placeholder per funzioni mancanti (sostituisci con le reali se le hai)
const getUserSafeMessage = (e) => (e && e.message) || 'Errore';
const useLessons = () => ({ items: [], isLoading: false, error: null, refetch: () => {} });
const useLessonActions = () => ({ remove: async (_id) => {}, create: async (_data) => {} });

// Placeholder components per evitare errori di compilazione (rimuovi quando hai i reali)
const LessonList = ({ items, loading, error, onRetry, onCreate, onEdit, onDelete }) => (
  <div>
    <p>Placeholder LessonList</p>
    {/* TODO: renderizza items */}
  </div>
);
const LessonForm = ({ onSubmit }) => (
  <form
    onSubmit={(e) => {
      e.preventDefault();
      if (onSubmit) onSubmit({});
    }}
  >
    <p>Placeholder LessonForm</p>
    <button type="submit">Invia</button>
  </form>
);
const Modal = ({ open, onClose, children }) =>
  open ? (
    <div className="modal">
      <button type="button" onClick={onClose}>
        Chiudi
      </button>
      {children}
    </div>
  ) : null;

export default function LessonsListPage() {
  const { courseId } = useParams();
  const cid = Number(courseId ?? NaN);
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [serverError, setServerError] = useState(null);

  const query = useLessons();
  const actions = useLessonActions();

  const onCreate = () => setIsOpen(true);
  const onEdit = (lesson) => navigate(`/courses/${cid}/lessons/${lesson.id}`);

  const onDelete = async (lesson) => {
    if (!window.confirm(`Eliminare la lezione "${lesson.title}"?`)) return;
    try {
      await actions.remove(lesson.id);
      // opzionale: query.refetch();
    } catch (e) {
      setServerError(getUserSafeMessage(e));
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="mb-0" data-testid="page-title">
          Lezioni
        </h3>
        <button type="button" onClick={onCreate}>
          Nuova lezione
        </button>
      </div>

      <LessonList
        items={query.items}
        loading={query.isLoading}
        error={query.error}
        onRetry={() => query.refetch()}
        onCreate={onCreate}
        onEdit={onEdit}
        onDelete={onDelete}
      />

      <Modal open={isOpen} onClose={() => setIsOpen(false)}>
        <h5 className="mb-3">Nuova lezione</h5>
        <LessonForm
          onSubmit={async (data) => {
            setServerError(null);
            try {
              await actions.create(data);
              setIsOpen(false);
              // opzionale: query.refetch();
            } catch (e) {
              setServerError(getUserSafeMessage(e));
            }
          }}
        />
        {serverError && <p className="text-danger mt-2">{serverError}</p>}
      </Modal>
    </div>
  );
}
