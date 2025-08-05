import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Tabs, Tab, ProgressBar } from 'react-bootstrap';
import { Link } from 'react-router-dom';

import WalletBalanceDisplay from '../../components/blockchain/WalletBalanceDisplay';
import ProfileWalletDisplay from '../../components/blockchain/ProfileWalletDisplay';
import StudentTeoCoinDashboard from '../../components/blockchain/DBStudentTeoCoinDashboard';
import RewardNotifications from '../../components/blockchain/RewardNotifications';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import { fetchStudentDashboard, fetchUserProfile } from '../../services/api/dashboard';
import StudentSubmissions from './StudentSubmissions';

// Import dashboard styles
import './dashboard-styles.css';

// Placeholder avatar - you may want to use actual user avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

// Helper functions for course cards
const getLevelBadgeClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'beginner':
      return 'bg-success';
    case 'intermediate':
      return 'bg-warning';
    case 'advanced':
      return 'bg-danger';
    default:
      return 'bg-primary';
  }
};

const calculateCourseProgress = (course) => {
  if (!course.lessons_count || course.lessons_count === 0) return 0;
  const completed = course.completed_lessons || 0;
  return Math.round((completed / course.lessons_count) * 100);
};

const StudentDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [stats, setStats] = useState({
    totalCourses: 0,
    completedLessons: 0,
    activeBadges: 0
  });

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchStudentDashboard();
        setCourses(res.data.courses || []);
        
        console.log('Corsi caricati:', res.data.courses);
        
        setTransactions(res.data.recent_transactions || []);
        
        // Calculate stats
        setStats({
          totalCourses: res.data.courses?.length || 0,
          completedLessons: res.data.completed_lessons || 0,
          activeBadges: res.data.badges?.length || 0
        });
      } catch (err) {
        console.error('Errore API dashboard:', err, err.response?.data);
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  // Enhanced Dashboard stats data with better icons and calculations
  const dashStatsData = [
    { 
      title: 'Corsi Attivi', 
      amount: stats.totalCourses.toString(), 
      icon: 'book-open',
      iconColor: 'text-primary',
      value: Math.min(stats.totalCourses * 25, 100), // More realistic progress calculation
      class: 'progress-c-theme',
      description: 'Corsi acquistati e disponibili',
      bgGradient: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(4, 169, 245, 0.05) 100%)'
    },
    { 
      title: 'Progresso Totale', 
      amount: stats.completedLessons.toString(), 
      icon: 'trending-up',
      iconColor: 'text-success',
      value: courses.length > 0 ? Math.round((stats.completedLessons / courses.reduce((total, course) => total + (course.lessons_count || 0), 0)) * 100) : 0, 
      class: 'progress-c-theme2',
      description: 'Lezioni completate',
      bgGradient: 'linear-gradient(135deg, rgba(29, 233, 182, 0.1) 0%, rgba(29, 233, 182, 0.05) 100%)'
    },
    { 
      title: 'Obiettivi Raggiunti', 
      amount: stats.activeBadges.toString(), 
      icon: 'award',
      iconColor: 'text-warning',
      value: Math.min(stats.activeBadges * 20, 100), // Badge progress
      class: 'progress-c-theme3',
      description: 'Badge e achievement',
      bgGradient: 'linear-gradient(135deg, rgba(244, 194, 43, 0.1) 0%, rgba(244, 194, 43, 0.05) 100%)'
    }
  ];

  if (loading) {
    return (
      <div className="pcoded-content">
        <div className="pcoded-inner-content">
          <div className="main-body">
            <div className="page-wrapper">
              <div className="page-body">
                <div className="row">
                  <div className="col-md-12">
                    <div className="card">
                      <div className="card-body text-center">
                        <div className="spinner-border text-primary" role="status">
                          <span className="sr-only">Caricamento...</span>
                        </div>
                        <p className="mt-3">Caricamento dashboard...</p>
                      </div>
                    </div>
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
      {/* Welcome Section */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center py-5" style={{
              background: 'linear-gradient(135deg, rgba(4, 169, 245, 0.1) 0%, rgba(29, 233, 182, 0.1) 100%)'
            }}>
              <div className="d-flex align-items-center justify-content-center mb-3">
                <div className="avatar-lg me-3">
                  <div className="d-flex align-items-center justify-content-center bg-primary rounded-circle text-white" style={{ width: '70px', height: '70px' }}>
                    <i className="feather icon-user" style={{ fontSize: '2rem' }} />
                  </div>
                </div>
                <div className="text-start">
                  <h2 className="fw-bold mb-1 text-dark">
                    Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!
                  </h2>
                  <p className="text-muted mb-0">Continua il tuo percorso di apprendimento artistico</p>
                </div>
              </div>
              
              {/* Quick Action Buttons */}
              <div className="d-flex gap-3 justify-content-center flex-wrap mt-4">
                <Link to="/corsi" className="btn btn-primary rounded-pill px-4 py-2">
                  <i className="feather icon-search me-2"></i>
                  Esplora Corsi
                </Link>
                {courses.length > 0 && (
                  <Link to={`/corsi/${courses[0].id}`} className="btn btn-outline-primary rounded-pill px-4 py-2">
                    <i className="feather icon-play-circle me-2"></i>
                    Continua Ultimo
                  </Link>
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
        {dashStatsData.map((data, index) => {
          return (
            <Col key={index} md={6} xl={4}>
              <Card className="dashboard-stat-card border-0 shadow-sm h-100">
                <Card.Body style={{ background: data.bgGradient }}>
                  <div className="d-flex align-items-center justify-content-between mb-3">
                    <div className="stat-icon">
                      <i className={`feather icon-${data.icon} ${data.iconColor}`} style={{ fontSize: '2.5rem' }} />
                    </div>
                    <div className="text-end">
                      <h3 className="mb-0 fw-bold text-dark">{data.amount}</h3>
                      <small className="text-muted">{data.value}% completo</small>
                    </div>
                  </div>
                  <h6 className="mb-2 fw-semibold text-dark">{data.title}</h6>
                  <p className="text-muted mb-3 small">{data.description}</p>
                  <div className="progress mb-0" style={{ height: '6px' }}>
                    <div
                      className={`progress-bar ${data.class}`}
                      role="progressbar"
                      style={{ width: data.value + '%' }}
                      aria-valuenow={data.value}
                      aria-valuemin="0"
                      aria-valuemax="100"
                    />
                  </div>
                </Card.Body>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* Recent Activities & Learning Insights */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card className="border-0 shadow-sm h-100">
            <Card.Header className="border-0 bg-transparent">
              <Card.Title as="h5" className="mb-0">
                <i className="feather icon-activity text-primary me-2"></i>
                Attività Recenti
              </Card.Title>
              <small className="text-muted">Le tue ultime interazioni con i corsi</small>
            </Card.Header>
            <Card.Body>
              {courses.length > 0 ? (
                <div className="activity-timeline">
                  {courses.slice(0, 3).map((course, index) => (
                    <div key={course.id} className="d-flex align-items-center mb-3">
                      <div className="activity-indicator me-3">
                        <div className={`rounded-circle d-flex align-items-center justify-content-center ${
                          index === 0 ? 'bg-primary' : index === 1 ? 'bg-success' : 'bg-warning'
                        }`} style={{ width: '40px', height: '40px' }}>
                          <i className={`feather ${
                            calculateCourseProgress(course) > 0 ? 'icon-play-circle' : 'icon-book-open'
                          } text-white`}></i>
                        </div>
                      </div>
                      <div className="flex-grow-1">
                        <h6 className="mb-1 fw-semibold">{course.title}</h6>
                        <p className="text-muted mb-0 small">
                          {calculateCourseProgress(course) > 0 ? 
                            `Progresso: ${calculateCourseProgress(course)}%` : 
                            'Pronto per iniziare'
                          }
                        </p>
                      </div>
                      <div className="text-end">
                        <Link to={`/corsi/${course.id}`} className="btn btn-sm btn-outline-primary">
                          <i className="feather icon-arrow-right"></i>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <i className="feather icon-activity text-muted" style={{ fontSize: '3rem' }}></i>
                  <p className="text-muted mt-3">Inizia il tuo primo corso per vedere le attività qui</p>
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
                Obiettivi Settimanali
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="goal-progress mb-4">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Lezioni da completare</span>
                  <span className="small text-primary fw-bold">3/5</span>
                </div>
                <div className="progress mb-3" style={{ height: '8px' }}>
                  <div className="progress-bar bg-primary" style={{ width: '60%' }}></div>
                </div>
                
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Esercizi da completare</span>
                  <span className="small text-success fw-bold">2/3</span>
                </div>
                <div className="progress mb-3" style={{ height: '8px' }}>
                  <div className="progress-bar bg-success" style={{ width: '67%' }}></div>
                </div>
                
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small fw-semibold">Minuti di studio</span>
                  <span className="small text-warning fw-bold">45/60</span>
                </div>
                <div className="progress" style={{ height: '8px' }}>
                  <div className="progress-bar bg-warning" style={{ width: '75%' }}></div>
                </div>
              </div>
              
              <div className="text-center">
                <small className="text-muted">
                  <i className="feather icon-calendar me-1"></i>
                  Resetta ogni lunedì
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

      {/* Reward Notifications */}
      <RewardNotifications />

      {/* TeoCoin Components - Enhanced Layout */}
      <Row className="mb-4">
        <Col lg={8} className="mb-4">
          {/* Enhanced TeoCoin Dashboard - Main */}
          <StudentTeoCoinDashboard />
        </Col>
        <Col lg={4} className="mb-4">
          {/* TeoCoin Withdrawal Widget - Sidebar */}
          <TeoCoinBalanceWidget />
        </Col>
      </Row>

      {/* Main Content Row */}
      <Row>
        {/* Full Width Column */}
        <Col lg={12} className="mb-4">

          {/* Enhanced Courses Section */}
          <Card className="border-0 shadow-sm mb-4">
            <Card.Header className="border-0 bg-light">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <Card.Title as="h5" className="mb-1">
                    <i className="feather icon-book text-primary me-2"></i>
                    I Tuoi Corsi ({courses.length})
                  </Card.Title>
                  <small className="text-muted">Gestisci e continua i tuoi corsi</small>
                </div>
                <Link to="/corsi" className="btn btn-outline-primary btn-sm">
                  <i className="feather icon-plus me-1"></i>
                  Acquista Corso
                </Link>
              </div>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-5">
                  <div className="empty-state">
                    <i className="feather icon-book-open text-muted mb-3" style={{ fontSize: '4rem' }}></i>
                    <h4 className="mb-3 text-dark">Nessun corso acquistato</h4>
                    <p className="text-muted mb-4 px-3">
                      Inizia il tuo percorso di apprendimento artistico acquistando il tuo primo corso. 
                      Scopri corsi di disegno, pittura, scultura e molto altro!
                    </p>
                    <div className="d-flex gap-2 justify-content-center flex-wrap">
                      <Link to="/corsi" className="btn btn-primary px-4">
                        <i className="feather icon-search me-2"></i>
                        Esplora Corsi
                      </Link>
                      <Link to="/corsi?categoria=disegno" className="btn btn-outline-primary px-4">
                        <i className="feather icon-edit me-2"></i>
                        Corsi di Disegno
                      </Link>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="row g-4">
                  {courses.map(course => (
                    <div key={course.id} className="col-12 col-lg-6">
                      <Card className="course-card border-0 shadow-sm h-100" style={{
                        transition: 'all 0.3s ease',
                        cursor: 'pointer'
                      }} 
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
                      }}>
                        <Card.Body className="p-4">
                          {/* Enhanced Header */}
                          <div className="d-flex justify-content-between align-items-start mb-3">
                            <div className="flex-grow-1">
                              <div className="d-flex align-items-center gap-2 mb-2">
                                <h6 className="course-title mb-0 fw-bold text-dark">{course.title}</h6>
                                <span className={`badge ${getLevelBadgeClass(course.level || 'Beginner')} rounded-pill`}>
                                  {course.level || 'Beginner'}
                                </span>
                              </div>
                              <div className="d-flex align-items-center gap-3 text-muted small">
                                <span>
                                  <i className="feather icon-calendar me-1"></i>
                                  {course.created_at ? new Date(course.created_at).toLocaleDateString('it-IT') : 'N/A'}
                                </span>
                                <span className="text-primary fw-bold">{course.price} TEO</span>
                              </div>
                            </div>
                          </div>

                          {/* Enhanced Description */}
                          <p className="course-description text-muted mb-3" style={{ 
                            minHeight: '45px',
                            lineHeight: '1.5'
                          }}>
                            {course.description && course.description.length > 100 
                              ? course.description.substring(0, 100) + '...' 
                              : course.description}
                          </p>

                          {/* Enhanced Progress section */}
                          <div className="progress-section mb-3">
                            <div className="d-flex justify-content-between align-items-center mb-2">
                              <span className="small fw-semibold text-dark">Progresso del corso</span>
                              <div className="d-flex align-items-center gap-2">
                                <span className="small text-primary fw-bold">
                                  {calculateCourseProgress(course)}%
                                </span>
                                {calculateCourseProgress(course) === 100 && (
                                  <i className="feather icon-check-circle text-success" title="Corso completato"></i>
                                )}
                              </div>
                            </div>
                            <div className="progress mb-3" style={{ height: '8px' }}>
                              <div 
                                className={`progress-bar ${calculateCourseProgress(course) === 100 ? 'bg-success' : 'bg-primary'}`}
                                role="progressbar" 
                                style={{ width: `${calculateCourseProgress(course)}%` }}
                                aria-valuenow={calculateCourseProgress(course)} 
                                aria-valuemin="0" 
                                aria-valuemax="100"
                              ></div>
                            </div>
                          </div>

                          {/* Enhanced Stats */}
                          <div className="course-stats row g-2 mb-4">
                            <div className="col-4">
                              <div className="stat-box text-center p-2 bg-light rounded">
                                <div className="fw-bold text-primary">{course.lessons_count || 0}</div>
                                <div className="text-muted small">Lezioni</div>
                              </div>
                            </div>
                            <div className="col-4">
                              <div className="stat-box text-center p-2 bg-light rounded">
                                <div className="fw-bold text-success">{course.exercises_count || 0}</div>
                                <div className="text-muted small">Esercizi</div>
                              </div>
                            </div>
                            <div className="col-4">
                              <div className="stat-box text-center p-2 bg-light rounded">
                                <div className="fw-bold text-warning">{course.completed_lessons || 0}</div>
                                <div className="text-muted small">Completate</div>
                              </div>
                            </div>
                          </div>

                          {/* Enhanced Action buttons */}
                          <div className="d-grid gap-2">
                            <Link 
                              to={`/corsi/${course.id}`} 
                              className={`btn ${calculateCourseProgress(course) > 0 ? 'btn-primary' : 'btn-outline-primary'} d-flex align-items-center justify-content-center`}
                            >
                              <i className={`feather ${calculateCourseProgress(course) > 0 ? 'icon-play-circle' : 'icon-play'} me-2`}></i>
                              {calculateCourseProgress(course) === 100 ? 'Rivedi Corso' : 
                               calculateCourseProgress(course) > 0 ? 'Continua Corso' : 'Inizia Corso'}
                            </Link>
                          </div>
                        </Card.Body>
                      </Card>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Enhanced Student Submissions */}
          <Card className="border-0 shadow-sm">
            <Card.Header className="border-0 bg-light">
              <Card.Title as="h5" className="mb-1">
                <i className="feather icon-file-text text-primary me-2"></i>
                I Tuoi Esercizi
              </Card.Title>
              <small className="text-muted">Gestisci le tue sottomissioni e feedback</small>
            </Card.Header>
            <Card.Body>
              <StudentSubmissions />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </React.Fragment>
  );
};

export default StudentDashboard;
