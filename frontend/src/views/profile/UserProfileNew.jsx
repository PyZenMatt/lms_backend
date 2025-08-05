import React, { useEffect, useState } from 'react';
import { Card, Spinner, Alert, Form, Button, Row, Col, Container, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { fetchUserProfile, updateUserProfile } from '../../services/api/dashboard';
import { fetchUserRole } from '../../services/api/auth';
import MainCard from '../../components/Card/MainCard';
import ProfileWalletDisplay from '../../components/blockchain/ProfileWalletDisplay';
import './UserProfile.css';

const UserProfileNew = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [userRole, setUserRole] = useState('');
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    address: '',
    bio: '',
    profession: '',
    artistic_aspirations: '',
  });
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);

  useEffect(() => {
    const loadProfile = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await fetchUserProfile();
        setProfile(res.data);
        
        // Costruisci l'URL completo dell'avatar se presente
        const avatarUrl = res.data.avatar ? 
          (res.data.avatar.startsWith('http') ? res.data.avatar : `http://127.0.0.1:8000${res.data.avatar}`) 
          : null;
        
        setForm({
          first_name: res.data.first_name || '',
          last_name: res.data.last_name || '',
          phone: res.data.phone || '',
          address: res.data.address || '',
          bio: res.data.bio || '',
          profession: res.data.profession || '',
          artistic_aspirations: res.data.artistic_aspirations || '',
        });
        
        if (avatarUrl) {
          setAvatarPreview(avatarUrl);
        }
      } catch (err) {
        setError('Errore nel caricamento del profilo');
      } finally {
        setLoading(false);
      }
    };

    const fetchRole = async () => {
      try {
        const role = await fetchUserRole();
        setUserRole(role);
      } catch {
        setUserRole('');
      }
    };

    loadProfile();
    fetchRole();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAvatarFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    try {
      const formData = new FormData();
      Object.keys(form).forEach(key => {
        formData.append(key, form[key]);
      });
      
      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }
      
      await updateUserProfile(formData);
      setSuccess('Profilo aggiornato con successo!');
      
      // Ricarica il profilo per avere i dati aggiornati
      const res = await fetchUserProfile();
      setProfile(res.data);
    } catch (err) {
      setError('Errore nell\'aggiornamento del profilo');
    }
  };

  // Helper function to get user initials
  const getUserInitials = () => {
    const firstName = form.first_name || profile?.first_name || '';
    const lastName = form.last_name || profile?.last_name || '';
    if (firstName && lastName) {
      return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
    }
    if (firstName) {
      return firstName.charAt(0).toUpperCase();
    }
    if (profile?.username) {
      return profile.username.charAt(0).toUpperCase();
    }
    return '?';
  };

  // Helper function to get full name
  const getFullName = () => {
    const firstName = form.first_name || profile?.first_name || '';
    const lastName = form.last_name || profile?.last_name || '';
    if (firstName && lastName) {
      return `${firstName} ${lastName}`;
    }
    if (firstName) {
      return firstName;
    }
    return profile?.username || 'Utente';
  };

  const getDashboardLink = () => {
    if (userRole === 'admin') return '/dashboard/admin';
    if (userRole === 'teacher') return '/dashboard/teacher';
    return '/dashboard/student';
  };

  if (loading) {
    return (
      <Container>
        <div className="d-flex justify-content-center align-items-center profile-loading-container">
          <div className="text-center">
            <Spinner animation="border" variant="primary" />
            <p className="mt-3 text-muted">Caricamento del profilo...</p>
          </div>
        </div>
      </Container>
    );
  }

  if (error && !profile) {
    return (
      <Container>
        <Row className="justify-content-center">
          <Col md={8}>
            <Alert variant="danger" className="text-center">
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          </Col>
        </Row>
      </Container>
    );
  }

  if (!profile) return null;

  return (
    <Container>
      {/* Profile Header */}
      <Row className="mb-4">
        <Col md={12}>
          <MainCard>
            <div className="d-flex align-items-center justify-content-between flex-wrap">
              <div className="d-flex align-items-center">
                {/* Avatar */}
                <div className="me-4">
                  {(avatarPreview || profile?.avatar) ? (
                    <img 
                      src={avatarPreview || (profile?.avatar?.startsWith('http') ? profile.avatar : `http://127.0.0.1:8000${profile.avatar}`)}
                      alt="Avatar" 
                      className="rounded-circle profile-avatar-image"
                    />
                  ) : (
                    <div 
                      className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center profile-avatar-placeholder"
                    >
                      {getUserInitials()}
                    </div>
                  )}
                </div>
                
                {/* Profile Info */}
                <div>
                  <h2 className="mb-1">{getFullName()}</h2>
                  <div className="d-flex align-items-center flex-wrap gap-2">
                    <Badge bg="primary" className="d-flex align-items-center">
                      <i className="feather icon-shield me-1"></i>
                      {profile.role}
                    </Badge>
                    {form.profession && (
                      <Badge bg="secondary" className="d-flex align-items-center">
                        <i className="feather icon-briefcase me-1"></i>
                        {form.profession}
                      </Badge>
                    )}
                    <Badge bg={profile.email ? 'success' : 'warning'} className="d-flex align-items-center">
                      <i className="feather icon-mail me-1"></i>
                      Email {profile.email ? 'Verificata' : 'Non Verificata'}
                    </Badge>
                  </div>
                  <p className="text-muted mt-2 mb-0">
                    <i className="feather icon-calendar me-1"></i>
                    Membro dal {profile.date_joined ? new Date(profile.date_joined).getFullYear() : 'N/A'}
                  </p>
                </div>
              </div>
              
              {/* TeoCoin Balance - now using blockchain component */}
              <div className="text-end">
                <div className="d-flex align-items-center">
                  <i className="feather icon-dollar-sign text-warning me-2 profile-teocoin-icon"></i>
                  <div>
                    <ProfileWalletDisplay />
                  </div>
                </div>
              </div>
            </div>
          </MainCard>
        </Col>
      </Row>

      {/* Alerts */}
      {error && (
        <Row className="mb-4">
          <Col md={12}>
            <Alert variant="danger">
              <i className="feather icon-alert-circle me-2"></i>
              {error}
            </Alert>
          </Col>
        </Row>
      )}

      {success && (
        <Row className="mb-4">
          <Col md={12}>
            <Alert variant="success">
              <i className="feather icon-check-circle me-2"></i>
              {success}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Profile Form */}
      <Row>
        <Col md={12}>
          <MainCard title={
            <span>
              <i className="feather icon-edit text-primary me-2"></i>
              Modifica Profilo
            </span>
          }>
            <Form onSubmit={handleSubmit}>
              {/* Avatar Upload */}
              <Row className="mb-4">
                <Col md={12}>
                  <Form.Group>
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-camera me-2"></i>
                      Foto Profilo
                    </Form.Label>
                    <Form.Control
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className="mb-2"
                    />
                    <Form.Text className="text-muted">
                      Carica una nuova foto profilo (formato: JPG, PNG, GIF)
                    </Form.Text>
                  </Form.Group>
                </Col>
              </Row>

              {/* Personal Info */}
              <Row className="mb-4">
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-user me-2"></i>
                      Nome
                    </Form.Label>
                    <Form.Control
                      type="text"
                      name="first_name"
                      value={form.first_name}
                      onChange={handleInputChange}
                      placeholder="Il tuo nome"
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-user me-2"></i>
                      Cognome
                    </Form.Label>
                    <Form.Control
                      type="text"
                      name="last_name"
                      value={form.last_name}
                      onChange={handleInputChange}
                      placeholder="Il tuo cognome"
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Row className="mb-4">
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-phone me-2"></i>
                      Telefono
                    </Form.Label>
                    <Form.Control
                      type="tel"
                      name="phone"
                      value={form.phone}
                      onChange={handleInputChange}
                      placeholder="Il tuo numero di telefono"
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-briefcase me-2"></i>
                      Professione
                    </Form.Label>
                    <Form.Control
                      type="text"
                      name="profession"
                      value={form.profession}
                      onChange={handleInputChange}
                      placeholder="La tua professione"
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Row className="mb-4">
                <Col md={12}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-map-pin me-2"></i>
                      Indirizzo
                    </Form.Label>
                    <Form.Control
                      type="text"
                      name="address"
                      value={form.address}
                      onChange={handleInputChange}
                      placeholder="Il tuo indirizzo"
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Row className="mb-4">
                <Col md={12}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-file-text me-2"></i>
                      Biografia
                    </Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      name="bio"
                      value={form.bio}
                      onChange={handleInputChange}
                      placeholder="Racconta qualcosa di te..."
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Row className="mb-4">
                <Col md={12}>
                  <Form.Group className="mb-3">
                    <Form.Label className="d-flex align-items-center">
                      <i className="feather icon-target me-2"></i>
                      Aspirazioni Artistiche
                    </Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      name="artistic_aspirations"
                      value={form.artistic_aspirations}
                      onChange={handleInputChange}
                      placeholder="Quali sono i tuoi obiettivi artistici?"
                    />
                  </Form.Group>
                </Col>
              </Row>

              {/* Action Buttons */}
              <Row>
                <Col md={12}>
                  <div className="d-flex justify-content-between align-items-center">
                    <Link 
                      to={getDashboardLink()} 
                      className="btn btn-outline-secondary d-flex align-items-center"
                    >
                      <i className="feather icon-arrow-left me-2"></i>
                      Torna alla dashboard
                    </Link>
                    <Button 
                      type="submit" 
                      variant="primary"
                      className="d-flex align-items-center"
                    >
                      <i className="feather icon-save me-2"></i>
                      Salva Modifiche
                    </Button>
                  </div>
                </Col>
              </Row>
            </Form>
          </MainCard>
        </Col>
      </Row>
    </Container>
  );
};

export default UserProfileNew;
