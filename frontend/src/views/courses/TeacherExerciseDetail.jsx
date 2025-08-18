import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge } from '@/components/ui/legacy-shims';
import { fetchExerciseDetail } from '../../services/api/courses';
import MainCard from '../../components/Card/MainCard';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const TeacherExerciseDetail = () => {
  const { exerciseId } = useParams();
  const navigate = useNavigate();
  const [exercise, setExercise] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadExerciseData = async () => {
      try {
        setLoading(true);
        setError('');

        // Fetch exercise details
        const exerciseData = await fetchExerciseDetail(exerciseId);
        setExercise(exerciseData);

        // Fetch submissions for this exercise
        const token = localStorage.getItem('token') || localStorage.getItem('access');
        const submissionsRes = await fetch(`${API_BASE_URL}/api/v1/exercises/${exerciseId}/submissions/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });

        if (submissionsRes.ok) {
          const submissionsData = await submissionsRes.json();
          setSubmissions(Array.isArray(submissionsData) ? submissionsData : []);
        }
      } catch (err) {
        console.error('Error loading exercise data:', err);
        setError("Errore nel caricamento dell'esercizio");
      } finally {
        setLoading(false);
      }
    };

    if (exerciseId) {
      loadExerciseData();
    }
  }, [exerciseId]);

  const handleBackToDashboard = () => {
    navigate('/dashboard/teacher');
  };

  const handleEditExercise = () => {
    navigate(`/teacher/esercizi/${exerciseId}/edit`);
  };

  const handleViewSubmission = (submissionId) => {
    navigate(`/teacher/submissions/${submissionId}`);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'submitted':
        return <Badge bg="warning">In Revisione</Badge>;
      case 'graded':
        return <Badge bg="success">Valutato</Badge>;
      case 'revision_requested':
        return <Badge bg="info">Revisione Richiesta</Badge>;
      default:
        return <Badge bg="secondary">Sconosciuto</Badge>;
    }
  };

  const getDifficultyBadge = (difficulty) => {
    switch (difficulty) {
      case 'beginner':
        return <Badge bg="success">Principiante</Badge>;
      case 'intermediate':
        return <Badge bg="warning">Intermedio</Badge>;
      case 'advanced':
        return <Badge bg="danger">Avanzato</Badge>;
      default:
        return <Badge bg="secondary">Non specificato</Badge>;
    }
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
          <Spinner animation="border" variant="primary" />
          <span className="ms-3">Caricamento esercizio...</span>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">
          <Alert.Heading>Errore</Alert.Heading>
          <p>{error}</p>
          <Button variant="outline-danger" onClick={handleBackToDashboard}>
            Torna alla Dashboard
          </Button>
        </Alert>
      </Container>
    );
  }

  if (!exercise) {
    return (
      <Container className="mt-4">
        <Alert variant="warning">
          <Alert.Heading>Esercizio non trovato</Alert.Heading>
          <p>L'esercizio richiesto non è stato trovato.</p>
          <Button variant="outline-warning" onClick={handleBackToDashboard}>
            Torna alla Dashboard
          </Button>
        </Alert>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <Button variant="outline-secondary" onClick={handleBackToDashboard} className="mb-2">
            <i className="feather icon-arrow-left me-2"></i>
            Torna alla Dashboard
          </Button>
          <h2 className="mb-0">{exercise.title}</h2>
          <p className="text-muted">Gestione esercizio - Vista Teacher</p>
        </div>
        <div>
          <Button variant="primary" onClick={handleEditExercise}>
            <i className="feather icon-edit me-2"></i>
            Modifica Esercizio
          </Button>
        </div>
      </div>

      <Row>
        {/* Exercise Information */}
        <Col lg={8}>
          <MainCard title="Dettagli Esercizio">
            <div className="exercise-info">
              <div className="mb-3">
                <h5>Descrizione</h5>
                <p>{exercise.description || 'Nessuna descrizione disponibile'}</p>
              </div>

              <div className="mb-3">
                <h5>Istruzioni</h5>
                <p>{exercise.instructions || 'Nessuna istruzione specificata'}</p>
              </div>

              {exercise.materials && (
                <div className="mb-3">
                  <h5>Materiali Necessari</h5>
                  <p>{exercise.materials}</p>
                </div>
              )}

              {exercise.reference_image && (
                <div className="mb-3">
                  <h5>Immagine di Riferimento</h5>
                  <img
                    src={exercise.reference_image}
                    alt="Riferimento esercizio"
                    className="img-fluid rounded"
                    style={{ maxHeight: '300px' }}
                  />
                </div>
              )}
            </div>
          </MainCard>
        </Col>

        {/* Exercise Details & Statistics */}
        <Col lg={4}>
          <MainCard title="Informazioni">
            <div className="exercise-details">
              <div className="mb-3">
                <strong>Tipo:</strong>
                <Badge bg="info" className="ms-2">
                  {exercise.exercise_type === 'practical'
                    ? 'Pratico'
                    : exercise.exercise_type === 'theory'
                      ? 'Teorico'
                      : exercise.exercise_type || 'Non specificato'}
                </Badge>
              </div>

              <div className="mb-3">
                <strong>Difficoltà:</strong>
                <div className="mt-1">{getDifficultyBadge(exercise.difficulty)}</div>
              </div>

              {exercise.time_estimate && (
                <div className="mb-3">
                  <strong>Tempo Stimato:</strong>
                  <p className="mb-0">{exercise.time_estimate} minuti</p>
                </div>
              )}

              <div className="mb-3">
                <strong>Creato il:</strong>
                <p className="mb-0">{new Date(exercise.created_at).toLocaleDateString('it-IT')}</p>
              </div>
            </div>
          </MainCard>

          <MainCard title="Statistiche" className="mt-3">
            <div className="stats-info">
              <div className="stat-item mb-3">
                <div className="d-flex justify-content-between">
                  <span>Consegne totali:</span>
                  <Badge bg="primary">{submissions.length}</Badge>
                </div>
              </div>
              <div className="stat-item mb-3">
                <div className="d-flex justify-content-between">
                  <span>Da valutare:</span>
                  <Badge bg="warning">{submissions.filter((s) => s.status === 'submitted').length}</Badge>
                </div>
              </div>
              <div className="stat-item mb-3">
                <div className="d-flex justify-content-between">
                  <span>Valutate:</span>
                  <Badge bg="success">{submissions.filter((s) => s.status === 'graded').length}</Badge>
                </div>
              </div>
            </div>
          </MainCard>
        </Col>
      </Row>

      {/* Submissions List */}
      <Row className="mt-4">
        <Col lg={12}>
          <MainCard title={`Consegne Studenti (${submissions.length})`}>
            {submissions.length === 0 ? (
              <div className="text-center py-4">
                <i className="feather icon-inbox" style={{ fontSize: '3rem', color: 'var(--muted-foreground)', marginBottom: '1rem' }}></i>
                <h4 className="mb-3">Nessuna consegna</h4>
                <p className="text-muted">Nessuno studente ha ancora consegnato questo esercizio</p>
              </div>
            ) : (
              <div className="submissions-list">
                {submissions.map((submission) => (
                  <Card key={submission.id} className="mb-3">
                    <Card.Body>
                      <div className="d-flex align-items-center justify-content-between">
                        <div className="d-flex align-items-center">
                          <div className="me-3">
                            <i className="feather icon-user-check text-primary" style={{ fontSize: '1.5rem' }}></i>
                          </div>
                          <div>
                            <h6 className="mb-1">{submission.student_name || `Studente ${submission.student}`}</h6>
                            <p className="text-muted small mb-0">
                              Consegnato il: {new Date(submission.submitted_at).toLocaleDateString('it-IT')}
                            </p>
                            {submission.grade && (
                              <p className="text-muted small mb-0">
                                Voto: <strong>{submission.grade}/10</strong>
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="d-flex align-items-center">
                          <div className="me-3">{getStatusBadge(submission.status)}</div>
                          <Button variant="outline-primary" size="sm" onClick={() => handleViewSubmission(submission.id)}>
                            <i className="feather icon-eye me-1"></i>
                            Visualizza
                          </Button>
                        </div>
                      </div>
                    </Card.Body>
                  </Card>
                ))}
              </div>
            )}
          </MainCard>
        </Col>
      </Row>
    </Container>
  );
};

export default TeacherExerciseDetail;
