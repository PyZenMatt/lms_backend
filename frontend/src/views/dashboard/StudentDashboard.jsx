
import React, { useEffect, useState } from 'react';
import { Row, Col, Card } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import BurnDepositInterface from '../../components/blockchain/BurnDepositInterface';
import TeoCoinWithdrawal from '../../components/TeoCoinWithdrawal';
import StudentSubmissions from './StudentSubmissions';
import { fetchStudentDashboard, fetchUserProfile } from '../../services/api/dashboard';


const StudentDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        const res = await fetchStudentDashboard();
        setCourses(res.data.courses || []);
      } catch (err) {
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);



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
    <>
      {/* Hero di benvenuto */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Body className="text-center py-5">
              <h2 className="fw-bold mb-1 text-dark">
                Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!
              </h2>
              <p className="text-muted mb-0">Continua il tuo percorso di apprendimento artistico</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>


      {/* Widget TeoCoin: Balance, Burn/Deposit, Withdrawal */}
      <Row className="mb-4">
        <Col md={4}>
          <TeoCoinBalanceWidget onWithdrawalClick={() => setWithdrawalOpen(true)} />
        </Col>
        <Col md={4}>
          <BurnDepositInterface />
        </Col>
        <Col md={4}>
          <TeoCoinWithdrawal isOpen={withdrawalOpen} onClose={() => setWithdrawalOpen(false)} />
        </Col>
      </Row>

      {/* Lista corsi effettuati */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-light border-0">
              <Card.Title as="h5" className="mb-1">
                I Tuoi Corsi ({courses.length})
              </Card.Title>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-4">
                  <i className="feather icon-book-open text-muted" style={{ fontSize: '3rem' }}></i>
                  <p className="text-muted mt-3">Nessun corso acquistato</p>
                </div>
              ) : (
                <ul className="list-group">
                  {courses.map(course => (
                    <li key={course.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <span>{course.title}</span>
                      <Link to={`/corsi/${course.id}`} className="btn btn-sm btn-outline-primary">Vai al corso</Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card.Body>
          </Card>
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
  );
};

export default StudentDashboard;
