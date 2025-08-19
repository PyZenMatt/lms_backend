/* @ts-nocheck */
import React, { useEffect, useState } from 'react';
import { Spinner } from '@/components/ui';
import { Card, CardHeader, CardContent, CardFooter } from '../../components/ui/ui-legacy/Card';
import { Button } from '../../components/ui/ui-legacy/Button';
import { Alert } from '../../components/ui/ui-legacy/Alert';
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
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-12">
            <Card>
              <CardHeader className="text-center py-5">
                <h2 className="font-bold mb-1 text-primary-foreground">Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!</h2>
                <p className="text-muted-foreground mb-0">Continua il tuo percorso di apprendimento artistico</p>
              </CardHeader>
            </Card>
          </div>
        </div>

        {!!error && (
          <div className="grid grid-cols-12 gap-4 mb-3">
            <div className="col-span-12 md:col-span-12">
              <Alert variant="destructive">{error}</Alert>
            </div>
          </div>
        )}

        {/* Widget TeoCoin: Balance, Burn/Deposit, Quick Actions */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-6">
            <TeoCoinBalanceWidget onWithdrawalClick={() => setWithdrawalOpen(true)} variant="student" />
          </div>
          <div className="col-span-12 md:col-span-6">
            <BurnDepositInterface />
          </div>
        </div>

        {/* Pending Withdrawals Manager */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-12">
            <PendingWithdrawalsManager />
          </div>
        </div>

        {/* Lista corsi e TeoCoin Activity */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-8">
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
          </div>
          <div className="col-span-12 md:col-span-4">
            <TeoCoinTransactionHistory limit={5} />
          </div>
        </div>

        {/* TeoCoin Journey Statistics */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-12">
            <StudentTeoCoinStats />
          </div>
        </div>

        {/* Peer Review assegnate (widget) */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-12 md:col-span-12">
            <StudentAssignedReviewsWidget />
          </div>
        </div>

        {/* Lista esercizi (StudentSubmissions) */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-12 md:col-span-12">
            <Card>
              <CardHeader>
                <h5 className="mb-1">I Tuoi Esercizi</h5>
              </CardHeader>
              <CardContent>
                <StudentSubmissions />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* TeoCoin Withdrawal Modal */}
        <TeoCoinWithdrawal open={withdrawalOpen} onClose={() => setWithdrawalOpen(false)} userBalance={userProfile?.teocoin_balance || 0} />
      </>
    </RoleGuard>
  );
};

export default StudentDashboard;
