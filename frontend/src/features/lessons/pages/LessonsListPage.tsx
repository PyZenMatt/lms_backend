
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

// Tipi minimi per le lezioni
type Lesson = { id: number; title: string };

// Placeholder per funzioni mancanti (sostituisci con le reali se le hai)
const getUserSafeMessage = (e: any): string => (e && e.message) || 'Errore';
const useLessons = (): { items: Lesson[]; isLoading: boolean; error: any; refetch: () => void } => ({ items: [], isLoading: false, error: null, refetch: () => {} });
const useLessonActions = (): { remove: (id: number) => Promise<void>; create: (data: any) => Promise<void> } => ({ remove: async (_id: number) => {}, create: async (_data: any) => {} });

// Placeholder components per evitare errori di compilazione (rimuovi quando hai i reali)
const LessonList: React.FC<{
  items: Lesson[];
  loading: boolean;
  error: any;
  onRetry: () => void;
  onCreate: () => void;
  onEdit: (lesson: Lesson) => void;
  onDelete: (lesson: Lesson) => void;
}> = ({ items, loading, error, onRetry, onCreate, onEdit, onDelete }) => (
  <div>
    <p>Placeholder LessonList</p>
    {/* TODO: renderizza items */}
  </div>
);

const LessonForm: React.FC<{ onSubmit: (data: any) => void }> = ({ onSubmit }) => (
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

// Legacy Modal placeholder removed (Bootstrap class removed)
const Modal: React.FC<{ open: boolean; onClose: () => void; children: React.ReactNode }> = ({ open, onClose, children }) =>
  open ? (
    <div className="fixed inset-0 flex items-center justify-center bg-background/80">
      <div className="bg-card text-card-foreground rounded-lg border border-border shadow-sm p-4">
        <button type="button" onClick={onClose} className="text-sm mb-2">Chiudi</button>
        {children}
      </div>
    </div>
  ) : null;


export default function LessonsListPage() {
  const { courseId } = useParams();
  const cid = Number(courseId ?? NaN);
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const query = useLessons();
  const actions = useLessonActions();

  const onCreate = () => setIsOpen(true);
  const onEdit = (lesson: Lesson) => navigate(`/courses/${cid}/lessons/${lesson.id}`);

  const onDelete = async (lesson: Lesson) => {
    if (!window.confirm(`Eliminare la lezione \"${lesson.title}\"?`)) return;
    try {
      await actions.remove(lesson.id);
      // opzionale: query.refetch();
    } catch (e) {
      setServerError(getUserSafeMessage(e));
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="m-0" data-testid="page-title">
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

      {isOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-card text-card-foreground rounded-lg border border-border shadow-sm p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h5 className="text-lg font-semibold">Nuova lezione</h5>
              <button type="button" onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>
            <LessonForm
              onSubmit={async (data) => {
                setServerError(null);
                try {
                  await actions.create(data);
                  setIsOpen(false);
                } catch (e) {
                  setServerError(getUserSafeMessage(e));
                }
              }}
            />
            {serverError && <p className="text-destructive mt-2 text-sm">{serverError}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
