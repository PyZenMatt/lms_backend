import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Form, Alert, Spinner, Card, Row, Col, Badge, ProgressBar } from 'react-bootstrap';
import { createCourse } from '../../services/api/courses';
import CustomToast from '../ui/Toast';
import '../../assets/css/components/CourseCreateModal.css';

import ErrorDisplay from '../ui/ErrorDisplay';
import { validateCourseForm, debounce } from '../../utils/formValidation';

const CourseCreateModal = ({ show, onHide, onCreated }) => {
  // Form data states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('');
  const [level, setLevel] = useState('beginner');
  const [duration, setDuration] = useState('');
  const [prerequisites, setPrerequisites] = useState('');
  const [learningObjectives, setLearningObjectives] = useState(['']);
  const [coverImage, setCoverImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // UI states
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [showToast, setShowToast] = useState(false);
  const [toastConfig, setToastConfig] = useState({ variant: 'success', title: '', message: '' });
  const fileInputRef = useRef(null);

  const totalSteps = 4;

  // Real-time validation with debouncing
  const validateForm = debounce(() => {
    const formData = { title, description, price, category };
    const validation = validateCourseForm(formData);
    setValidationErrors(validation.errors);
  }, 300);

  // Trigger validation when form data changes
  useEffect(() => {
    validateForm();
  }, [title, description, price, category]);

  // Clear validation errors when modal opens
  useEffect(() => {
    if (show) {
      setValidationErrors({});
    }
  }, [show]);

  // Enhanced categories with better organization
  const categories = [
    { value: 'disegno', label: '✏️ Disegno', color: 'primary', group: 'traditional' },
    { value: 'pittura-olio', label: '🎨 Pittura ad Olio', color: 'warning', group: 'traditional' },
    { value: 'acquerello', label: '💧 Acquerello', color: 'info', group: 'traditional' },
    { value: 'tempera', label: '🖌️ Tempera', color: 'success', group: 'traditional' },
    { value: 'acrilico', label: '🌈 Pittura Acrilica', color: 'danger', group: 'traditional' },
    { value: 'scultura', label: '🗿 Scultura', color: 'dark', group: 'traditional' },
    { value: 'ceramica', label: '🏺 Ceramica', color: 'warning', group: 'traditional' },
    { value: 'incisione', label: '⚱️ Incisione', color: 'dark', group: 'traditional' },
    { value: 'arte-digitale', label: '💻 Arte Digitale', color: 'success', group: 'digital' },
    { value: 'fotografia', label: '📸 Fotografia', color: 'primary', group: 'digital' },
    { value: 'illustrazione', label: '🖊️ Illustrazione', color: 'info', group: 'digital' },
    { value: 'design-grafico', label: '🎨 Design Grafico', color: 'danger', group: 'digital' },
    { value: 'fumetto', label: '💭 Fumetto', color: 'info', group: 'digital' },
    { value: 'storia-arte', label: '📚 Storia dell\'Arte', color: 'secondary', group: 'theory' },
    { value: 'arte-contemporanea', label: '🆕 Arte Contemporanea', color: 'success', group: 'theory' },
    { value: 'arte-classica', label: '🏛️ Arte Classica', color: 'warning', group: 'theory' },
    { value: 'restauro', label: '🛠️ Restauro', color: 'secondary', group: 'theory' },
    { value: 'mosaico', label: '🔷 Mosaico', color: 'primary', group: 'specialized' },
    { value: 'calligrafia', label: '✒️ Calligrafia', color: 'dark', group: 'specialized' },
    { value: 'other', label: '🎭 Altro', color: 'secondary', group: 'specialized' }
  ];

  const levelOptions = [
    { value: 'beginner', label: '� Principiante', description: 'Nessuna esperienza richiesta', color: 'success' },
    { value: 'intermediate', label: '� Intermedio', description: 'Conoscenze di base necessarie', color: 'warning' },
    { value: 'advanced', label: '� Avanzato', description: 'Esperienza significativa richiesta', color: 'danger' },
    { value: 'expert', label: '� Esperto', description: 'Solo per artisti esperti', color: 'dark' }
  ];

  // Step navigation functions
  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step) => {
    setCurrentStep(step);
  };

  // Learning objectives management
  const addLearningObjective = () => {
    setLearningObjectives([...learningObjectives, '']);
  };

  const removeLearningObjective = (index) => {
    if (learningObjectives.length > 1) {
      setLearningObjectives(learningObjectives.filter((_, i) => i !== index));
    }
  };

  const updateLearningObjective = (index, value) => {
    const updated = [...learningObjectives];
    updated[index] = value;
    setLearningObjectives(updated);
  };

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
    
    setCoverImage(file);
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
    setCoverImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setPrice('');
    setCategory('');
    setLevel('beginner');
    setDuration('');
    setPrerequisites('');
    setLearningObjectives(['']);
    setCoverImage(null);
    setImagePreview(null);
    setCurrentStep(1);
    setError('');
    setValidationErrors({});
    setShowToast(false);
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
      formData.append('price', price);
      formData.append('category', category);
      formData.append('level', level);
      formData.append('duration', duration);
      formData.append('prerequisites', prerequisites);
      formData.append('learning_objectives', JSON.stringify(learningObjectives.filter(obj => obj.trim())));
      if (coverImage) {
        formData.append('cover_image', coverImage);
      }

      await createCourse(formData);
      
      // Show success notification
      setToastConfig({
        variant: 'success',
        title: 'Successo!',
        message: `Il corso "${title}" è stato creato con successo! 🎉`
      });
      setShowToast(true);
      
      resetForm();
      if (onCreated) onCreated();
      
      // Close modal immediately after success
      onHide();
    } catch (err) {
      console.error('Errore creazione corso:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          'Errore nella creazione del corso. Verifica tutti i campi.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onHide();
  };

  // Step validation functions
  const isStep1Valid = () => title && description && price;
  const isStep2Valid = () => category && level;
  const isStep3Valid = () => duration && learningObjectives.some(obj => obj.trim());
  const isStep4Valid = () => true; // Image is optional

  const canProceedToNext = () => {
    switch (currentStep) {
      case 1: return isStep1Valid();
      case 2: return isStep2Valid();
      case 3: return isStep3Valid();
      case 4: return isStep4Valid();
      default: return false;
    }
  };

  const renderStepIndicator = () => (
    <div className="step-indicator mb-4">
      <ProgressBar className="mb-3">
        <ProgressBar 
          variant="primary" 
          now={(currentStep / totalSteps) * 100} 
          style={{ transition: 'width 0.3s ease' }}
        />
      </ProgressBar>
      <div className="d-flex justify-content-between">
        {[1, 2, 3, 4].map((step) => (
          <div 
            key={step} 
            className={`step-item ${currentStep >= step ? 'completed' : ''} ${currentStep === step ? 'active' : ''}`}
            onClick={() => goToStep(step)}
            style={{ cursor: 'pointer' }}
          >
            <div className={`step-circle d-flex align-items-center justify-content-center mx-auto mb-2 ${
              currentStep >= step ? 'bg-primary text-white' : 'bg-light text-muted'
            }`} style={{ width: '40px', height: '40px', borderRadius: '50%' }}>
              {currentStep > step ? (
                <i className="feather icon-check" style={{ fontSize: '1rem' }}></i>
              ) : (
                <span className="fw-bold">{step}</span>
              )}
            </div>
            <small className={`text-center d-block ${currentStep >= step ? 'text-primary fw-semibold' : 'text-muted'}`}>
              {step === 1 && 'Informazioni'}
              {step === 2 && 'Categoria'}
              {step === 3 && 'Dettagli'}
              {step === 4 && 'Immagine'}
            </small>
          </div>
        ))}
      </div>
    </div>
  );

  const renderStep1 = () => (
    <Card className="border-0 shadow-sm">
      <Card.Body>
        <div className="text-center mb-4">
          <i className="feather icon-book-open text-primary" style={{ fontSize: '3rem' }}></i>
          <h5 className="mt-3 mb-2">Informazioni Base del Corso</h5>
          <p className="text-muted">Iniziamo con le informazioni fondamentali del tuo corso</p>
        </div>
        
        <Form.Group className="mb-4">
          <Form.Label className="fw-semibold">
            <i className="feather icon-edit-3 me-2"></i>Titolo del Corso
          </Form.Label>
          <Form.Control 
            value={title} 
            onChange={e => setTitle(e.target.value)} 
            placeholder="es. Corso di Pittura ad Olio per Principianti"
            className="form-control-lg"
            isInvalid={!!validationErrors.title}
            size="lg"
          />
          <Form.Text className="text-muted">
            Scegli un titolo chiaro e accattivante che descriva il contenuto del corso
          </Form.Text>
          <Form.Control.Feedback type="invalid">
            {validationErrors.title}
          </Form.Control.Feedback>
        </Form.Group>

        <Form.Group className="mb-4">
          <Form.Label className="fw-semibold">
            <i className="feather icon-align-left me-2"></i>Descrizione del Corso
          </Form.Label>
          <Form.Control 
            as="textarea" 
            rows={5}
            value={description} 
            onChange={e => setDescription(e.target.value)} 
            placeholder="Descrivi il contenuto del corso, gli obiettivi di apprendimento e a chi è rivolto. Includi informazioni sui materiali necessari e cosa impareranno gli studenti..."
            isInvalid={!!validationErrors.description}
          />
          <Form.Text className="text-muted">
            Una descrizione dettagliata aiuta gli studenti a capire cosa aspettarsi dal corso
          </Form.Text>
          <Form.Control.Feedback type="invalid">
            {validationErrors.description}
          </Form.Control.Feedback>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label className="fw-semibold">
            <i className="feather icon-dollar-sign me-2"></i>Prezzo (TeoCoin)
          </Form.Label>
          <div className="input-group input-group-lg">
            <Form.Control 
              type="number" 
              min={0} 
              value={price} 
              onChange={e => setPrice(e.target.value)} 
              placeholder="0"
              isInvalid={!!validationErrors.price}
            />
            <span className="input-group-text">TEO</span>
          </div>
          <Form.Text className="text-muted">
            Imposta un prezzo equo considerando la durata e il valore del contenuto
          </Form.Text>
          <Form.Control.Feedback type="invalid">
            {validationErrors.price}
          </Form.Control.Feedback>
        </Form.Group>
      </Card.Body>
    </Card>
  );

  const renderStep2 = () => {
    const groupedCategories = {
      traditional: categories.filter(cat => cat.group === 'traditional'),
      digital: categories.filter(cat => cat.group === 'digital'),
      theory: categories.filter(cat => cat.group === 'theory'),
      specialized: categories.filter(cat => cat.group === 'specialized')
    };

    return (
      <Card className="border-0 shadow-sm">
        <Card.Body>
          <div className="text-center mb-4">
            <i className="feather icon-grid text-primary" style={{ fontSize: '3rem' }}></i>
            <h5 className="mt-3 mb-2">Categoria e Livello</h5>
            <p className="text-muted">Seleziona la categoria artistica e il livello di difficoltà</p>
          </div>

          <div className="mb-4">
            <h6 className="fw-semibold mb-3">
              <i className="feather icon-tag me-2"></i>Categoria Artistica
            </h6>
            {validationErrors.category && (
              <div className="text-danger small mb-3">
                <i className="feather icon-alert-triangle me-1"></i>
                {validationErrors.category}
              </div>
            )}
            
            {Object.entries(groupedCategories).map(([groupName, groupCategories]) => (
              <div key={groupName} className="mb-4">
                <small className="text-muted fw-semibold text-uppercase d-block mb-2">
                  {groupName === 'traditional' && '🎨 Arte Tradizionale'}
                  {groupName === 'digital' && '💻 Arte Digitale'}
                  {groupName === 'theory' && '📚 Teoria e Storia'}
                  {groupName === 'specialized' && '🎭 Specializzate'}
                </small>
                <Row>
                  {groupCategories.map((cat) => (
                    <Col sm={6} md={4} key={cat.value} className="mb-2">
                      <div 
                        className={`category-option cursor-pointer h-100 ${category === cat.value ? 'selected' : ''}`}
                        onClick={() => setCategory(cat.value)}
                      >
                        <Badge 
                          bg={category === cat.value ? cat.color : 'light'} 
                          text={category === cat.value ? 'white' : 'dark'}
                          className="w-100 p-3 category-badge h-100 d-flex align-items-center justify-content-center"
                          style={{ fontSize: '0.9rem', minHeight: '50px' }}
                        >
                          {cat.label}
                        </Badge>
                      </div>
                    </Col>
                  ))}
                </Row>
              </div>
            ))}
          </div>

          <div>
            <h6 className="fw-semibold mb-3">
              <i className="feather icon-trending-up me-2"></i>Livello di Difficoltà
            </h6>
            <Row>
              {levelOptions.map((levelOption) => (
                <Col sm={6} md={3} key={levelOption.value} className="mb-3">
                  <Card 
                    className={`h-100 cursor-pointer border-2 ${level === levelOption.value ? `border-${levelOption.color}` : 'border-light'}`}
                    onClick={() => setLevel(levelOption.value)}
                    style={{ transition: 'all 0.3s ease' }}
                  >
                    <Card.Body className="text-center p-3">
                      <Badge 
                        bg={level === levelOption.value ? levelOption.color : 'light'} 
                        text={level === levelOption.value ? 'white' : 'dark'}
                        className="mb-2"
                      >
                        {levelOption.label}
                      </Badge>
                      <p className="small text-muted mb-0">{levelOption.description}</p>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </Card.Body>
      </Card>
    );
  };

  const renderStep3 = () => (
    <Card className="border-0 shadow-sm">
      <Card.Body>
        <div className="text-center mb-4">
          <i className="feather icon-clock text-primary" style={{ fontSize: '3rem' }}></i>
          <h5 className="mt-3 mb-2">Dettagli del Corso</h5>
          <p className="text-muted">Aggiungi informazioni dettagliate per completare il corso</p>
        </div>

        <Row>
          <Col md={6}>
            <Form.Group className="mb-4">
              <Form.Label className="fw-semibold">
                <i className="feather icon-clock me-2"></i>Durata Stimata
              </Form.Label>
              <div className="input-group input-group-lg">
                <Form.Control 
                  type="number" 
                  min={1} 
                  value={duration} 
                  onChange={e => setDuration(e.target.value)} 
                  placeholder="8"
                />
                <span className="input-group-text">ore</span>
              </div>
              <Form.Text className="text-muted">
                Stima il tempo totale necessario per completare il corso
              </Form.Text>
            </Form.Group>
          </Col>
        </Row>

        <Form.Group className="mb-4">
          <Form.Label className="fw-semibold">
            <i className="feather icon-check-square me-2"></i>Prerequisiti
          </Form.Label>
          <Form.Control 
            as="textarea" 
            rows={3}
            value={prerequisites} 
            onChange={e => setPrerequisites(e.target.value)} 
            placeholder="es. Conoscenze di base del disegno, materiali artistici di base..."
          />
          <Form.Text className="text-muted">
            Specifica le conoscenze o materiali necessari (lascia vuoto se non ci sono prerequisiti)
          </Form.Text>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label className="fw-semibold">
            <i className="feather icon-target me-2"></i>Obiettivi di Apprendimento
          </Form.Label>
          {learningObjectives.map((objective, index) => (
            <div key={index} className="d-flex mb-2">
              <Form.Control 
                value={objective}
                onChange={(e) => updateLearningObjective(index, e.target.value)}
                placeholder={`Obiettivo ${index + 1}...`}
                className="me-2"
              />
              {learningObjectives.length > 1 && (
                <Button 
                  variant="outline-danger" 
                  size="sm"
                  onClick={() => removeLearningObjective(index)}
                >
                  <i className="feather icon-trash-2"></i>
                </Button>
              )}
            </div>
          ))}
          <Button 
            variant="outline-primary" 
            size="sm" 
            onClick={addLearningObjective}
            className="mt-2"
          >
            <i className="feather icon-plus me-2"></i>Aggiungi Obiettivo
          </Button>
          <Form.Text className="text-muted d-block mt-2">
            Elenca cosa impareranno gli studenti completando questo corso
          </Form.Text>
        </Form.Group>
      </Card.Body>
    </Card>
  );

  const renderStep4 = () => (
    <Card className="border-0 shadow-sm">
      <Card.Body>
        <div className="text-center mb-4">
          <i className="feather icon-image text-primary" style={{ fontSize: '3rem' }}></i>
          <h5 className="mt-3 mb-2">Immagine di Copertina</h5>
          <p className="text-muted">Aggiungi un'immagine accattivante per il tuo corso (opzionale)</p>
        </div>
        
        {!imagePreview ? (
          <div 
            className="image-upload-area"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-content">
              <i className="feather icon-upload-cloud text-primary mb-3" style={{ fontSize: '4rem' }}></i>
              <h5>Carica Immagine di Copertina</h5>
              <p className="text-muted">
                Clicca qui o <strong>trascina un'immagine</strong> per selezionare una copertina
              </p>
              <small className="text-muted d-block mb-3">
                Formati supportati: JPG, PNG, GIF (max 5MB)
              </small>
              <Button variant="outline-primary" size="lg">
                <i className="feather icon-image me-2"></i>Seleziona Immagine
              </Button>
            </div>
          </div>
        ) : (
          <div className="image-preview text-center">
            <img src={imagePreview} alt="Preview" className="preview-image mb-3" />
            <div>
              <Button 
                variant="outline-danger" 
                onClick={removeImage}
                className="me-2"
              >
                <i className="feather icon-trash-2 me-2"></i>Rimuovi
              </Button>
              <Button 
                variant="outline-primary"
                onClick={() => fileInputRef.current?.click()}
              >
                <i className="feather icon-edit me-2"></i>Cambia Immagine
              </Button>
            </div>
          </div>
        )}
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{ display: 'none' }}
        />
      </Card.Body>
    </Card>
  );

  return (
    <>
      <Modal show={show} onHide={handleClose} size="lg" backdrop="static">
        <Modal.Header closeButton className="border-0 pb-0">
          <Modal.Title className="d-flex align-items-center">
            <span className="me-2">🎨</span>
            Crea un Nuovo Corso Artistico
          </Modal.Title>
        </Modal.Header>
        
        <Form onSubmit={handleSubmit}>
          <Modal.Body className="pt-2">
            {renderStepIndicator()}
            
            <ErrorDisplay errors={validationErrors} />

            {error && (
              <Alert variant="danger" className="d-flex align-items-center mb-4">
                <i className="feather icon-alert-triangle me-2"></i>
                {error}
              </Alert>
            )}

            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
            {currentStep === 4 && renderStep4()}
          </Modal.Body>
          
          <Modal.Footer className="border-0 pt-0">
            <div className="d-flex justify-content-between w-100">
              <div>
                {currentStep > 1 && (
                  <Button variant="outline-secondary" onClick={prevStep}>
                    <i className="feather icon-arrow-left me-2"></i>Indietro
                  </Button>
                )}
              </div>
              
              <div className="d-flex gap-2">
                <Button variant="outline-secondary" onClick={handleClose}>
                  <i className="feather icon-x me-2"></i>Annulla
                </Button>
                
                {currentStep < totalSteps ? (
                  <Button 
                    variant="primary" 
                    onClick={nextStep}
                    disabled={!canProceedToNext()}
                  >
                    Avanti
                    <i className="feather icon-arrow-right ms-2"></i>
                  </Button>
                ) : (
                  <Button 
                    type="submit" 
                    variant="success" 
                    disabled={loading || !canProceedToNext()}
                    className="px-4"
                  >
                    {loading ? (
                      <>
                        <Spinner size="sm" animation="border" className="me-2" />
                        Creazione...
                      </>
                    ) : (
                      <>
                        <i className="feather icon-check me-2"></i>Crea Corso
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
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

export default CourseCreateModal;
