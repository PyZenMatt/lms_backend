import React, { useState } from 'react';
import { Row, Col, Form, Spinner } from '@/components/ui/legacy-shims';
import { Card, CardHeader, CardContent, Button } from '../../../components/ui';
import { Alert } from '../../../components/ui/Alert';
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
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-md mx-auto">
        <Card>
          <CardHeader className="text-center py-6">
            <div className="mb-4">
              <i className="feather icon-user-plus text-4xl text-primary" />
            </div>
            <h3 className="mb-4">Registrazione</h3>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4 flex items-center">
                <i className="feather icon-border rounded-md p-3 bg-muted text-muted-foreground-circle mr-2"></i>
                {error}
              </Alert>
            )}
            {success && (
              <Alert variant="default" className="mb-4 flex items-center">
                <i className="feather icon-check-circle mr-2"></i>
                {success}
              </Alert>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Role Selection */}
              <div>
                <label className="font-bold">Seleziona il tuo ruolo:</label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <label className="flex flex-col cursor-pointer">
                    <input
                      type="radio"
                      name="role"
                      value="student"
                      checked={formData.role === 'student'}
                      onChange={handleInputChange}
                      className="accent-primary"
                    />
                    <span className="font-bold">Studente</span>
                    <span className="text-muted-foreground text-xs">Accesso immediato</span>
                  </label>
                  <label className="flex flex-col cursor-pointer">
                    <input
                      type="radio"
                      name="role"
                      value="teacher"
                      checked={formData.role === 'teacher'}
                      onChange={handleInputChange}
                      className="accent-primary"
                    />
                    <span className="font-bold">Docente</span>
                    <span className="text-muted-foreground text-xs">Richiede approvazione</span>
                  </label>
                </div>
              </div>
              {/* Account Info */}
              <div className="flex items-center border rounded px-3 py-2">
                <i className="feather icon-at-sign mr-2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                  className="flex-1 bg-transparent outline-none"
                />
              </div>
              <div className="flex items-center border rounded px-3 py-2">
                <i className="feather icon-mail mr-2 text-muted-foreground" />
                <input
                  type="email"
                  placeholder="Email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="flex-1 bg-transparent outline-none"
                />
              </div>
              <div className="flex items-center border rounded px-3 py-2">
                <i className="feather icon-lock mr-2 text-muted-foreground" />
                <input
                  type="password"
                  placeholder="Password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="flex-1 bg-transparent outline-none"
                />
              </div>
              <div className="flex items-center border rounded px-3 py-2">
                <i className="feather icon-lock mr-2 text-muted-foreground" />
                <input
                  type="password"
                  placeholder="Conferma Password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  required
                  className="flex-1 bg-transparent outline-none"
                />
              </div>
              {/* Newsletter */}
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="newsletter"
                  name="newsletter"
                  checked={formData.newsletter}
                  onChange={handleInputChange}
                  className="accent-primary"
                />
                <span>Iscriviti alla newsletter settimanale</span>
              </label>
              {/* Submit Button */}
              <Button type="submit" variant="primary" size="md" className="w-full" disabled={loading}>
                {loading ? (
                  <>
                    <Spinner animation="border" size="sm" className="mr-2" />
                    Registrazione...
                  </>
                ) : (
                  <>
                    <i className="feather icon-user-plus mr-2"></i>
                    Registrati
                  </>
                )}
              </Button>
            </form>
            <p className="mt-4 text-center text-sm">
              Hai già un account?{' '}
              <NavLink to={'/auth/signin-1'} className="underline text-primary">
                Accedi
              </NavLink>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SignUpNew;
