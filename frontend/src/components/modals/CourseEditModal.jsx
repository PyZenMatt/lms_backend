import React, { useState, useEffect } from 'react';
import { Modal, Form, Button, Alert, Spinner, Row, Col } from 'react-bootstrap';
import PropTypes from 'prop-types';
import { fetchCourseDetail, updateCourse } from '../../services/api/courses';

const CourseEditModal = ({ show, onHide, courseId, onCourseUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('PITTURA');
  const [teocoinDiscountPercent, setTeocoinDiscountPercent] = useState('10');
  const [teocoinReward, setTeocoinReward] = useState('5');
  const [coverImage, setCoverImage] = useState(null);
  const [currentCoverImageUrl, setCurrentCoverImageUrl] = useState('');

  // Validation
  const [validationErrors, setValidationErrors] = useState({});

  // Load course data when modal opens
  useEffect(() => {
    if (show && courseId) {
      loadCourseData();
    } else if (!show) {
      // Reset form when modal closes
      resetForm();
    }
  }, [show, courseId]);

  const loadCourseData = async () => {
    setLoading(true);
    setError('');
    try {
      const course = await fetchCourseDetail(courseId);

      setTitle(course.title || '');
      setDescription(course.description || '');
      setPrice(course.price || course.price_eur || '');
      setCategory(course.category || 'PITTURA');
      setTeocoinDiscountPercent(course.teocoin_discount_percent || '10');
      setTeocoinReward(course.teocoin_reward || '5');
      setCurrentCoverImageUrl(course.cover_image_url || course.cover_image || '');
    } catch (err) {
      setError('Errore nel caricamento dei dati del corso');
      console.error('Error loading course:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setPrice('');
    setCategory('PITTURA');
    setTeocoinDiscountPercent('10');
    setTeocoinReward('5');
    setCoverImage(null);
    setCurrentCoverImageUrl('');
    setError('');
    setSuccess(false);
    setValidationErrors({});
  };

  const validateForm = () => {
    const errors = {};

    if (!title.trim()) {
      errors.title = 'Il titolo è obbligatorio';
    }

    if (!description.trim()) {
      errors.description = 'La descrizione è obbligatoria';
    }

    if (!price || parseFloat(price) < 0) {
      errors.price = 'Il prezzo deve essere un numero positivo';
    }

    if (!category) {
      errors.category = 'La categoria è obbligatoria';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      formData.append('price', price);
      formData.append('category', category);
      formData.append('teocoin_discount_percent', teocoinDiscountPercent);
      formData.append('teocoin_reward', teocoinReward);

      if (coverImage) {
        formData.append('cover_image', coverImage);
      }

      await updateCourse(courseId, formData);

      setSuccess(true);

      // Notify parent component
      if (onCourseUpdated) {
        onCourseUpdated(courseId);
      }

      // Close modal after 1 second
      setTimeout(() => {
        onHide();
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.message || "Errore nell'aggiornamento del corso");
      console.error('Error updating course:', err);
    } finally {
      setSaving(false);
    }
  };

  const categoryOptions = [
    { value: 'PITTURA', label: 'Pittura' },
    { value: 'SCULTURA', label: 'Scultura' },
    { value: 'DISEGNO', label: 'Disegno' },
    { value: 'FOTOGRAFIA', label: 'Fotografia' },
    { value: 'ARTE_DIGITALE', label: 'Arte Digitale' },
    { value: 'ALTRO', label: 'Altro' }
  ];

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          <i className="feather icon-edit me-2"></i>
          Modifica Corso
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {loading ? (
          <div className="text-center py-4">
            <Spinner animation="border" variant="primary" />
            <p className="mt-2">Caricamento dati corso...</p>
          </div>
        ) : (
          <Form onSubmit={handleSubmit}>
            {error && (
              <Alert variant="danger" className="mb-3">
                <i className="feather icon-alert-circle me-2"></i>
                {error}
              </Alert>
            )}

            {success && (
              <Alert variant="success" className="mb-3">
                <i className="feather icon-check-circle me-2"></i>
                Corso aggiornato con successo!
              </Alert>
            )}

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>
                    <i className="feather icon-book me-2"></i>Titolo Corso
                  </Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Es. Corso di Pittura Base"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    isInvalid={!!validationErrors.title}
                  />
                  <Form.Control.Feedback type="invalid">{validationErrors.title}</Form.Control.Feedback>
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>
                    <i className="feather icon-tag me-2"></i>Categoria
                  </Form.Label>
                  <Form.Select value={category} onChange={(e) => setCategory(e.target.value)} isInvalid={!!validationErrors.category}>
                    {categoryOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Form.Select>
                  <Form.Control.Feedback type="invalid">{validationErrors.category}</Form.Control.Feedback>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>
                <i className="feather icon-file-text me-2"></i>Descrizione
              </Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Descrivi il tuo corso..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                isInvalid={!!validationErrors.description}
              />
              <Form.Control.Feedback type="invalid">{validationErrors.description}</Form.Control.Feedback>
            </Form.Group>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>
                    <i className="feather icon-euro me-2"></i>Prezzo (Euro)
                  </Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    isInvalid={!!validationErrors.price}
                  />
                  <Form.Control.Feedback type="invalid">{validationErrors.price}</Form.Control.Feedback>
                </Form.Group>
              </Col>

              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>
                    <i className="feather icon-percent me-2"></i>Sconto TeoCoin (%)
                  </Form.Label>
                  <Form.Control
                    type="number"
                    min="0"
                    max="50"
                    value={teocoinDiscountPercent}
                    onChange={(e) => setTeocoinDiscountPercent(e.target.value)}
                  />
                </Form.Group>
              </Col>

              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>
                    <i className="feather icon-award me-2"></i>Ricompensa TeoCoin
                  </Form.Label>
                  <Form.Control type="number" min="0" max="100" value={teocoinReward} onChange={(e) => setTeocoinReward(e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>
                <i className="feather icon-image me-2"></i>Immagine di Copertina
              </Form.Label>
              {currentCoverImageUrl && (
                <div className="mb-2">
                  <img
                    src={currentCoverImageUrl}
                    alt="Cover attuale"
                    style={{ maxWidth: '200px', maxHeight: '100px', objectFit: 'cover' }}
                    className="rounded"
                  />
                  <p className="text-muted small mt-1">Immagine attuale</p>
                </div>
              )}
              <Form.Control type="file" accept="image/*" onChange={(e) => setCoverImage(e.target.files[0])} />
              <Form.Text className="text-muted">Carica una nuova immagine se vuoi sostituire quella attuale</Form.Text>
            </Form.Group>
          </Form>
        )}
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onHide} disabled={saving}>
          Annulla
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={saving || loading}>
          {saving ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" className="me-2" />
              Salvando...
            </>
          ) : (
            <>
              <i className="feather icon-save me-2"></i>
              Salva Modifiche
            </>
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

CourseEditModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onHide: PropTypes.func.isRequired,
  courseId: PropTypes.number,
  onCourseUpdated: PropTypes.func
};

export default CourseEditModal;
