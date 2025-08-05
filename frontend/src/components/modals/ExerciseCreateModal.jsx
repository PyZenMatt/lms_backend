import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Form, Alert, Spinner, Card, Row, Col, Badge, InputGroup } from 'react-bootstrap';
import { createExercise } from '../../services/api/courses';
import CustomToast from '../ui/Toast';
import '../../assets/css/components/ExerciseCreateModal.css';

import ErrorDisplay from '../ui/ErrorDisplay';
import { validateExerciseForm, debounce } from '../../utils/formValidation';

const ExerciseCreateModal = ({ show, onHide, onCreated, lessonId, courseId }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [exerciseType, setExerciseType] = useState('practical');
  const [difficulty, setDifficulty] = useState('beginner');
  const [timeEstimate, setTimeEstimate] = useState('');
  const [materials, setMaterials] = useState('');
  const [instructions, setInstructions] = useState('');
  const [referenceImage, setReferenceImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
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
      description, 
      timeEstimate, 
      materials, 
      instructions 
    };
    const validation = validateExerciseForm(formData);
    setValidationErrors(validation.errors);
  }, 300);

  // Trigger validation when form data changes
  useEffect(() => {
    validateForm();
  }, [title, description, timeEstimate, materials, instructions]);

  // Clear validation errors when modal opens
  useEffect(() => {
    if (show) {
      setValidationErrors({});
    }
  }, [show]);

  // Tipi di esercizio
  const exerciseTypes = [
    { value: 'practical', label: '🎨 Pratico', description: 'Esercizio di creazione artistica', color: 'success' },
    { value: 'study', label: '📖 Studio', description: 'Analisi e studio di opere', color: 'primary' },
    { value: 'technique', label: '🛠️ Tecnica', description: 'Pratica di tecniche specifiche', color: 'warning' },
    { value: 'creative', label: '💡 Creativo', description: 'Progetto libero e creativo', color: 'info' }
  ];

  // Livelli di difficoltà
  const difficultyLevels = [
    { value: 'beginner', label: '🌱 Principiante', color: 'success' },
    { value: 'intermediate', label: '🌿 Intermedio', color: 'warning' },
    { value: 'advanced', label: '🌳 Avanzato', color: 'danger' }
  ];

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processImageFile(file);
    }
  };

  const processImageFile = (file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Per favore seleziona un file immagine valido');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('L\'immagine deve essere inferiore a 5MB');
      return;
    }
    
    setReferenceImage(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
    setError(''); // Clear any previous errors
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processImageFile(files[0]);
    }
  };

  const removeImage = () => {
    setReferenceImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setExerciseType('practical');
    setDifficulty('beginner');
    setTimeEstimate('');
    setMaterials('');
    setInstructions('');
    setReferenceImage(null);
    setImagePreview(null);
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
      formData.append('description', description);
      formData.append('exercise_type', exerciseType);
      formData.append('difficulty', difficulty);
      formData.append('time_estimate', timeEstimate);
      formData.append('materials', materials);
      formData.append('instructions', instructions);
      formData.append('lesson', lessonId); // Il campo si chiama 'lesson' nel serializer
      formData.append('lesson_id', lessonId);
      formData.append('course_id', courseId);
      
      if (referenceImage) {
        formData.append('reference_image', referenceImage);
      }

      console.log('📤 Creating exercise with data:', {
        title,
        lessonId,
        courseId,
        exercise_type: exerciseType,
        difficulty
      });

      await createExercise(formData);
      
      // Show success notification
      setToastConfig({
        variant: 'success',
        title: 'Successo!',
        message: `L'esercizio "${title}" è stato creato con successo! 🎉`
      });
      setShowToast(true);
      
      resetForm();
      if (onCreated) onCreated();
      
      // Delay modal close to show success message
      setTimeout(() => {
        onHide();
      }, 2000);
    } catch (err) {
      console.error("Errore creazione esercizio:", err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          "Errore nella creazione dell'esercizio. Verifica tutti i campi.";
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
      <Modal show={show} onHide={handleClose} size="xl" className="exercise-create-modal">
      <Modal.Header closeButton className="border-0 pb-0">
        <Modal.Title className="d-flex align-items-center">
          <span className="me-2">🎯</span>
          Crea un Nuovo Esercizio Artistico
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

          <Row>
            <Col lg={8}>
              <Card className="border-0 shadow-sm mb-4">
                <Card.Body>
                  <h6 className="text-muted mb-3">📝 Informazioni Base</h6>
                  
                  <Form.Group className="mb-3">
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-palette me-2"></i>Titolo dell'Esercizio
                    </Form.Label>
                    <Form.Control 
                      value={title} 
                      onChange={e => setTitle(e.target.value)} 
                      placeholder="es. Disegno dal vero - Studio di natura morta"
                      className="form-control-lg"
                      isInvalid={!!validationErrors.title}
                      required 
                    />
                    <Form.Control.Feedback type="invalid">
                      {validationErrors.title}
                    </Form.Control.Feedback>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-text-paragraph me-2"></i>Descrizione dell'Esercizio
                    </Form.Label>
                    <Form.Control 
                      as="textarea" 
                      rows={3}
                      value={description} 
                      onChange={e => setDescription(e.target.value)} 
                      placeholder="Descrivi brevemente l'esercizio e i suoi obiettivi..."
                      isInvalid={!!validationErrors.description}
                      required 
                    />
                    <Form.Control.Feedback type="invalid">
                      {validationErrors.description}
                    </Form.Control.Feedback>
                  </Form.Group>

                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label className="fw-semibold">
                          <i className="bi bi-clock me-2"></i>Tempo Stimato
                        </Form.Label>
                        <InputGroup>
                          <Form.Control 
                            type="number" 
                            min={1} 
                            max={480}
                            value={timeEstimate} 
                            onChange={e => setTimeEstimate(e.target.value)} 
                            placeholder="60"
                            isInvalid={!!validationErrors.timeEstimate}
                            required 
                          />
                          <InputGroup.Text>minuti</InputGroup.Text>
                        </InputGroup>
                        {validationErrors.timeEstimate && (
                          <div className="text-danger small mt-1">
                            {validationErrors.timeEstimate}
                          </div>
                        )}
                      </Form.Group>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>

              <Card className="border-0 shadow-sm mb-4">
                <Card.Body>
                  <h6 className="text-muted mb-3">📋 Materiali Necessari</h6>
                  <Form.Group>
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-list-ul me-2"></i>Lista Materiali
                    </Form.Label>
                    <Form.Control 
                      as="textarea" 
                      rows={3}
                      value={materials} 
                      onChange={e => setMaterials(e.target.value)} 
                      placeholder="Elenca i materiali necessari (es. matite 2B, 4B, carta da disegno, gomma...)"
                      isInvalid={!!validationErrors.materials}
                      required 
                    />
                    <Form.Control.Feedback type="invalid">
                      {validationErrors.materials}
                    </Form.Control.Feedback>
                  </Form.Group>
                </Card.Body>
              </Card>

              <Card className="border-0 shadow-sm">
                <Card.Body>
                  <h6 className="text-muted mb-3">📖 Istruzioni Dettagliate</h6>
                  <Form.Group>
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-list-ol me-2"></i>Passaggi dell'Esercizio
                    </Form.Label>
                    <Form.Control 
                      as="textarea" 
                      rows={6}
                      value={instructions} 
                      onChange={e => setInstructions(e.target.value)} 
                      placeholder="Descrivi passo dopo passo come svolgere l'esercizio..."
                      isInvalid={!!validationErrors.instructions}
                      required 
                    />
                    <Form.Control.Feedback type="invalid">
                      {validationErrors.instructions}
                    </Form.Control.Feedback>
                  </Form.Group>
                </Card.Body>
              </Card>
            </Col>

            <Col lg={4}>
              <Card className="border-0 shadow-sm mb-4">
                <Card.Body>
                  <h6 className="text-muted mb-3">🎯 Tipo di Esercizio</h6>
                  {exerciseTypes.map((type) => (
                    <div 
                      key={type.value}
                      className={`mb-2 exercise-modal-clickable ${exerciseType === type.value ? 'border border-primary rounded' : ''}`}
                      onClick={() => setExerciseType(type.value)}
                    >
                      <Card className={exerciseType === type.value ? 'border-primary' : ''}>
                        <Card.Body className="p-2">
                          <div className="d-flex align-items-center">
                            <Badge 
                              bg={exerciseType === type.value ? type.color : 'light'} 
                              text={exerciseType === type.value ? 'white' : 'dark'}
                              className="me-2"
                            >
                              {type.label}
                            </Badge>
                          </div>
                          <small className="text-muted">{type.description}</small>
                        </Card.Body>
                      </Card>
                    </div>
                  ))}
                </Card.Body>
              </Card>

              <Card className="border-0 shadow-sm mb-4">
                <Card.Body>
                  <h6 className="text-muted mb-3">⚡ Livello di Difficoltà</h6>
                  {difficultyLevels.map((level) => (
                    <div 
                      key={level.value}
                      className={`difficulty-option mb-2 ${difficulty === level.value ? 'selected' : ''}`}
                      onClick={() => setDifficulty(level.value)}
                    >
                      <Badge 
                        bg={difficulty === level.value ? level.color : 'light'} 
                        text={difficulty === level.value ? 'white' : 'dark'}
                        className="w-100 p-2 difficulty-badge"
                      >
                        {level.label}
                      </Badge>
                    </div>
                  ))}
                </Card.Body>
              </Card>

              <Card className="border-0 shadow-sm">
                <Card.Body>
                  <h6 className="text-muted mb-3">🖼️ Immagine di Riferimento</h6>
                  
                  {!imagePreview ? (
                    <div 
                      className="reference-upload-area"
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver}
                      onDragEnter={handleDragEnter}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      <div className="upload-content">
                        <i className="bi bi-image fs-2 text-info mb-2"></i>
                        <p className="small text-muted mb-2">
                          Clicca qui o <strong>trascina un'immagine</strong> di riferimento
                        </p>
                        <small className="text-muted d-block mb-2">
                          JPG, PNG, GIF (max 5MB)
                        </small>
                        <Button variant="outline-info" size="sm">
                          <i className="bi bi-upload me-1"></i>Carica
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="reference-preview">
                      <img src={imagePreview} alt="Reference" className="reference-image" />
                      <div className="image-overlay">
                        <Button 
                          variant="danger" 
                          size="sm" 
                          onClick={removeImage}
                          className="remove-image-btn"
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="exercise-modal-hidden-input"
                  />
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Modal.Body>
        
        <Modal.Footer className="border-0 pt-0">
          <Button variant="outline-secondary" onClick={handleClose} disabled={loading}>
            <i className="bi bi-x-circle me-2"></i>Annulla
          </Button>
          <Button 
            type="submit" 
            variant="info" 
            disabled={loading || Object.keys(validationErrors).length > 0 || !title || !description || !timeEstimate || !materials || !instructions}
            className="px-4"
          >
            {loading ? (
              <>
                <Spinner size="sm" animation="border" className="me-2" />
                Creazione in corso...
              </>
            ) : (
              <>
                <i className="bi bi-plus-circle me-2"></i>Crea Esercizio
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

export default ExerciseCreateModal;
