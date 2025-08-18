import React, { useEffect, useState } from 'react';
import { Row, Col, Spinner } from '@/components/ui';
import { Card, CardHeader, CardContent, CardFooter } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
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
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['student']}>
      <>
        {/* Hero di benvenuto */}
        <Row className="mb-4">
          <Col md={12}>
            <Card>
              <CardHeader className="text-center py-5">
                <h2 className="font-bold mb-1 text-primary-foreground">Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!</h2>
                <p className="text-muted-foreground mb-0">Continua il tuo percorso di apprendimento artistico</p>
              </CardHeader>
            </Card>
          </Col>
        </Row>

        {!!error && (
          <Row className="mb-3">
            <Col md={12}>
              <Alert variant="destructive">{error}</Alert>
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
            <Card>
              <CardHeader className="flex justify-between items-center">
                <h5 className="mb-0">I Tuoi Corsi ({courses.length})</h5>
                <Button variant="outline" size="sm" onClick={handleRefreshDashboard} disabled={loading} title="Aggiorna elenco corsi">
                  {loading ? <Spinner animation="border" size="sm" /> : <i className="feather icon-refresh-cw"></i>}
                </Button>
              </CardHeader>
              <CardContent>
                {courses.length === 0 ? (
                  <div className="text-center py-4">
                    <i className="feather icon-book-open text-muted-foreground" style={{ fontSize: '3rem' }}></i>
                    <p className="text-muted-foreground mt-3">Nessun corso acquistato</p>
                  </div>
                ) : (
                  <div className="grid gap-3">
                    {courses.map((course) => (
                      <div key={course.id} className="w-full">
                        <Card>
                          <CardContent>
                            <div className="flex justify-between items-start">
                              <div className="flex-grow">
                                <h6 className="mb-2">{course.title}</h6>
                                <div className="flex items-center text-muted-foreground text-sm mb-2">
                                  <i className="feather icon-play-circle mr-1"></i>
                                  <span>{course.lessons?.length || 0} lezioni disponibili</span>
                                  <span className="mx-2">•</span>
                                  <i className="feather icon-user mr-1"></i>
                                  <span>Docente: {course.teacher?.first_name || course.teacher?.username}</span>
                                </div>
                                {course.description && (
                                  <p
                                    className="text-muted-foreground text-sm mb-0 line-clamp-2"
                                  >
                                    {course.description}
                                  </p>
                                )}
                              </div>
                              <Button variant="primary" size="sm" className="ml-3" as={Link} to={`/corsi/${course.id}`}>
                                <i className="feather icon-arrow-right mr-1"></i>
                                Inizia
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
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
            <Card>
              <CardHeader>
                <h5 className="mb-1">I Tuoi Esercizi</h5>
              </CardHeader>
              <CardContent>
                <StudentSubmissions />
              </CardContent>
            </Card>
          </Col>
        </Row>

        {/* TeoCoin Withdrawal Modal */}
        <TeoCoinWithdrawal open={withdrawalOpen} onClose={() => setWithdrawalOpen(false)} userBalance={userProfile?.teocoin_balance || 0} />
      </>
    </RoleGuard>
  );
};

export default StudentDashboard;
