import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const DashboardRedirect = () => {
  const { user, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && isAuthenticated && user && user.role) {
      const userRole = user.role.toLowerCase();
      
      // Redirect in base al ruolo dell'utente
      switch (userRole) {
        case 'student':
          navigate('/dashboard/student', { replace: true });
          break;
        case 'teacher':
          navigate('/dashboard/teacher', { replace: true });
          break;
        case 'admin':
          navigate('/dashboard/admin', { replace: true });
          break;
        default:
          console.warn('Unknown role:', userRole, '- defaulting to student dashboard');
          navigate('/dashboard/student', { replace: true });
      }
    } else if (!loading && !isAuthenticated) {
      // Se non è autenticato, redirect al login
      navigate('/login', { replace: true });
    }
  }, [user, loading, isAuthenticated, navigate]);

  // Mostra un loader mentre decide dove redirectare
  return (
    <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Caricamento...</span>
        </div>
        <p className="mt-3 text-muted">Caricamento dashboard...</p>
      </div>
    </div>
  );
};

export default DashboardRedirect;
