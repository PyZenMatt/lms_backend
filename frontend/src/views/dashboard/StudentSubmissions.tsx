/* @ts-nocheck */
import React, { useEffect, useState } from 'react';
import { Card, Spinner, Alert, Badge } from '@/components/ui';
import { useNavigate } from 'react-router-dom';
import { fetchStudentSubmissions } from '../../services/api/dashboard';

// Helper functions per gli stati e colori
const getStatusInfo = (submission) => {
  if (submission.reviewed) {
    const score = submission.average_score ? Math.round(submission.average_score * 10) / 10 : submission.average_score;
    const scoreClass = score >= 8 ? 'success' : score >= 6 ? 'warning' : 'danger';
    const icon = score >= 8 ? 'check-circle' : score >= 6 ? 'border rounded-md p-3 bg-muted text-muted-foreground-circle' : 'x-circle';
    return {
      node: (
        <Badge bg={scoreClass}>
          <i className={`feather icon-${icon} me-1`}></i>Valutato: {score}
        </Badge>
      ),
      icon: icon,
      class: scoreClass
    };
  }
  return {
    node: (
      <Badge bg="info" text="dark">
        <i className="feather icon-clock me-1"></i>In Review
      </Badge>
    ),
    icon: 'clock',
    class: 'info'
  };
};

const getExerciseTypeIcon = (exerciseTitle) => {
  if (exerciseTitle?.toLowerCase().includes('disegno')) return 'edit-3';
  if (exerciseTitle?.toLowerCase().includes('pittura')) return 'image';
  if (exerciseTitle?.toLowerCase().includes('scultura')) return 'box';
  return 'file-text';
};

const StudentSubmissions = () => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmissionClick = (submission) => {
    if (submission.reviewed) {
      navigate(`/submission-graded/${submission.id}`);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await fetchStudentSubmissions();
        setSubmissions(res.data);
      } catch (err) {
        setError('Errore nel caricamento delle sottomissioni');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <>
      {error && <Alert variant="danger">{error}</Alert>}
      {loading ? (
        <div className="text-center py-4">
          <Spinner animation="border" variant="primary" />
          <p className="mt-2 text-muted">Caricamento sottomissioni...</p>
        </div>
      ) : submissions.length === 0 ? (
        <div className="text-center py-5">
          <div className="mb-4">
            <i className="feather icon-file-text" style={{ fontSize: '4rem', color: 'hsl(var(--muted))' }}></i>
          </div>
          <h5 className="text-muted mb-3">Nessuna sottomissione trovata</h5>
          <p className="text-muted">
            Non hai ancora sottomesso alcun esercizio.
            <br />
            Inizia a completare gli esercizi dei tuoi corsi!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-4 g-3">
          {submissions
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map((submission, idx) => {
              const statusInfo = getStatusInfo(submission);
              const exerciseIcon = getExerciseTypeIcon(submission.exercise?.title);
              const submissionDate = new Date(submission.created_at);
              const isClickable = submission.reviewed;

              return (
                <div className="col-span-12" key={submission.id}>
                  <Card
                    className={`submission-bg-card text-card-foreground rounded-lg border border-border shadow-sm h-100 ${isClickable ? 'submission-clickable' : ''}`}
                    onClick={() => handleSubmissionClick(submission)}
                    style={{
                      cursor: isClickable ? 'pointer' : 'default',
                      transition: 'all 0.2s ease',
                      border: isClickable ? '1px solid var(--border)' : '1px solid var(--bg-card text-card-foreground rounded-lg border border-border shadow-sm-border, var(--border))'
                    }}
                  >
                    <Card.Body className="p-3">
                      <div className="grid grid-cols-12 gap-4 align-items-center">
                        {/* Numero e Icona */}
                        <div className="col-span-12" xs="auto">
                          <div className="submission-icon-wrapper d-flex align-items-center justify-content-center">
                            <div className={`submission-number bg-${statusInfo.class} bg-opacity-10 text-${statusInfo.class}`}>
                              #{idx + 1}
                            </div>
                          </div>
                        </div>

                        {/* Info principale */}
                        <div className="col-span-12">
                          <div className="submission-info">
                            <div className="d-flex align-items-center mb-2">
                              <i className={`feather icon-${exerciseIcon} me-2 text-${statusInfo.class}`}></i>
                              <h6 className="mb-0 fw-semibold">{submission.exercise?.title || 'Esercizio Senza Titolo'}</h6>
                            </div>

                            <div className="submission-details text-muted small">
                              <div className="d-flex flex-wrap gap-3">
                                <span>
                                  <i className="feather icon-calendar me-1"></i>
                                  {submissionDate.toLocaleDateString('it-IT', {
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric'
                                  })}
                                </span>
                                <span>
                                  <i className="feather icon-clock me-1"></i>
                                  {submissionDate.toLocaleTimeString('it-IT', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                                {submission.exercise?.course_title && (
                                  <span>
                                    <i className="feather icon-book me-1"></i>
                                    {submission.exercise.course_title}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className="col-span-12" xs="auto">
                          <div className="submission-status">
                            {statusInfo.node}
                            {isClickable && (
                              <div className="mt-2">
                                <small className="text-muted">
                                  <i className="feather icon-eye me-1"></i>
                                  Visualizza dettagli
                                </small>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card.Body>
                  </Card>
                </div>
              );
            })}
        </div>
      )}
    </>
  );
};

export default StudentSubmissions;
