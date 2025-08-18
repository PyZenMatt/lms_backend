import React, { useEffect, useState } from 'react';
import { Card, Button, Row, Col, Spinner, Alert, Badge, Form, InputGroup } from '@/components/ui/legacy-shims';
import { fetchCourses } from '../../services/api/courses';
import CourseCheckoutModal from '../../components/courses/DBCourseCheckoutModal';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const AllCourses = () => {
  const [courses, setCourses] = useState([]);
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [expandedCourse, setExpandedCourse] = useState(null);
  const [courseLessons, setCourseLessons] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);

  // Categorie artistiche disponibili
  const categories = [
    { value: 'all', label: 'Tutte le categorie' },
    { value: 'disegno', label: '✏️ Disegno' },
    { value: 'pittura-olio', label: '🎨 Pittura ad Olio' },
    { value: 'acquerello', label: '💧 Acquerello' },
    { value: 'tempera', label: '🖌️ Tempera' },
    { value: 'acrilico', label: '🌈 Pittura Acrilica' },
    { value: 'scultura', label: '🗿 Scultura' },
    { value: 'storia-arte', label: "📚 Storia dell'Arte" },
    { value: 'fotografia', label: '📸 Fotografia Artistica' },
    { value: 'illustrazione', label: '🖊️ Illustrazione' },
    { value: 'arte-digitale', label: '💻 Arte Digitale' },
    { value: 'ceramica', label: '🏺 Ceramica e Terracotta' },
    { value: 'incisione', label: '⚱️ Incisione e Stampa' },
    { value: 'mosaico', label: '🔷 Mosaico' },
    { value: 'restauro', label: '🛠️ Restauro Artistico' },
    { value: 'calligrafia', label: '✒️ Calligrafia' },
    { value: 'fumetto', label: '💭 Fumetto e Graphic Novel' },
    { value: 'design-grafico', label: '🎨 Design Grafico' },
    { value: 'arte-contemporanea', label: '🆕 Arte Contemporanea' },
    { value: 'arte-classica', label: '🏛️ Arte Classica' },
    { value: 'other', label: '🎭 Altro' }
  ];

  useEffect(() => {
    const loadCourses = async () => {
      setLoading(true);
      try {
        const params = {};
        if (selectedCategory !== 'all') {
          params.category = selectedCategory;
        }
        if (searchTerm) {
          params.search = searchTerm;
        }
        params.ordering = '-created_at'; // Ordina per data di creazione discendente

        const res = await fetchCourses(params);
        setCourses(res.data);
        setFilteredCourses(res.data);
      } catch (err) {
        setError('Errore nel caricamento dei corsi');
      } finally {
        setLoading(false);
      }
    };
    loadCourses();
  }, [selectedCategory, searchTerm]);

  // Rimuoviamo il filtro lato client dato che ora filtriamo lato server
  // useEffect(() => {
  //   let filtered = courses;
  //   // ... filtri rimossi
  //   setFilteredCourses(filtered);
  // }, [courses, selectedCategory, searchTerm]);

  const handlePurchase = (course) => {
    setSelectedCourse(course);
    setShowCheckoutModal(true);
  };

  const handlePurchaseComplete = (courseId, data) => {
    setSuccess('Corso acquistato con successo!');
    setCourses((prev) => prev.map((c) => (c.id === courseId ? { ...c, is_enrolled: true } : c)));
    // Wait a bit then close the modal
    setTimeout(() => {
      setShowCheckoutModal(false);
    }, 2000);
  };

  const handleExpand = async (courseId) => {
    console.log('handleExpand chiamato per corso', courseId); // <--- AGGIUNGI QUESTO
    if (expandedCourse === courseId) {
      setExpandedCourse(null);
      return;
    }
    setExpandedCourse(courseId);
    if (!courseLessons[courseId]) {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('access');
        const res = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}/lessons/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        const text = await res.text();
        console.log('Risposta grezza:', text);
        let data = [];
        try {
          data = JSON.parse(text);
          if (!Array.isArray(data)) data = [];
        } catch (e) {
          console.error('Risposta non in JSON:', text);
          data = [];
        }
        setCourseLessons((prev) => ({ ...prev, [courseId]: data }));
      } catch (err) {
        console.error('Errore fetch lezioni:', err);
        setCourseLessons((prev) => ({ ...prev, [courseId]: [] }));
      }
    }
  };

  if (loading)
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
        <Spinner animation="border" variant="primary" />
      </div>
    );

  return (
    <div className="container-fluid px-4 py-4">
      {/* Header Section */}
      <div className="row mb-4">
        <div className="col-12">
          <h1 className="h2 mb-3" style={{ color: '#6c63ff' }}>
            <i className="feather icon-palette me-2"></i>
            Esplora i Corsi d'Arte
          </h1>
          <p className="text-muted">Scopri i migliori corsi artistici per sviluppare la tua creatività e tecnica</p>
        </div>
      </div>

      {/* Search and Filter Section */}
      <div className="row mb-4">
        <div className="col-md-6">
          <InputGroup>
            <InputGroup.Text>
              <i className="feather icon-search"></i>
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder="Cerca corsi d'arte, artisti o tecniche..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </div>
        <div className="col-md-6">
          <Form.Select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            {categories.map((category) => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </Form.Select>
        </div>
      </div>

      {/* Alert Messages */}
      {error && (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" className="mb-4">
          {success}
        </Alert>
      )}

      {/* Results Count */}
      <div className="row mb-3">
        <div className="col-12">
          <p className="text-muted">
            {filteredCourses.length} {filteredCourses.length === 1 ? 'corso trovato' : 'corsi trovati'}
          </p>
        </div>
      </div>

      {/* Courses Grid */}
      <Row className="g-4">
        {filteredCourses.length === 0 ? (
          <Col xs={12}>
            <Card className="text-center py-5">
              <Card.Body>
                <i className="feather icon-palette" style={{ fontSize: '3rem', color: 'hsl(var(--muted))' }}></i>
                <h4 className="mt-3 text-muted">Nessun corso d'arte trovato</h4>
                <p className="text-muted">Prova a modificare i filtri di ricerca</p>
              </Card.Body>
            </Card>
          </Col>
        ) : (
          filteredCourses.map((course) => (
            <Col key={course.id} xs={12} md={6} lg={4}>
              <Card
                className="h-100 shadow-sm border-0"
                style={{ transition: 'transform 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-5px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                {/* Course Image */}
                <div style={{ height: '200px', backgroundColor: 'var(--bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg, var(--background))', position: 'relative' }}>
                  {course.cover_image_url ? (
                    <Card.Img
                      variant="top"
                      src={course.cover_image_url}
                      style={{ height: '200px', objectFit: 'cover' }}
                      alt={course.title}
                    />
                  ) : (
                    <div className="d-flex align-items-center justify-content-center h-100">
                      <i className="feather icon-palette" style={{ fontSize: '3rem', color: 'hsl(var(--muted))' }}></i>
                    </div>
                  )}

                  {/* Category Badge */}
                  {course.category_display && (
                    <Badge bg="primary" className="position-absolute top-0 start-0 m-2" style={{ backgroundColor: '#6c63ff' }}>
                      {course.category_display}
                    </Badge>
                  )}

                  {/* Enrollment Status */}
                  {course.is_enrolled && (
                    <Badge bg="success" className="position-absolute top-0 end-0 m-2">
                      Iscritto
                    </Badge>
                  )}
                </div>

                <Card.Body className="d-flex flex-column">
                  {/* Course Title */}
                  <Card.Title className="h5 mb-2" style={{ color: '#2d3436' }}>
                    {course.title || 'Senza titolo'}
                  </Card.Title>

                  {/* Teacher Info */}
                  <div className="mb-2">
                    <small className="text-muted">
                      <i className="feather icon-user me-1"></i>
                      {course.teacher?.username || 'Docente non specificato'}
                    </small>
                  </div>

                  {/* Course Description */}
                  <Card.Text className="text-muted flex-grow-1" style={{ fontSize: '0.9rem' }}>
                    {course.description?.length > 100
                      ? course.description.substring(0, 100) + '...'
                      : course.description || 'Nessuna descrizione disponibile'}
                  </Card.Text>

                  {/* Course Stats and Pricing */}
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <div className="d-flex align-items-center">
                        <i className="feather icon-users me-1 text-muted"></i>
                        <small className="text-muted">{course.student_count || 0} studenti</small>
                      </div>
                    </div>

                    {/* Dual Pricing Display */}
                    <div className="pricing-section p-2" style={{ backgroundColor: 'var(--bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg, var(--background))', borderRadius: '6px' }}>
                      {course.price_eur > 0 ? (
                        <>
                          <div className="d-flex justify-content-between align-items-center mb-1">
                            <span className="text-primary fw-bold">💳 €{course.price_eur}</span>
                            <small className="text-success">+2 TEO reward</small>
                          </div>
                          <div className="d-flex justify-content-between align-items-center">
                            <span className="text-success">
                              🪙 Use {Math.floor((course.price_eur * course.teocoin_discount_percent) / 100)} TEO for{' '}
                              {course.teocoin_discount_percent}% discount
                            </span>
                          </div>
                        </>
                      ) : (
                        <div className="text-center">
                          <span className="text-success fw-bold">🆓 GRATUITO</span>
                          <small className="d-block text-muted">+2 TEO reward per exercise</small>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="d-grid gap-2">
                    <Button
                      variant={course.is_enrolled ? 'success' : 'primary'}
                      disabled={course.is_enrolled || purchasing === course.id}
                      onClick={() => handlePurchase(course)}
                      style={{
                        backgroundColor: course.is_enrolled ? '#00b894' : '#6c63ff',
                        borderColor: course.is_enrolled ? '#00b894' : '#6c63ff'
                      }}
                    >
                      {purchasing === course.id ? (
                        <>
                          <Spinner size="sm" className="me-2" />
                          Acquistando...
                        </>
                      ) : course.is_enrolled ? (
                        <>
                          <i className="feather icon-check me-2"></i>Già iscritto
                        </>
                      ) : (
                        <>
                          <i className="feather icon-shopping-cart me-2"></i>Acquista Corso
                        </>
                      )}
                    </Button>

                    <Button variant="outline-secondary" size="sm" onClick={() => handleExpand(course.id)}>
                      {expandedCourse === course.id ? (
                        <>
                          <i className="feather icon-chevron-up me-1"></i>Nascondi dettagli
                        </>
                      ) : (
                        <>
                          <i className="feather icon-chevron-down me-1"></i>Mostra dettagli
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Expanded Details */}
                  {expandedCourse === course.id && (
                    <div className="mt-3 pt-3 border-top">
                      <h6 className="mb-2">
                        <i className="feather icon-list me-2"></i>
                        Programma del corso
                      </h6>
                      {Array.isArray(courseLessons[course.id]) && courseLessons[course.id].length > 0 ? (
                        <ul className="list-unstyled mb-0">
                          {courseLessons[course.id].map((lesson, index) => (
                            <li key={lesson.id} className="mb-1">
                              <small className="text-muted">
                                <i className="feather icon-play-circle me-2" style={{ color: '#6c63ff' }}></i>
                                {lesson.order ? `${lesson.order}. ` : `${index + 1}. `}
                                {lesson.title}
                                {lesson.duration ? ` (${lesson.duration} min)` : ''}
                              </small>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-muted mb-0">
                          <small>
                            <i className="feather icon-info me-2"></i>
                            Programma in aggiornamento
                          </small>
                        </p>
                      )}
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          ))
        )}
      </Row>

      {/* Checkout Modal */}
      <CourseCheckoutModal
        course={selectedCourse}
        show={showCheckoutModal}
        handleClose={() => setShowCheckoutModal(false)}
        onPurchaseComplete={handlePurchaseComplete}
      />
    </div>
  );
};

export default AllCourses;
