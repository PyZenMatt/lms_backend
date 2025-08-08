import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import RoleGuard from '../../components/guards/RoleGuard';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import BurnDepositInterface from '../../components/blockchain/BurnDepositInterface';
import TeoCoinWithdrawal from '../../components/TeoCoinWithdrawal';
import TeoCoinTransactionHistory from '../../components/TeoCoinTransactionHistory';
import StudentTeoCoinStats from '../../components/StudentTeoCoinStats';
import PendingWithdrawalsManager from '../../components/PendingWithdrawalsManager';
import StudentSubmissions from './StudentSubmissions';
import { fetchStudentDashboard, fetchUserProfile } from '../../services/api/dashboard';
import StudentAssignedReviewsWidget from '../../components/review/StudentAssignedReviewsWidget';


const StudentDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);
  // const [refreshKey, setRefreshKey] = useState(0); // For refreshing components after withdrawal changes

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        console.log('🔄 Loading student dashboard data...');
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        const res = await fetchStudentDashboard();
        console.log('📚 Dashboard courses loaded:', res.data.courses?.length || 0);
        setCourses(res.data.courses || []);
      } catch (err) {
        console.error('❌ Error loading dashboard:', err);
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  // Add automatic refresh when page becomes visible (e.g., user returns from course purchase)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('👁️ Page became visible, refreshing dashboard...');
        const refreshDashboard = async () => {
          try {
            const res = await fetchStudentDashboard();
            console.log('🔄 Dashboard refreshed, courses:', res.data.courses?.length || 0);
            setCourses(res.data.courses || []);
          } catch (err) {
            console.error('❌ Error refreshing dashboard:', err);
          }
        };
        refreshDashboard();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Manual refresh function
  const handleRefreshDashboard = async () => {
    setLoading(true);
    try {
      console.log('🔄 Manual refresh triggered...');
      const res = await fetchStudentDashboard();
      console.log('📚 Courses reloaded:', res.data.courses?.length || 0);
      setCourses(res.data.courses || []);
    } catch (err) {
  console.error('❌ Error refreshing dashboard:', err);
  setError("Errore durante l'aggiornamento");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Caricamento...</span>
        </div>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['student']}>
      <>
        {/* Hero di benvenuto */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center py-5">
              <h2 className="fw-bold mb-1 text-dark">Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!</h2>
              <p className="text-muted mb-0">Continua il tuo percorso di apprendimento artistico</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {!!error && (
        <Row className="mb-3">
          <Col md={12}>
            <Alert variant="danger">{error}</Alert>
          </Col>
        </Row>
      )}


      {/* Widget TeoCoin: Balance, Burn/Deposit, Quick Actions */}
      <Row className="mb-4">
        <Col md={6}>
          <TeoCoinBalanceWidget onWithdrawalClick={() => setWithdrawalOpen(true)} variant="student" />
        </Col>
        <Col md={6}>
          <BurnDepositInterface />
        </Col>
      </Row>

      {/* Pending Withdrawals Manager */}
      <Row className="mb-4">
        <Col md={12}>
          <PendingWithdrawalsManager />
        </Col>
      </Row>

      {/* Lista corsi e TeoCoin Activity */}
      <Row className="mb-4">
        <Col md={8}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-light border-0">
              <div className="d-flex justify-content-between align-items-center">
                <Card.Title as="h5" className="mb-0">
                  I Tuoi Corsi ({courses.length})
                </Card.Title>
                <Button 
                  variant="outline-primary" 
                  size="sm" 
                  onClick={handleRefreshDashboard}
                  disabled={loading}
                  title="Aggiorna elenco corsi"
                >
                  {loading ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <i className="feather icon-refresh-cw"></i>
                  )}
                </Button>
              </div>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-4">
                  <i className="feather icon-book-open text-muted" style={{ fontSize: '3rem' }}></i>
                  <p className="text-muted mt-3">Nessun corso acquistato</p>
                </div>
              ) : (
                <div className="row g-3">
                  {courses.map(course => (
                    <div key={course.id} className="col-12">
                      <div className="card border-0 shadow-sm">
                        <div className="card-body">
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <h6 className="card-title mb-2">{course.title}</h6>
                              <div className="d-flex align-items-center text-muted small mb-2">
                                <i className="feather icon-play-circle me-1"></i>
                                <span>{course.lessons?.length || 0} lezioni disponibili</span>
                                <span className="mx-2">•</span>
                                <i className="feather icon-user me-1"></i>
                                <span>Docente: {course.teacher?.first_name || course.teacher?.username}</span>
                              </div>
                              {course.description && (
                                <p className="text-muted small mb-0" style={{
                                  display: '-webkit-box',
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden'
                                }}>
                                  {course.description}
                                </p>
                              )}
                            </div>
                            <Link to={`/corsi/${course.id}`} className="btn btn-sm btn-primary ms-3">
                              <i className="feather icon-arrow-right me-1"></i>
                              Inizia
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <TeoCoinTransactionHistory limit={5} />
        </Col>
      </Row>

      {/* TeoCoin Journey Statistics */}
      <Row className="mb-4">
        <Col md={12}>
          <StudentTeoCoinStats />
        </Col>
      </Row>

      {/* Peer Review assegnate (widget) */}
      <Row className="mb-4">
        <Col md={12}>
          <StudentAssignedReviewsWidget />
        </Col>
      </Row>

      {/* Lista esercizi (StudentSubmissions) */}
      <Row>
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-light border-0">
              <Card.Title as="h5" className="mb-1">
                I Tuoi Esercizi
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <StudentSubmissions />
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* TeoCoin Withdrawal Modal */}
      <TeoCoinWithdrawal
        open={withdrawalOpen}
        onClose={() => setWithdrawalOpen(false)}
        userBalance={userProfile?.teocoin_balance || 0}
      />
    </>
    </RoleGuard>
  );
};

export default StudentDashboard;
