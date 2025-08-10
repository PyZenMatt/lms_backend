import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { H4, Muted } from '@/components/ui/Typography';
import { getUserSafeMessage } from '@/lib/http/errors';
import { useLesson, useLessonActions } from '../hooks/useLessons';

export default function LessonDetailPage() {
  const { courseId, lessonId } = useParams();
  const cid = Number(courseId);
  const id = Number(lessonId);
  const navigate = useNavigate();
  const { data: lesson, isLoading, error, refetch } = useLesson(cid, id);
  const actions = useLessonActions(cid, id);
  const [serverError, setServerError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card className="placeholder-glow" style={{ minHeight: 200 }}>
        <Card.Content>
          <div className="placeholder col-6 mb-2" />
          <div className="placeholder col-10" />
        </Card.Content>
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
        <H4 className="mb-0">{lesson.title}</H4>
        <div className="d-flex gap-2">
          <Button onClick={() => navigate(`/courses/${cid}/lessons`)}>Torna alla lista</Button>
          <Button variant="secondary" onClick={() => navigate(`/courses/${cid}/lessons/${id}?edit=1`)}>
            Modifica
          </Button>
          <Button
            variant="danger"
            onClick={async () => {
              if (!window.confirm('Eliminare questa lezione?')) return;
              try {
                await actions.remove(id);
                navigate(`/courses/${cid}/lessons`);
              } catch (e: any) {
                setServerError(getUserSafeMessage(e));
              }
            }}
          >
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
          <Card.Content>
            <div dangerouslySetInnerHTML={{ __html: lesson.content }} />
          </Card.Content>
        </Card>
      ) : (
        <Muted>Nessun contenuto</Muted>
      )}

      {serverError && <p className="text-danger mt-3">{serverError}</p>}
    </div>
  );
}
