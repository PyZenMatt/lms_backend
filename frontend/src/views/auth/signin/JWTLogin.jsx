import React from 'react';
import { Row, Col, Alert, Button } from 'react-bootstrap';
import * as Yup from 'yup';
import { Formik } from 'formik';
import { login } from '../../../services/api/auth'; // Importa la funzione API per il login
import { fetchUserProfile } from '../../../services/api/dashboard';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';

const JWTLogin = () => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

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

          // Recupera il ruolo utente dal context aggiornato
          const profileRes = await fetchUserProfile();
          const { role } = profileRes.data;

          if (role === 'student' || role === 'user') {
            navigate('/dashboard/student');
          } else if (role === 'teacher') {
            navigate('/dashboard/teacher');
          } else if (role === 'admin' || role === 'staff') {
            navigate('/dashboard/admin');
          } else {
            // fallback
            navigate('/');
          }
        } catch (error) {
          setErrors({ submit: 'Email o password non validi' });
          setSubmitting(false);
        }
      }}
    >
      {({ errors, handleBlur, handleChange, handleSubmit, isSubmitting, touched, values }) => (
        <form noValidate onSubmit={handleSubmit}>
          <div className="form-group mb-3">
            <input
              className="form-control"
              placeholder="Inserisci la tua email"
              name="email"
              onBlur={handleBlur}
              onChange={handleChange}
              type="email"
              value={values.email}
            />
            {touched.email && errors.email && <small className="text-danger form-text">{errors.email}</small>}
          </div>
          <div className="form-group mb-4">
            <input
              className="form-control"
              placeholder="Inserisci la tua password"
              name="password"
              onBlur={handleBlur}
              onChange={handleChange}
              type="password"
              value={values.password}
            />
            {touched.password && errors.password && <small className="text-danger form-text">{errors.password}</small>}
          </div>

          <div className="mb-4 mt-2 form-check">
            <input type="checkbox" className="form-check-input" id="customCheck1" />
            <label className="form-check-label" htmlFor="customCheck1">
              Ricorda credenziali
            </label>
          </div>

          {errors.submit && (
            <Col sm={12}>
              <Alert variant="danger">{errors.submit}</Alert>
            </Col>
          )}

          <Row>
            <Col mt={2}>
              <Button className="btn-block mb-4" color="primary" disabled={isSubmitting} size="large" type="submit" variant="primary">
                {isSubmitting ? 'Accesso in corso...' : 'Accedi'}
              </Button>
            </Col>
          </Row>
        </form>
      )}
    </Formik>
  );
};

export default JWTLogin;