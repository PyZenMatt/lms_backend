
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

// Placeholder minimi per componenti mancanti
const Button: React.FC<{ onClick?: () => void; variant?: string; children: React.ReactNode }> = ({ onClick, variant, children }) => (
  <button type="button" onClick={onClick} style={{ marginRight: 8 }}>{children}</button>
);
const Card: React.FC<{ className?: string; style?: React.CSSProperties; children?: React.ReactNode }> = ({ className, style, children }) => (
  <div className={className} style={style}>{children}</div>
);
const CardContent: React.FC<{ children?: React.ReactNode }> = ({ children }) => <div>{children}</div>;
const H4: React.FC<{ className?: string; children?: React.ReactNode; [key: string]: any }> = ({ className, children, ...props }) => <h4 className={className} {...props}>{children}</h4>;
const Muted: React.FC<{ children?: React.ReactNode }> = ({ children }) => <span style={{ color: 'hsl(var(--muted-foreground))' }}>{children}</span>;

const getUserSafeMessage = (e: any): string => (e && e.message) || 'Errore';
const useLesson = (_cid: number, _id: number) => ({ data: { title: 'Lezione', videoUrl: '', content: '' }, isLoading: false, error: null, refetch: () => {} });
const useLessonActions = (_cid: number, _id: number) => ({ remove: async (_id: number) => {} });

export default function LessonDetailPage() {
  const { courseId, lessonId } = useParams();
  const cid = Number(courseId);
  const id = Number(lessonId);
  const navigate = useNavigate();
  const { data: lesson, isLoading, error, refetch } = useLesson(cid, id);
  const actions = useLessonActions(cid, id);
  const [serverError, setServerError] = useState<string | null>(null);

  const onDelete = async (lessonId: number) => {
    if (window.confirm('Sei sicuro di voler eliminare questa lezione?')) {
      try {
        await actions.remove(lessonId);
        navigate(`/courses/${cid}/lessons`);
      } catch (e) {
        setServerError(getUserSafeMessage(e));
      }
    }
  };

  if (isLoading) {
    return (
      <Card className="placeholder-glow" style={{ minHeight: 200 }}>
        <CardContent>
          <div className="placeholder col-6 mb-2" />
          <div className="placeholder col-10" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <div className="text-center py-5">
        <p className="text-danger mb-3">{getUserSafeMessage(error)}</p>
        <Button onClick={() => refetch()}>Riprova</Button>
      </div>
    );
  }

  if (!lesson) return null;

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <H4 className="mb-0" data-testid="page-title">
          {lesson.title}
        </H4>
        <div className="d-flex gap-2">
          <Button onClick={() => navigate(`/courses/${cid}/lessons`)}>Torna alla lista</Button>
          <Button variant="secondary" onClick={() => navigate(`/courses/${cid}/lessons/${id}?edit=1`)}>
            Modifica
          </Button>
          <Button variant="danger" onClick={() => onDelete(id)}>
            Elimina
          </Button>
        </div>
      </div>

      {lesson.videoUrl && (
        <div className="mb-3">
          <video controls style={{ maxWidth: '100%' }} src={lesson.videoUrl}>
            <track kind="captions" srcLang="en" label="English (auto)" />
          </video>
        </div>
      )}

      {lesson.content ? (
        <Card>
          <CardContent>
            <div dangerouslySetInnerHTML={{ __html: lesson.content }} />
          </CardContent>
        </Card>
      ) : (
        <Muted>Nessun contenuto</Muted>
      )}

      {serverError && <p className="text-danger mt-3">{serverError}</p>}
    </div>
  );
}
