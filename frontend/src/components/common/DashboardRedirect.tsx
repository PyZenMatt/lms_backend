/* @ts-nocheck */
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const DashboardRedirect = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      const userRole = user.role?.toLowerCase();

      console.log('🔄 DashboardRedirect: Redirecting user with role:', userRole);

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
          console.warn('🔄 Unknown user role, redirecting to login');
          navigate('/auth/signin-1', { replace: true });
      }
    } else if (!loading && !user) {
      console.log('🔄 No user found, redirecting to login');
      navigate('/auth/signin-1', { replace: true });
    }
  }, [user, loading, navigate]);

  // Show loading while redirecting
  return (
    <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
      <div className="spinner-border text-primary" role="status">
        <span className="sr-only">Reindirizzamento...</span>
      </div>
    </div>
  );
};

export default DashboardRedirect;
