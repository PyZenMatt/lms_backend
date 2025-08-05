import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Form, Alert, Spinner, Card, Row, Col, Badge } from 'react-bootstrap';
import { createLesson } from '../../services/api/courses';
import CustomToast from '../ui/Toast';
import '../../assets/css/components/LessonCreateModal.css';

import ErrorDisplay from '../ui/ErrorDisplay';
import { validateLessonForm, debounce } from '../../utils/formValidation';

const LessonCreateModal = ({ show, onHide, onCreated, courseId }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [duration, setDuration] = useState('');
  const [lessonType, setLessonType] = useState('theory');
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [showToast, setShowToast] = useState(false);
  const [toastConfig, setToastConfig] = useState({ variant: 'success', title: '', message: '' });
  const fileInputRef = useRef(null);

  // Real-time validation with debouncing
  const validateForm = debounce(() => {
    const formData = { 
      title, 
      content, 
      duration, 
      lessonType,
      videoFile: lessonType === 'video' ? videoFile : true 
    };
    const validation = validateLessonForm(formData);
    setValidationErrors(validation.errors);
  }, 300);

  // Trigger validation when form data changes
  useEffect(() => {
    validateForm();
  }, [title, content, duration, lessonType, videoFile]);

  // Clear validation errors when modal opens
  useEffect(() => {
    if (show) {
      setValidationErrors({});
    }
  }, [show]);

  // Tipi di lezione
  const lessonTypes = [
    { value: 'theory', label: '📚 Teoria', description: 'Lezione teorica con contenuti testuali', color: 'primary' },
    { value: 'practical', label: '🎨 Pratica', description: 'Esercitazione pratica guidata', color: 'success' },
    { value: 'video', label: '🎥 Video', description: 'Lezione video con dimostrazione', color: 'warning' },
    { value: 'mixed', label: '🔄 Mista', description: 'Combinazione di teoria e pratica', color: 'info' }
  ];

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processVideoFile(file);
    }
  };

  const processVideoFile = (file) => {
    // Validate file type
    if (!file.type.startsWith('video/')) {
      setError('Per favore seleziona un file video valido');
      return;
    }
    
    // Validate file size (max 200MB)
    if (file.size > 200 * 1024 * 1024) {
      setError('Il video deve essere inferiore a 200MB');
      return;
    }
    
    setVideoFile(file);
    const url = URL.createObjectURL(file);
    setVideoPreview(url);
    setError(''); // Clear any previous errors
  };

  // Drag and drop handlers for video
  const handleVideoDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleVideoDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleVideoDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleVideoDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processVideoFile(files[0]);
    }
  };

  const removeVideo = () => {
    setVideoFile(null);
    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }
    setVideoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetForm = () => {
    setTitle('');
    setContent('');
    setDuration('');
    setLessonType('theory');
    setVideoFile(null);
    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }
    setVideoPreview(null);
    setError('');
    setValidationErrors({});
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('content', content);
      formData.append('duration', duration);
      formData.append('lesson_type', lessonType);
      formData.append('course_id', courseId);
      
      if (videoFile && lessonType === 'video') {
        formData.append('video_file', videoFile);
      }

      await createLesson(formData);
      
      // Show success notification
      setToastConfig({
        variant: 'success',
        title: 'Successo!',
        message: `La lezione "${title}" è stata creata con successo! 🎉`
      });
      setShowToast(true);
      
      resetForm();
      if (onCreated) onCreated();
      
      // Close modal immediately after success
      onHide();
    } catch (err) {
      console.error('Errore creazione lezione:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          'Errore nella creazione della lezione. Verifica tutti i campi.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onHide();
  };

  return (
    <>
      <Modal show={show} onHide={handleClose} size="lg">
      <Modal.Header closeButton className="border-0 pb-0">
        <Modal.Title className="d-flex align-items-center">
          <span className="me-2">📖</span>
          Crea una Nuova Lezione
        </Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body className="pt-2">
          <ErrorDisplay errors={validationErrors} />

          {error && (
            <Alert variant="danger" className="d-flex align-items-center">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              {error}
            </Alert>
          )}

          <Card className="border-0 shadow-sm mb-4">
            <Card.Body>
              <h6 className="text-muted mb-3">📝 Dettagli della Lezione</h6>
              
              <Form.Group className="mb-3">
                <Form.Label className="fw-semibold">
                  <i className="bi bi-book me-2"></i>Titolo della Lezione
                </Form.Label>
                <Form.Control 
                  value={title} 
                  onChange={e => setTitle(e.target.value)} 
                  placeholder="es. Introduzione alla Tecnica dell'Acquerello"
                  className="form-control-lg"
                  isInvalid={!!validationErrors.title}
                  required 
                />
                <Form.Control.Feedback type="invalid">
                  {validationErrors.title}
                </Form.Control.Feedback>
              </Form.Group>

              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-clock me-2"></i>Durata (minuti)
                    </Form.Label>
                    <InputGroup>
                      <Form.Control 
                        type="number" 
                        min={1} 
                        max={300}
                        value={duration} 
                        onChange={e => setDuration(e.target.value)} 
                        placeholder="60"
                        className="form-control-lg"
                        isInvalid={!!validationErrors.duration}
                        required 
                      />
                      <InputGroup.Text>
                        <i className="bi bi-stopwatch"></i>
                      </InputGroup.Text>
                    </InputGroup>
                    {validationErrors.duration && (
                      <div className="text-danger small mt-1">
                        {validationErrors.duration}
                      </div>
                    )}
                  </Form.Group>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm mb-4">
            <Card.Body>
              <h6 className="text-muted mb-3">🎯 Tipo di Lezione</h6>
              <Row>
                {lessonTypes.map((type) => (
                  <Col sm={6} key={type.value} className="mb-3">
                    <div 
                      className={`mb-3 lesson-modal-clickable ${lessonType === type.value ? 'border border-primary rounded' : ''}`}
                      onClick={() => setLessonType(type.value)}
                    >
                      <Card className={`h-100 ${lessonType === type.value ? 'border-primary' : ''}`}>
                        <Card.Body className="text-center p-3">
                          <Badge 
                            bg={lessonType === type.value ? type.color : 'light'} 
                            text={lessonType === type.value ? 'white' : 'dark'}
                            className="mb-2 lesson-modal-badge"
                          >
                            {type.label}
                          </Badge>
                          <p className="small text-muted mb-0">{type.description}</p>
                        </Card.Body>
                      </Card>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm mb-4">
            <Card.Body>
              <h6 className="text-muted mb-3">📄 Contenuto della Lezione</h6>
              <Form.Group>
                <Form.Label className="fw-semibold">
                  <i className="bi bi-text-paragraph me-2"></i>Descrizione e Istruzioni
                </Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={6}
                  value={content} 
                  onChange={e => setContent(e.target.value)} 
                  placeholder="Inserisci il contenuto della lezione, gli obiettivi di apprendimento, le istruzioni step-by-step e i materiali necessari..."
                  isInvalid={!!validationErrors.content}
                  required 
                />
                <Form.Control.Feedback type="invalid">
                  {validationErrors.content}
                </Form.Control.Feedback>
              </Form.Group>
            </Card.Body>
          </Card>

          {lessonType === 'video' && (
            <Card className="border-0 shadow-sm">
              <Card.Body>
                <h6 className="text-muted mb-3">🎥 Video della Lezione</h6>
                {validationErrors.videoFile && (
                  <div className="text-danger small mb-2">
                    <i className="bi bi-exclamation-triangle me-1"></i>
                    {validationErrors.videoFile}
                  </div>
                )}
                
                {!videoPreview ? (
                  <div 
                    className="video-upload-area"
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleVideoDragOver}
                    onDragEnter={handleVideoDragEnter}
                    onDragLeave={handleVideoDragLeave}
                    onDrop={handleVideoDrop}
                  >
                    <div className="upload-content">
                      <i className="bi bi-camera-video fs-1 text-warning mb-3"></i>
                      <h5>Carica Video</h5>
                      <p className="text-muted">
                        Clicca qui o <strong>trascina un video</strong> per caricarlo
                      </p>
                      <small className="text-muted d-block mb-2">
                        Formati supportati: MP4, AVI, MOV (max 200MB)
                      </small>
                      <Button variant="outline-warning">
                        <i className="bi bi-upload me-2"></i>Seleziona Video
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="video-preview">
                    <video 
                      src={videoPreview} 
                      controls 
                      className="preview-video"
                    >
                      Il tuo browser non supporta il tag video.
                    </video>
                    <div className="video-overlay">
                      <Button 
                        variant="danger" 
                        size="sm" 
                        onClick={removeVideo}
                        className="remove-video-btn"
                      >
                        <i className="bi bi-trash"></i>
                      </Button>
                    </div>
                  </div>
                )}
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleVideoChange}
                  className="lesson-modal-hidden-input"
                />
              </Card.Body>
            </Card>
          )}
        </Modal.Body>
        
        <Modal.Footer className="border-0 pt-0">
          <Button variant="outline-secondary" onClick={handleClose}>
            <i className="bi bi-x-circle me-2"></i>Annulla
          </Button>
          <Button 
            type="submit" 
            variant="success" 
            disabled={loading || Object.keys(validationErrors).length > 0 || !title || !content || !duration || (lessonType === 'video' && !videoFile)}
            className="px-4"
          >
            {loading ? (
              <>
                <Spinner size="sm" animation="border" className="me-2" />
                Creazione in corso...
              </>
            ) : (
              <>
                <i className="bi bi-plus-circle me-2"></i>Crea Lezione
              </>
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
    
    <CustomToast
      show={showToast}
      onClose={() => setShowToast(false)}
      variant={toastConfig.variant}
      title={toastConfig.title}
      message={toastConfig.message}
    />
    </>
  );
};

export default LessonCreateModal;
