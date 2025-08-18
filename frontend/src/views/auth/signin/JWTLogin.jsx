import React, { useEffect } from 'react';
import { Row, Col } from '@/components/ui';
import { Button } from '../../../components/ui/Button';
import { Alert } from '../../../components/ui/Alert';
import * as Yup from 'yup';
import { Formik } from 'formik';
import { login } from '../../../services/api/auth';
import { fetchUserProfile } from '../../../services/api/dashboard';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';

const JWTLogin = () => {
  const navigate = useNavigate();
  const { refreshUser, isAuthenticated, loading } = useAuth();

  // Redirect automatico solo quando login completato
  useEffect(() => {
    if (!loading && isAuthenticated) {
      // Recupera il ruolo utente dal profilo
      fetchUserProfile().then((profileRes) => {
        const { role } = profileRes.data;
        if (role === 'student' || role === 'user') {
          navigate('/dashboard/student');
        } else if (role === 'teacher') {
          navigate('/dashboard/teacher');
        } else if (role === 'admin' || role === 'staff') {
          navigate('/dashboard/admin');
        } else {
          navigate('/');
        }
      });
    }
  }, [isAuthenticated, loading, navigate]);

  return (
    <Formik
      initialValues={{
        email: '',
        password: '',
        submit: null
      }}
      validationSchema={Yup.object().shape({
        email: Yup.string().email('Deve essere un indirizzo email valido').max(255).required('Email richiesta'),
        password: Yup.string().max(255).required('Password richiesta')
      })}
      onSubmit={async (values, { setErrors, setSubmitting }) => {
        try {
          const response = await login(values);
          const { access, refresh } = response.data;
          localStorage.setItem('accessToken', access);
          localStorage.setItem('refreshToken', refresh);
          // Salva anche con chiavi compatibili col resto del frontend
          localStorage.setItem('token', access);
          localStorage.setItem('access', access);

          // Aggiorna l'AuthContext dopo il login
          await refreshUser();

          // Il redirect ora è gestito dal useEffect sopra
        } catch (error) {
          setErrors({ submit: 'Email o password non validi' });
          setSubmitting(false);
        }
      }}
    >
      {({ errors, handleBlur, handleChange, handleSubmit, isSubmitting, touched, values }) => (
        <form noValidate onSubmit={handleSubmit} className="space-y-4 w-full max-w-md mx-auto mt-12">
          <div className="flex flex-col gap-2">
            <input
              className="border rounded px-3 py-2 bg-background text-foreground outline-none"
              placeholder="Inserisci la tua email"
              name="email"
              onBlur={handleBlur}
              onChange={handleChange}
              type="email"
              value={values.email}
              required
            />
            {touched.email && errors.email && <span className="text-destructive text-xs">{errors.email}</span>}
          </div>
          <div className="flex flex-col gap-2">
            <input
              className="border rounded px-3 py-2 bg-background text-foreground outline-none"
              placeholder="Inserisci la tua password"
              name="password"
              onBlur={handleBlur}
              onChange={handleChange}
              type="password"
              value={values.password}
              required
            />
            {touched.password && errors.password && <span className="text-destructive text-xs">{errors.password}</span>}
          </div>
          <label className="flex items-center gap-2 mb-2">
            <input type="checkbox" id="customCheck1" className="accent-primary" />
            <span>Ricorda credenziali</span>
          </label>
          {errors.submit && (
            <Alert variant="destructive" className="mb-4 flex items-center">
              {errors.submit}
            </Alert>
          )}
          <Button
            type="submit"
            variant="primary"
            size="md"
            className="w-full"
            disabled={isSubmitting || loading}
          >
            {isSubmitting || loading ? 'Accesso in corso...' : 'Accedi'}
          </Button>
        </form>
      )}
    </Formik>
  );
};

export default JWTLogin;
