import React, { useEffect, useState } from 'react';
import { Card, Spinner, Alert, Form, Button, Row, Col } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { fetchUserProfile, updateUserProfile } from '../../services/api/dashboard';
import TeoCoinBalance from '../../components/blockchain/DBTeoCoinBalance';

const UserProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
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
    loadProfile();
  }, []);

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleAvatarChange = e => {
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

  const handleSave = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      const formData = new FormData();
      
      // Aggiungi tutti i campi del form
      Object.keys(form).forEach(key => {
        if (form[key] !== undefined && form[key] !== null) {
          formData.append(key, form[key]);
        }
      });
      
      // Aggiungi l'avatar se presente
      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }

      await updateUserProfile(formData);
      setSuccess('Profilo aggiornato con successo');
      setAvatarFile(null);
    } catch (err) {
      setError('Errore nel salvataggio');
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

  if (loading) {
    return (
      <div className="skillshare-profile-wrapper">
        <div className="skillshare-loading-container">
          <div className="skillshare-loading-spinner"></div>
          <p className="skillshare-loading-text">Caricamento del profilo...</p>
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="skillshare-profile-wrapper">
        <div className="container">
          <div className="skillshare-auth-error">
            <i className="feather icon-alert-circle"></i>
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="skillshare-profile-wrapper">
      {/* Background Elements */}
      <div className="skillshare-bg-elements">
        <div className="skillshare-bg-circle skillshare-bg-circle-1"></div>
        <div className="skillshare-bg-circle skillshare-bg-circle-2"></div>
        <div className="skillshare-bg-circle skillshare-bg-circle-3"></div>
      </div>

      <div className="container">
        {/* Profile Header Card */}
        <div className="skillshare-profile-header">
          <div className="skillshare-auth-card">
            <div className="skillshare-profile-hero">
              <div className="skillshare-avatar-section">
                <div className="skillshare-avatar-container">
                  {(avatarPreview || profile?.avatar) ? (
                    <img 
                      src={avatarPreview || (profile?.avatar?.startsWith('http') ? profile.avatar : `http://127.0.0.1:8000${profile.avatar}`)}
                      alt="Avatar" 
                      className="skillshare-avatar-image" 
                    />
                  ) : (
                    <div className="skillshare-avatar-placeholder">
                      {getUserInitials()}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="skillshare-profile-info">
                <h1 className="skillshare-profile-name">{getFullName()}</h1>
                <div className="skillshare-profile-meta">
                  <span className="skillshare-profile-role">
                    <i className="feather icon-shield"></i>
                    {profile.role}
                  </span>
                  {form.profession && (
                    <span className="skillshare-profile-profession">
                      <i className="feather icon-briefcase"></i>
                      {form.profession}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="skillshare-profile-stats">
          <div className="skillshare-stat-card">
            <div className="skillshare-stat-icon">
              <i className="feather icon-mail"></i>
            </div>
            <div className="skillshare-stat-content">
              <div className="skillshare-stat-value">
                {profile.email ? '✓' : '×'}
              </div>
              <div className="skillshare-stat-label">Email Verificata</div>
            </div>
          </div>
          
          <div className="skillshare-stat-card skillshare-stat-special">
            <div className="skillshare-stat-icon">
              <i className="feather icon-dollar-sign"></i>
            </div>
            <div className="skillshare-stat-content">
              <TeoCoinBalance showDetails={false} />
            </div>
          </div>
          
          <div className="skillshare-stat-card">
            <div className="skillshare-stat-icon">
              <i className="feather icon-calendar"></i>
            </div>
            <div className="skillshare-stat-content">
              <div className="skillshare-stat-value">
                {profile.date_joined ? new Date(profile.date_joined).getFullYear() : 'N/A'}
              </div>
              <div className="skillshare-stat-label">Membro dal</div>
            </div>
          </div>
        </div>

        {/* Main Profile Form */}
        <div className="skillshare-profile-content">
          <div className="skillshare-auth-card">
            <div className="skillshare-auth-body">
              <div className="skillshare-auth-header">
                <h2 className="skillshare-auth-title">
                  <i className="feather icon-user"></i>
                  Il Mio Profilo
                </h2>
                <p className="skillshare-auth-subtitle">
                  Gestisci le tue informazioni personali e le preferenze del profilo
                </p>
              </div>

              {/* Read-only Information */}
              <div className="skillshare-readonly-section">
                <div className="row">
                  <div className="col-md-6">
                    <div className="skillshare-info-item">
                      <label className="skillshare-info-label">Username:</label>
                      <span className="skillshare-info-value">{profile.username}</span>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="skillshare-info-item">
                      <label className="skillshare-info-label">Email:</label>
                      <span className="skillshare-info-value">{profile.email}</span>
                    </div>
                  </div>
                </div>
              </div>

              <Form onSubmit={handleSave} className="skillshare-auth-form">
                <div className="row">
                  <div className="col-md-6">
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Foto Profilo</label>
                      <div className="skillshare-file-upload-container">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleAvatarChange}
                          className="skillshare-file-input"
                          id="avatar-upload"
                        />
                        <label htmlFor="avatar-upload" className="skillshare-file-label">
                          <i className="feather icon-camera"></i>
                          <span>Scegli foto</span>
                        </label>
                      </div>
                      {avatarPreview && (
                        <div className="skillshare-avatar-preview-container">
                          <img src={avatarPreview} alt="Preview" className="skillshare-avatar-preview" />
                        </div>
                      )}
                    </div>
                    
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Nome</label>
                      <input
                        type="text"
                        className="skillshare-input"
                        name="first_name"
                        value={form.first_name}
                        onChange={handleChange}
                        placeholder="Inserisci il tuo nome"
                      />
                    </div>
                    
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Cognome</label>
                      <input
                        type="text"
                        className="skillshare-input"
                        name="last_name"
                        value={form.last_name}
                        onChange={handleChange}
                        placeholder="Inserisci il tuo cognome"
                      />
                    </div>
                    
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Telefono</label>
                      <input
                        type="tel"
                        className="skillshare-input"
                        name="phone"
                        value={form.phone}
                        onChange={handleChange}
                        placeholder="Inserisci il tuo numero di telefono"
                      />
                    </div>
                  </div>
                  
                  <div className="col-md-6">
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Professione Artistica</label>
                      <input
                        type="text"
                        className="skillshare-input"
                        name="profession"
                        value={form.profession}
                        onChange={handleChange}
                        placeholder="es. Illustratore, Pittore ad olio, Scultore..."
                      />
                    </div>
                    
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Aspirazioni Artistiche</label>
                      <textarea
                        rows={3}
                        className="skillshare-input skillshare-textarea"
                        name="artistic_aspirations"
                        value={form.artistic_aspirations}
                        onChange={handleChange}
                        placeholder="Descrivi le tue aspirazioni e specializzazioni artistiche..."
                      />
                    </div>
                    
                    <div className="skillshare-input-group">
                      <label className="skillshare-input-label">Biografia</label>
                      <textarea
                        rows={3}
                        className="skillshare-input skillshare-textarea"
                        name="bio"
                        value={form.bio}
                        onChange={handleChange}
                        placeholder="Raccontaci qualcosa di te..."
                      />
                    </div>
                  </div>
                </div>
                
                <div className="skillshare-input-group">
                  <label className="skillshare-input-label">Indirizzo</label>
                  <input
                    type="text"
                    className="skillshare-input"
                    name="address"
                    value={form.address}
                    onChange={handleChange}
                    placeholder="Inserisci il tuo indirizzo"
                  />
                </div>
                
                <button type="submit" className="skillshare-auth-button">
                  <i className="feather icon-save"></i>
                  <span>Salva Modifiche</span>
                </button>
                
                {success && (
                  <div className="skillshare-success-message">
                    <i className="feather icon-check-circle"></i>
                    <span>{success}</span>
                  </div>
                )}
                
                {error && (
                  <div className="skillshare-auth-error">
                    <i className="feather icon-alert-circle"></i>
                    <span>{error}</span>
                  </div>
                )}
              </Form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
