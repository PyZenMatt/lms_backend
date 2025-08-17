import React, { useState } from 'react';
import { Card, Row, Col, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { NavLink, useNavigate } from 'react-router-dom';
import api from '../../../services/core/axiosClient';

const SignUpNew = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student', // default to student
    newsletter: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      setError('Username è obbligatorio');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email è obbligatoria');
      return false;
    }
    if (!formData.password) {
      setError('Password è obbligatoria');
      return false;
    }
    if (formData.password.length < 6) {
      setError('La password deve essere di almeno 6 caratteri');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Le password non coincidono');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const payload = {
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        role: formData.role
      };

      const response = await api.post('/register/', payload);

      console.log('Registration response:', response.data);

      // Handle successful response
      if (response.data?.success !== false) {
        if (formData.role === 'student') {
          setSuccess('🎉 Registrazione completata! Il tuo account studente è attivo. Puoi effettuare il login subito.');
          setTimeout(() => {
            navigate('/auth/signin-1');
          }, 2000);
        } else {
          setSuccess(
            "📧 Registrazione inviata! La tua richiesta di accesso come docente è in attesa di approvazione da parte dell'amministratore. Ti contatteremo via email quando sarà approvata. Grazie per la pazienza!"
          );
        }
      } else {
        // Handle API error response
        setError(response.data?.error || 'Errore durante la registrazione. Riprova.');
      }
    } catch (err) {
      console.error('Signup error:', err);
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.username) {
          setError(`Username: ${errorData.username[0]}`);
        } else if (errorData.email) {
          setError(`Email: ${errorData.email[0]}`);
        } else if (errorData.password) {
          setError(`Password: ${errorData.password[0]}`);
        } else if (errorData.non_field_errors) {
          setError(errorData.non_field_errors[0]);
        } else {
          setError('Errore durante la registrazione. Riprova.');
        }
      } else {
        setError('Errore di connessione. Riprova.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-content">
        <div className="auth-bg">
          <span className="r" />
          <span className="r s" />
          <span className="r s" />
          <span className="r" />
        </div>
        <Card className="borderless">
          <Row className="align-items-center">
            <Col>
              <Card.Body className="text-center">
                <div className="mb-4">
                  <i className="feather icon-user-plus auth-icon" />
                </div>
                <h3 className="mb-4">Registrazione</h3>

                {error && (
                  <Alert variant="danger" className="text-start">
                    <i className="feather icon-alert-circle me-2"></i>
                    {error}
                  </Alert>
                )}

                {success && (
                  <Alert variant="success" className="text-start">
                    <i className="feather icon-check-circle me-2"></i>
                    {success}
                  </Alert>
                )}

                <Form onSubmit={handleSubmit} className="text-start">
                  {/* Role Selection */}
                  <div className="mb-4">
                    <Form.Label className="fw-bold">Seleziona il tuo ruolo:</Form.Label>
                    <div className="row">
                      <div className="col-6">
                        <Form.Check
                          type="radio"
                          id="role-student"
                          name="role"
                          value="student"
                          checked={formData.role === 'student'}
                          onChange={handleInputChange}
                          label={
                            <div className="d-flex flex-column">
                              <span className="fw-bold">Studente</span>
                              <small className="text-muted">Accesso immediato</small>
                            </div>
                          }
                        />
                      </div>
                      <div className="col-6">
                        <Form.Check
                          type="radio"
                          id="role-teacher"
                          name="role"
                          value="teacher"
                          checked={formData.role === 'teacher'}
                          onChange={handleInputChange}
                          label={
                            <div className="d-flex flex-column">
                              <span className="fw-bold">Docente</span>
                              <small className="text-muted">Richiede approvazione</small>
                            </div>
                          }
                        />
                      </div>
                    </div>
                  </div>

                  {/* Account Info */}
                  <div className="input-group mb-3">
                    <span className="input-group-text">
                      <i className="feather icon-at-sign"></i>
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Username"
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="input-group mb-3">
                    <span className="input-group-text">
                      <i className="feather icon-mail"></i>
                    </span>
                    <input
                      type="email"
                      className="form-control"
                      placeholder="Email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="input-group mb-3">
                    <span className="input-group-text">
                      <i className="feather icon-lock"></i>
                    </span>
                    <input
                      type="password"
                      className="form-control"
                      placeholder="Password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="input-group mb-4">
                    <span className="input-group-text">
                      <i className="feather icon-lock"></i>
                    </span>
                    <input
                      type="password"
                      className="form-control"
                      placeholder="Conferma Password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  {/* Newsletter */}
                  <div className="form-check text-start mb-4 mt-2">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="newsletter"
                      name="newsletter"
                      checked={formData.newsletter}
                      onChange={handleInputChange}
                    />
                    <label className="form-check-label" htmlFor="newsletter">
                      Iscriviti alla newsletter settimanale
                    </label>
                  </div>

                  {/* Submit Button */}
                  <Button type="submit" className="btn btn-primary mb-4 w-100" disabled={loading}>
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Registrazione...
                      </>
                    ) : (
                      <>
                        <i className="feather icon-user-plus me-2"></i>
                        Registrati
                      </>
                    )}
                  </Button>
                </Form>

                <p className="mb-2">
                  Hai già un account?{' '}
                  <NavLink to={'/auth/signin-1'} className="f-w-400">
                    Accedi
                  </NavLink>
                </p>
              </Card.Body>
            </Col>
          </Row>
        </Card>
      </div>
    </div>
  );
};

export default SignUpNew;
