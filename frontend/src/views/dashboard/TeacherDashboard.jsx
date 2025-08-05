import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Button, Modal, Spinner, Badge } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import './TeacherDashboard.css';

import DatabaseStaking from '../../components/staking/DatabaseStaking';
import MetaMaskDeposit from '../../components/deposit/MetaMaskDeposit';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import StatCard from '../../components/common/StatCard';
import CoursesTable from '../../components/courses/CoursesTable';
import { fetchTeacherDashboard, fetchUserProfile } from '../../services/api/dashboard';
import { fetchLessonsForCourse, fetchExercisesForLesson } from '../../services/api/courses';
import CourseCreateModal from '../../components/modals/CourseCreateModal';
import LessonCreateModal from '../../components/modals/LessonCreateModal';
import ExerciseCreateModal from '../../components/modals/ExerciseCreateModal';
import AdvancedAnalyticsDashboard from '../../components/analytics/AdvancedAnalyticsDashboard';
import EnhancedNotificationSystem from '../../components/notifications/EnhancedNotificationSystem';

// Import dashboard styles
import './dashboard-styles.css';

// Placeholder avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

const TeacherDashboard = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [sales, setSales] = useState({ daily: 0, monthly: 0, yearly: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  
  // Course expansion and lesson management
  const [expandedCourse, setExpandedCourse] = useState(null);
  const [courseLessons, setCourseLessons] = useState({});
  const [loadingLessons, setLoadingLessons] = useState({});
  const [showLessonModal, setShowLessonModal] = useState({});
  
  // Exercise management
  const [showExerciseModal, setShowExerciseModal] = useState({});
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [lessonExercises, setLessonExercises] = useState({});
  const [loadingExercises, setLoadingExercises] = useState({});

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchTeacherDashboard();
        console.log('🔍 TeacherDashboard API Response:', res);
        setCourses(res.data.courses);
        setSales(res.data.sales);
        setTransactions(res.data.transactions || []);
        console.log('📚 Courses set in state:', res.data.courses);
        
        // Popola le lezioni da subito con i dati che arrivano dall'API
        const lessonsData = {};
        res.data.courses.forEach(course => {
          if (course.lessons && course.lessons.length > 0) {
            lessonsData[course.id] = course.lessons;
          }
        });
        setCourseLessons(lessonsData);
        console.log('📖 Lessons populated from API:', lessonsData);
        
      } catch (err) {
        console.error('Errore API dashboard:', err, err.response?.data);
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  // Course expansion handling
  const handleExpandCourse = async (courseId) => {
    if (expandedCourse === courseId) {
      setExpandedCourse(null);
      return;
    }
    
    setExpandedCourse(courseId);
    
    // Se le lezioni sono già presenti, non fare chiamata API
    if (courseLessons[courseId]) {
      console.log('📖 Lessons already loaded for course:', courseId);
      return;
    }
    
    setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
    
    try {
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
      console.log('📖 Lessons loaded from API for course:', courseId, res.data);
    } catch (err) {
      console.error('Errore caricamento lezioni:', err);
      setCourseLessons(prev => ({ ...prev, [courseId]: [] }));
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
  };

  // Lesson modal management
  const handleShowLessonModal = (courseId) => {
    setShowLessonModal(prev => ({ ...prev, [courseId]: true }));
  };
  
  const handleHideLessonModal = (courseId) => {
    setShowLessonModal(prev => ({ ...prev, [courseId]: false }));
  };
  
  const handleLessonCreated = async (courseId) => {
    // Refresh lessons for the course
    try {
      setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
    } catch (error) {
      console.error('Error refreshing lessons:', error);
      setCourseLessons(prev => ({ ...prev, [courseId]: [] }));
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
    handleHideLessonModal(courseId);
  };

  // Load exercises for a lesson
  const loadExercisesForLesson = async (lessonId) => {
    try {
      setLoadingExercises(prev => ({ ...prev, [lessonId]: true }));
      const res = await fetchExercisesForLesson(lessonId);
      setLessonExercises(prev => ({ ...prev, [lessonId]: res.data }));
    } catch (error) {
      console.error('Error loading exercises:', error);
      setLessonExercises(prev => ({ ...prev, [lessonId]: [] }));
    } finally {
      setLoadingExercises(prev => ({ ...prev, [lessonId]: false }));
    }
  };

  // Exercise management functions
  const handleShowExerciseModal = (lesson) => {
    console.log('🎯 Selected lesson for exercise creation:', lesson);
    setSelectedLesson(lesson);
    setShowExerciseModal(prev => ({ ...prev, [lesson.id]: true }));
  };

  const handleHideExerciseModal = (lessonId) => {
    setShowExerciseModal(prev => ({ ...prev, [lessonId]: false }));
    setSelectedLesson(null);
  };

  const handleExerciseCreated = async (lessonId, courseId) => {
    // Refresh lessons for the course to show updated exercise count
    try {
      setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
    } catch (error) {
      console.error('Error refreshing lessons:', error);
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
    handleHideExerciseModal(lessonId);
  };

  // Handle component updates
  const handleComponentUpdate = () => {
    // This can be used to refresh data across components
    console.log('Component data updated');
  };

  // Navigation functions
  const handleViewCourse = (courseId) => {
    navigate(`/corsi-docente/${courseId}`);
  };

  const handleViewLesson = (lessonId) => {
    navigate(`/lezioni-docente/${lessonId}`);
  };

  const handleEditCourse = (courseId) => {
    navigate(`/teacher/corsi/${courseId}/edit`);
  };

  const handleEditLesson = (lessonId) => {
    navigate(`/teacher/lezioni/${lessonId}/edit`);
  };

  const handleViewExercise = (exerciseId) => {
    navigate(`/esercizi-docente/${exerciseId}`);
  };

  const handleEditExercise = (exerciseId) => {
    navigate(`/teacher/esercizi/${exerciseId}/edit`);
  };

  // Enhanced Dashboard stats data with better calculations and icons
  const dashStatsData = [
    { 
      title: 'Corsi Attivi', 
      value: courses.length.toString(), 
      icon: 'book-open',
      percentage: Math.min(courses.length * 10, 100), // More realistic percentage
      progressColor: 'progress-c-theme',
      iconColor: 'text-primary',
      description: 'Corsi pubblicati e disponibili',
      bgGradient: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(4, 169, 245, 0.05) 100%)'
    },
    { 
      title: 'Guadagni Mensili', 
      value: `€${sales.monthly}`, 
      icon: 'trending-up',
      percentage: Math.min((sales.monthly / 1000) * 100, 100), // Percentage based on 1k target
      progressColor: 'progress-c-theme2',
      iconColor: 'text-success',
      description: 'Ricavi del mese corrente',
      bgGradient: 'linear-gradient(135deg, rgba(29, 233, 182, 0.1) 0%, rgba(29, 233, 182, 0.05) 100%)'
    },
    { 
      title: 'Fatturato Totale', 
      value: `€${sales.yearly}`, 
      icon: 'dollar-sign',
      percentage: Math.min((sales.yearly / 5000) * 100, 100), // Percentage based on 5k target
      progressColor: 'progress-c-theme3',
      iconColor: 'text-warning',
      description: 'Guadagni totali dalla piattaforma',
      bgGradient: 'linear-gradient(135deg, rgba(244, 194, 43, 0.1) 0%, rgba(244, 194, 43, 0.05) 100%)'
    }
  ];

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-12">
            <div className="card">
              <div className="card-body">
                <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                  <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Caricamento...</span>
                    </div>
                    <p className="mt-3">Caricamento dashboard...</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <React.Fragment>
      {/* 🔥 PHASE 4: Enhanced Notification System */}
      <EnhancedNotificationSystem />
      
      {/* Enhanced Welcome Section */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center py-5" style={{
              background: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(29, 233, 182, 0.1) 100%)'
            }}>
              <div className="d-flex align-items-center justify-content-center mb-3">
                <div className="avatar-lg me-3">
                  <div className="d-flex align-items-center justify-content-center bg-primary rounded-circle text-white" style={{ width: '70px', height: '70px' }}>
                    <i className="feather icon-award" style={{ fontSize: '2rem' }} />
                  </div>
                </div>
                <div className="text-start">
                  <h2 className="fw-bold mb-1 text-dark">
                    Benvenuto, {userProfile?.first_name || userProfile?.username || 'Insegnante'}!
                  </h2>
                  <p className="text-muted mb-0">Gestisci i tuoi corsi e monitora le tue performance</p>
                </div>
              </div>
              
              {/* Quick Action Buttons */}
              <div className="d-flex gap-3 justify-content-center flex-wrap mt-4">
                <Button 
                  variant="primary" 
                  className="rounded-pill px-4 py-2"
                  onClick={() => setShowCreateModal(true)}
                >
                  <i className="feather icon-plus me-2"></i>
                  Nuovo Corso
                </Button>
                {courses.length > 0 && (
                  <Button 
                    variant="outline-primary" 
                    className="rounded-pill px-4 py-2"
                    onClick={() => handleViewCourse(courses[0].id)}
                  >
                    <i className="feather icon-edit me-2"></i>
                    Gestisci Corsi
                  </Button>
                )}
                <Link to="/profilo" className="btn btn-outline-secondary rounded-pill px-4 py-2">
                  <i className="feather icon-settings me-2"></i>
                  Profilo
                </Link>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Enhanced Stats Cards */}
      <Row>
        {dashStatsData.map((data, index) => (
          <Col key={index} md={6} xl={4}>
            <Card className="dashboard-stat-card border-0 shadow-sm h-100">
              <Card.Body style={{ background: data.bgGradient }}>
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <div className="stat-icon">
                    <i className={`feather icon-${data.icon} ${data.iconColor}`} style={{ fontSize: '2.5rem' }} />
                  </div>
                  <div className="text-end">
                    <h3 className="mb-0 fw-bold text-dark">{data.value}</h3>
                    <small className="text-muted">{data.percentage}% obiettivo</small>
                  </div>
                </div>
                <h6 className="mb-2 fw-semibold text-dark">{data.title}</h6>
                <p className="text-muted mb-3 small">{data.description}</p>
                <div className="progress mb-0" style={{ height: '6px' }}>
                  <div
                    className={`progress-bar ${data.progressColor}`}
                    role="progressbar"
                    style={{ width: data.percentage + '%' }}
                    aria-valuenow={data.percentage}
                    aria-valuemin="0"
                    aria-valuemax="100"
                  />
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Teacher Analytics & Insights */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-transparent">
              <Card.Title as="h5" className="mb-0">
                <i className="feather icon-bar-chart-2 text-primary me-2"></i>
                Performance dei Corsi
              </Card.Title>
              <small className="text-muted">Analisi delle vendite e engagement</small>
            </Card.Header>
            <Card.Body>
              {courses.length > 0 ? (
                <div className="course-performance">
                  {courses.slice(0, 3).map((course, index) => {
                    const enrollmentRate = Math.random() * 100; // Mock data - replace with real metrics
                    const completionRate = Math.random() * 100;
                    
                    return (
                      <div key={course.id} className="performance-item d-flex align-items-center mb-4">
                        <div className="performance-indicator me-3">
                          <div className={`rounded-circle d-flex align-items-center justify-content-center ${
                            index === 0 ? 'bg-primary' : index === 1 ? 'bg-success' : 'bg-warning'
                          }`} style={{ width: '45px', height: '45px' }}>
                            <i className="feather icon-book-open text-white"></i>
                          </div>
                        </div>
                        <div className="flex-grow-1">
                          <h6 className="mb-2 fw-semibold">{course.title}</h6>
                          <div className="performance-metrics row g-2">
                            <div className="col-6">
                              <small className="text-muted d-block">Iscrizioni</small>
                              <div className="progress mb-1" style={{ height: '4px' }}>
                                <div className="progress-bar bg-primary" style={{ width: `${enrollmentRate}%` }}></div>
                              </div>
                              <small className="fw-bold text-primary">{Math.round(enrollmentRate)}%</small>
                            </div>
                            <div className="col-6">
                              <small className="text-muted d-block">Completamento</small>
                              <div className="progress mb-1" style={{ height: '4px' }}>
                                <div className="progress-bar bg-success" style={{ width: `${completionRate}%` }}></div>
                              </div>
                              <small className="fw-bold text-success">{Math.round(completionRate)}%</small>
                            </div>
                          </div>
                        </div>
                        <div className="text-end">
                          <div className="performance-actions">
                            <Button 
                              variant="outline-primary" 
                              size="sm"
                              onClick={() => handleViewCourse(course.id)}
                            >
                              <i className="feather icon-eye"></i>
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-4">
                  <i className="feather icon-bar-chart text-muted" style={{ fontSize: '3rem' }}></i>
                  <p className="text-muted mt-3">Crea il tuo primo corso per vedere le analytics</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-transparent">
              <Card.Title as="h6" className="mb-0">
                <i className="feather icon-target text-success me-2"></i>
                Obiettivi Mensili
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="teacher-goals mb-4">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Nuovi studenti</span>
                  <span className="small text-primary fw-bold">8/15</span>
                </div>
                <div className="progress mb-3" style={{ height: '8px' }}>
                  <div className="progress-bar bg-primary" style={{ width: '53%' }}></div>
                </div>
                
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Corsi pubblicati</span>
                  <span className="small text-success fw-bold">{courses.length}/3</span>
                </div>
                <div className="progress mb-3" style={{ height: '8px' }}>
                  <div className="progress-bar bg-success" style={{ width: `${Math.min((courses.length/3)*100, 100)}%` }}></div>
                </div>
                
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Revenue target</span>
                  <span className="small text-warning fw-bold">€{sales.monthly}/€1000</span>
                </div>
                <div className="progress" style={{ height: '8px' }}>
                  <div className="progress-bar bg-warning" style={{ width: `${Math.min((sales.monthly/1000)*100, 100)}%` }}></div>
                </div>
              </div>
              
              <div className="text-center">
                <small className="text-muted">
                  <i className="feather icon-calendar me-1"></i>
                  Aggiornato al {new Date().toLocaleDateString('it-IT')}
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Error Alert */}
      {error && (
        <Row>
          <Col md={12}>
            <Card className="bg-danger text-white">
              <Card.Body>
                <i className="feather icon-alert-triangle me-2"></i>
                {error}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Content Row */}
      <Row>
        {/* Full Width Column - following StudentDashboard layout */}
        <Col lg={12} className="mb-4">
          {/* 💰 SEPARATED TEOCOIN SYSTEMS */}
          <div className="mb-4">
            <h4 className="mb-3">
              <i className="feather icon-layers me-2 text-primary"></i>
              TeoCoin Management
              <Badge bg="info" className="ms-2">Teacher Features</Badge>
            </h4>
            <div className="alert alert-info">
              <i className="feather icon-info me-2"></i>
              <strong>Teacher Benefits:</strong> 
              Stake your TEO to reduce platform commission rates and increase your earnings. 
              Deposits/withdrawals handle MetaMask ↔ Platform transfers.
            </div>
          </div>

          {/* Separated TeoCoin Components - Database Staking & MetaMask Operations */}
          <Row className="mb-4">
            {/* Database Staking - Virtual staking system */}
            <Col lg={6} className="mb-4">
              <DatabaseStaking 
                onBalanceUpdate={handleComponentUpdate}
              />
            </Col>
            
            {/* MetaMask Deposit - MetaMask to Platform */}
            <Col lg={6} className="mb-4">
              <MetaMaskDeposit 
                onDepositComplete={handleComponentUpdate}
              />
            </Col>
          </Row>

          {/* TeoCoin Balance Widget */}
          <Row className="mb-4">
            <Col lg={12}>
              <TeoCoinBalanceWidget />
            </Col>
          </Row>

          {/* Removed TeacherDiscountDashboard and TeacherDiscountAbsorptionDashboard as they are not relevant for teachers */}

          {/* Courses Management Section */}
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <Card.Title as="h5">
                <i className="feather icon-book me-2"></i>
                I Miei Corsi
              </Card.Title>
              <Button 
                variant="primary" 
                size="sm"
                onClick={() => setShowCreateModal(true)}
              >
                <i className="feather icon-plus me-1"></i>
                Nuovo Corso
              </Button>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-4">
                  <i className="feather icon-book" style={{ fontSize: '3rem', color: '#999', marginBottom: '1rem' }}></i>
                  <h4 className="mb-3">Nessun corso creato</h4>
                  <p className="text-muted mb-4">Inizia creando il tuo primo corso</p>
                  <Button 
                    variant="primary"
                    onClick={() => setShowCreateModal(true)}
                  >
                    <i className="feather icon-plus me-2"></i>
                    Crea Primo Corso
                  </Button>
                </div>
              ) : (
                <CoursesTable
                  courses={courses}
                  showActions={true}
                  onCreateLesson={handleShowLessonModal}
                  expandedCourse={expandedCourse}
                  onExpandCourse={handleExpandCourse}
                  courseLessons={courseLessons}
                  loadingLessons={loadingLessons}
                  onCreateExercise={handleShowExerciseModal}
                  lessonExercises={lessonExercises}
                  loadingExercises={loadingExercises}
                  onLoadExercises={loadExercisesForLesson}
                  onViewCourse={handleViewCourse}
                  onViewLesson={handleViewLesson}
                  onEditCourse={handleEditCourse}
                  onEditLesson={handleEditLesson}
                  onViewExercise={handleViewExercise}
                  onEditExercise={handleEditExercise}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* 🔥 PHASE 4: Advanced Analytics */}
      <Row className="mb-4">
        <Col lg={12}>
          <AdvancedAnalyticsDashboard />
        </Col>
      </Row>

      {/* Modals */}
      <CourseCreateModal 
        show={showCreateModal} 
        onHide={() => setShowCreateModal(false)} 
      />
      
      {/* Lesson Creation Modals */}
      {Object.keys(showLessonModal).map(courseId => (
        <LessonCreateModal
          key={`lesson-${courseId}`}
          show={showLessonModal[courseId]}
          onHide={() => handleHideLessonModal(courseId)}
          courseId={courseId}
          onCreated={() => handleLessonCreated(courseId)}
        />
      ))}
      
      {/* Exercise Creation Modals */}
      {Object.keys(showExerciseModal).map(lessonId => (
        <ExerciseCreateModal
          key={`exercise-${lessonId}`}
          show={showExerciseModal[lessonId]}
          onHide={() => handleHideExerciseModal(lessonId)}
          lessonId={selectedLesson?.id}
          courseId={selectedLesson?.course_id || selectedLesson?.course}
          lesson={selectedLesson}
          onCreated={() => handleExerciseCreated(lessonId, selectedLesson?.course_id || selectedLesson?.course)}
        />
      ))}
    </React.Fragment>
  );
};

export default TeacherDashboard;
