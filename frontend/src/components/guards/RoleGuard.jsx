import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const RoleGuard = ({ allowedRoles, children, redirectTo }) => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      const userRole = user.role?.toLowerCase();

      if (!allowedRoles.includes(userRole)) {
        console.error(`🚫 Access denied: User role "${userRole}" not in allowed roles:`, allowedRoles);

        // Redirect to correct dashboard based on role
        switch (userRole) {
          case 'admin':
            navigate('/dashboard/admin', { replace: true });
            break;
          case 'teacher':
            navigate('/dashboard/teacher', { replace: true });
            break;
          case 'student':
            navigate('/dashboard/student', { replace: true });
            break;
          default:
            navigate('/auth/signin-1', { replace: true });
        }
        return;
      }
    }
  }, [user, loading, allowedRoles, navigate, redirectTo]);

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">Verificando permessi...</span>
        </div>
      </div>
    );
  }

  // User not logged in
  if (!user) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="alert alert-warning">
          <h5>Accesso negato</h5>
          <p>Devi effettuare il login per accedere a questa pagina.</p>
        </div>
      </div>
    );
  }

  const userRole = user.role?.toLowerCase();

  // Check if user role is allowed
  if (!allowedRoles.includes(userRole)) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="alert alert-danger">
          <h5>Accesso non autorizzato</h5>
          <p>Non hai i permessi per accedere a questa sezione.</p>
          <p>
            Il tuo ruolo: <strong>{userRole}</strong>
          </p>
          <p>
            Ruoli richiesti: <strong>{allowedRoles.join(', ')}</strong>
          </p>
        </div>
      </div>
    );
  }

  return children;
};

RoleGuard.propTypes = {
  allowedRoles: PropTypes.arrayOf(PropTypes.string).isRequired,
  children: PropTypes.node.isRequired,
  redirectTo: PropTypes.string
};

RoleGuard.defaultProps = {
  redirectTo: '/unauthorized'
};

export default RoleGuard;
