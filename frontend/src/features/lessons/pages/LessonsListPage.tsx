import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getUserSafeMessage } from '@/lib/http/errors';
import LessonList from '../components/LessonList';
import LessonForm from '../components/LessonForm';
import Modal from '@/components/ui/Modal';
import { useLessons, useLessonActions } from '../hooks/useLessons';

export default function LessonsListPage() {
  const { courseId } = useParams();
  const cid = Number(courseId);
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const query = useLessons(cid);
  const actions = useLessonActions(cid);

  const onCreate = () => setIsOpen(true);

  const onEdit = (lesson: any) => navigate(`/courses/${cid}/lessons/${lesson.id}`);

  const onDelete = async (lesson: any) => {
  if (!window.confirm(`Eliminare la lezione "${lesson.title}"?`)) return;
    try {
      await actions.remove(lesson.id);
    } catch (e: any) {
      setServerError(getUserSafeMessage(e));
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="mb-0">Lezioni</h3>
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
              await actions.create(data as any);
              setIsOpen(false);
            } catch (e: any) {
              setServerError(getUserSafeMessage(e));
            }
          }}
        />
        {serverError && <p className="text-danger mt-2">{serverError}</p>}
      </Modal>
    </div>
  );
}
