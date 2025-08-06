import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Button, Modal, Spinner, Badge } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import './TeacherDashboard.css';
import RoleGuard from '../../components/guards/RoleGuard';

import DatabaseStaking from '../../components/staking/DatabaseStaking';
import MetaMaskDeposit from '../../components/deposit/MetaMaskDeposit';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import TeoCoinWithdrawal from '../../components/TeoCoinWithdrawal';
import StatCard from '../../components/common/StatCard';
import CoursesTable from '../../components/courses/CoursesTable';
import { fetchTeacherDashboard, fetchUserProfile } from '../../services/api/dashboard';
import { fetchLessonsForCourse, fetchExercisesForLesson } from '../../services/api/courses';
import CourseCreateModal from '../../components/modals/CourseCreateModal';
import CourseEditModal from '../../components/modals/CourseEditModal';
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
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingCourseId, setEditingCourseId] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);
  
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
        console.log('📚 Courses data:', res.data.courses);
        
        // Sanitize courses data to prevent toLowerCase errors
        const sanitizedCourses = (res.data.courses || []).map(course => ({
          ...course,
          category: course.category || 'ALTRO',
          status: course.status || course.is_approved ? 'approved' : 'pending',
          price: course.price || course.price_eur || 0,
          price_eur: course.price_eur || course.price || 0
        }));
        
        setCourses(sanitizedCourses);
        setSales(res.data.sales);
        setTransactions(res.data.transactions || []);
        console.log('📚 Courses set in state:', sanitizedCourses);
        
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
    setEditingCourseId(courseId);
    setShowEditModal(true);
  };

  const handleCourseUpdated = (courseId) => {
    // Ricarica la dashboard per mostrare i cambiamenti
    loadDashboard();
    setShowEditModal(false);
    setEditingCourseId(null);
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
    <RoleGuard allowedRoles={['teacher']}>
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



      {/* Sezione credito, burn e deposit */}
      <Row>
        <Col xs={12} md={6} lg={6} className="mb-4">
          <TeoCoinBalanceWidget 
            userProfile={userProfile} 
            onWithdrawalClick={() => setWithdrawalOpen(true)}
          />
        </Col>
        <Col xs={12} md={6} lg={6} className="mb-4">
          <MetaMaskDeposit userProfile={userProfile} />
        </Col>
      </Row>

      {/* Sezione Staking - larghezza piena su schermi grandi */}
      <Row className="mb-4">
        <Col xs={12}>
          <DatabaseStaking userProfile={userProfile} />
        </Col>
      </Row>

      {/* Tabella corsi docente */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent border-0 pb-0">
              <h5 className="card-title mb-0">I tuoi corsi</h5>
            </Card.Header>
            <Card.Body>
              <CoursesTable
                courses={courses}
                onExpandCourse={handleExpandCourse}
                expandedCourse={expandedCourse}
                courseLessons={courseLessons}
                loadingLessons={loadingLessons}
                onCreateLesson={handleShowLessonModal}
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
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Modals */}
      <CourseCreateModal 
        show={showCreateModal} 
        onHide={() => setShowCreateModal(false)} 
        onCreated={async (course) => {
          console.log('✅ Course created successfully:', course);
          setShowCreateModal(false);
          
          // Add the new course to the existing courses list instead of reloading
          setCourses(prevCourses => [...prevCourses, course]);
          
          // Optional: Refresh dashboard data if needed
          // You could also just add the course to the state without reloading
          // setTimeout(() => {
          //   window.location.reload(); // or implement a more elegant refresh
          // }, 1000);
        }}
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
      
      {/* TeoCoin Withdrawal Modal */}
      <TeoCoinWithdrawal
        open={withdrawalOpen}
        onClose={() => setWithdrawalOpen(false)}
        userBalance={userProfile?.teocoin_balance || 0}
      />
      
      {/* Course Edit Modal */}
      <CourseEditModal
        show={showEditModal}
        onHide={() => {
          setShowEditModal(false);
          setEditingCourseId(null);
        }}
        courseId={editingCourseId}
        onCourseUpdated={handleCourseUpdated}
      />
    </React.Fragment>
    </RoleGuard>
  );
};

export default TeacherDashboard;
