import React, { useState, useEffect } from 'react';
import { Form, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { fetchUserSettings, updateUserSettings, transformSettingsData, transformSettingsForBackend } from '../../services/api/profile';

const ProfileSettings = () => {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    courseReminders: true,
    weeklyDigest: true,
    marketingEmails: false,
    theme: 'light',
    language: 'it',
    timezone: 'Europe/Rome',
    privacy: {
      showProfile: true,
      showProgress: false,
      showAchievements: true
    }
  });

  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Load user settings on component mount
  useEffect(() => {
    loadUserSettings();
  }, []);

  const loadUserSettings = async () => {
    try {
      setInitialLoading(true);
      const response = await fetchUserSettings();
      const transformedData = transformSettingsData(response.data);
      setSettings(transformedData);
    } catch (err) {
      console.error('Error loading user settings:', err);
      setError('Errore nel caricamento delle impostazioni');
      // Keep default settings if API fails
    } finally {
      setInitialLoading(false);
    }
  };

  const handleChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setSettings(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const backendData = transformSettingsForBackend(settings);
      await updateUserSettings(backendData);
      setSuccess('Impostazioni salvate con successo!');
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('Errore nel salvataggio delle impostazioni');
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = () => {
    setSettings({
      emailNotifications: true,
      pushNotifications: false,
      courseReminders: true,
      weeklyDigest: true,
      marketingEmails: false,
      theme: 'light',
      language: 'it',
      timezone: 'Europe/Rome',
      privacy: {
        showProfile: true,
        showProgress: false,
        showAchievements: true
      }
    });
  };

  return (
    <div className="enhanced-profile-container">
      {/* Floating Decorative Elements */}
      <div className="enhanced-floating-decoration enhanced-deco-1"></div>
      <div className="enhanced-floating-decoration enhanced-deco-2"></div>
      <div className="enhanced-floating-decoration enhanced-deco-3"></div>

      {/* Header */}
      <div className="enhanced-profile-hero">
        <div className="container">
          <div className="enhanced-profile-header">
            <div className="enhanced-settings-header">
              <h1 className="enhanced-profile-name">
                <i className="feather icon-settings"></i>
                Impostazioni Profilo
              </h1>
              <p className="enhanced-settings-subtitle">
                Personalizza la tua esperienza sulla piattaforma
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Profile Navigation */}
      <div className="container">
        <div className="enhanced-profile-navigation">
          <Link to="/profile" className="enhanced-nav-item">
            <i className="feather icon-user"></i>
            <span>Profilo</span>
          </Link>
          <Link to="/profile/notifications" className="enhanced-nav-item">
            <i className="feather icon-bell"></i>
            <span>Notifiche</span>
          </Link>
          <Link to="/profile/settings" className="enhanced-nav-item active">
            <i className="feather icon-settings"></i>
            <span>Impostazioni</span>
          </Link>
          <Link to="/profile/progress" className="enhanced-nav-item">
            <i className="feather icon-award"></i>
            <span>Progressi</span>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="container">
        <div className="enhanced-profile-content">
          {initialLoading ? (
            <div className="enhanced-loading-container">
              <div className="enhanced-loading-spinner"></div>
              <p className="enhanced-loading-text">Caricamento impostazioni...</p>
            </div>
          ) : (
            <Form onSubmit={handleSave} className="enhanced-settings-form">
            
            {/* Notifications Settings */}
            <div className="enhanced-settings-section">
              <div className="enhanced-section-header">
                <h3 className="enhanced-section-title">
                  <i className="feather icon-bell"></i>
                  <span>Notifiche</span>
                </h3>
                <p className="enhanced-section-description">
                  Gestisci come e quando ricevere le notifiche
                </p>
              </div>
              
              <div className="enhanced-settings-grid">
                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Email Notifiche</label>
                    <p className="enhanced-setting-description">
                      Ricevi notifiche via email per aggiornamenti importanti
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="emailNotifications"
                      checked={settings.emailNotifications}
                      onChange={(e) => handleChange('emailNotifications', e.target.checked)}
                    />
                    <label htmlFor="emailNotifications" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Notifiche Push</label>
                    <p className="enhanced-setting-description">
                      Ricevi notifiche push sul browser
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="pushNotifications"
                      checked={settings.pushNotifications}
                      onChange={(e) => handleChange('pushNotifications', e.target.checked)}
                    />
                    <label htmlFor="pushNotifications" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Promemoria Corsi</label>
                    <p className="enhanced-setting-description">
                      Ricorda i corsi in programma e le scadenze
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="courseReminders"
                      checked={settings.courseReminders}
                      onChange={(e) => handleChange('courseReminders', e.target.checked)}
                    />
                    <label htmlFor="courseReminders" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Riassunto Settimanale</label>
                    <p className="enhanced-setting-description">
                      Ricevi un riassunto dei tuoi progressi ogni settimana
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="weeklyDigest"
                      checked={settings.weeklyDigest}
                      onChange={(e) => handleChange('weeklyDigest', e.target.checked)}
                    />
                    <label htmlFor="weeklyDigest" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Email Marketing</label>
                    <p className="enhanced-setting-description">
                      Ricevi email promozionali su nuovi corsi e offerte
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="marketingEmails"
                      checked={settings.marketingEmails}
                      onChange={(e) => handleChange('marketingEmails', e.target.checked)}
                    />
                    <label htmlFor="marketingEmails" className="enhanced-toggle-label"></label>
                  </div>
                </div>
              </div>
            </div>

            {/* Appearance Settings */}
            <div className="enhanced-settings-section">
              <div className="enhanced-section-header">
                <h3 className="enhanced-section-title">
                  <i className="feather icon-palette"></i>
                  <span>Aspetto</span>
                </h3>
                <p className="enhanced-section-description">
                  Personalizza l'aspetto dell'interfaccia
                </p>
              </div>
              
              <div className="enhanced-settings-grid">
                <div className="enhanced-setting-item enhanced-setting-select">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Tema</label>
                    <p className="enhanced-setting-description">
                      Scegli tra tema chiaro o scuro
                    </p>
                  </div>
                  <div className="enhanced-select-wrapper">
                    <Form.Select
                      value={settings.theme}
                      onChange={(e) => handleChange('theme', e.target.value)}
                      className="enhanced-form-select"
                    >
                      <option value="light">Chiaro</option>
                      <option value="dark">Scuro</option>
                      <option value="auto">Automatico</option>
                    </Form.Select>
                  </div>
                </div>

                <div className="enhanced-setting-item enhanced-setting-select">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Lingua</label>
                    <p className="enhanced-setting-description">
                      Seleziona la lingua dell'interfaccia
                    </p>
                  </div>
                  <div className="enhanced-select-wrapper">
                    <Form.Select
                      value={settings.language}
                      onChange={(e) => handleChange('language', e.target.value)}
                      className="enhanced-form-select"
                    >
                      <option value="it">Italiano</option>
                      <option value="en">English</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                    </Form.Select>
                  </div>
                </div>

                <div className="enhanced-setting-item enhanced-setting-select">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Fuso Orario</label>
                    <p className="enhanced-setting-description">
                      Il tuo fuso orario per date e orari
                    </p>
                  </div>
                  <div className="enhanced-select-wrapper">
                    <Form.Select
                      value={settings.timezone}
                      onChange={(e) => handleChange('timezone', e.target.value)}
                      className="enhanced-form-select"
                    >
                      <option value="Europe/Rome">Roma (GMT+1)</option>
                      <option value="Europe/London">Londra (GMT)</option>
                      <option value="America/New_York">New York (GMT-5)</option>
                      <option value="Asia/Tokyo">Tokyo (GMT+9)</option>
                    </Form.Select>
                  </div>
                </div>
              </div>
            </div>

            {/* Privacy Settings */}
            <div className="enhanced-settings-section">
              <div className="enhanced-section-header">
                <h3 className="enhanced-section-title">
                  <i className="feather icon-shield"></i>
                  <span>Privacy</span>
                </h3>
                <p className="enhanced-section-description">
                  Controlla la visibilità delle tue informazioni
                </p>
              </div>
              
              <div className="enhanced-settings-grid">
                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Profilo Pubblico</label>
                    <p className="enhanced-setting-description">
                      Permetti ad altri di vedere il tuo profilo
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="showProfile"
                      checked={settings.privacy.showProfile}
                      onChange={(e) => handleChange('privacy.showProfile', e.target.checked)}
                    />
                    <label htmlFor="showProfile" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Mostra Progressi</label>
                    <p className="enhanced-setting-description">
                      Condividi i tuoi progressi nei corsi
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="showProgress"
                      checked={settings.privacy.showProgress}
                      onChange={(e) => handleChange('privacy.showProgress', e.target.checked)}
                    />
                    <label htmlFor="showProgress" className="enhanced-toggle-label"></label>
                  </div>
                </div>

                <div className="enhanced-setting-item">
                  <div className="enhanced-setting-info">
                    <label className="enhanced-setting-label">Mostra Risultati</label>
                    <p className="enhanced-setting-description">
                      Rendi visibili i tuoi risultati e certificati
                    </p>
                  </div>
                  <div className="enhanced-toggle-switch">
                    <input
                      type="checkbox"
                      id="showAchievements"
                      checked={settings.privacy.showAchievements}
                      onChange={(e) => handleChange('privacy.showAchievements', e.target.checked)}
                    />
                    <label htmlFor="showAchievements" className="enhanced-toggle-label"></label>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="enhanced-settings-actions">
              <div className="enhanced-actions-group">
                <Button 
                  type="button" 
                  variant="outline-secondary"
                  className="enhanced-btn enhanced-btn-secondary"
                  onClick={resetToDefaults}
                >
                  <i className="feather icon-refresh-cw"></i>
                  <span>Ripristina Default</span>
                </Button>
                
                <Button 
                  type="submit" 
                  className="enhanced-btn enhanced-btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <div className="enhanced-loading-spinner-small"></div>
                      <span>Salvando...</span>
                    </>
                  ) : (
                    <>
                      <i className="feather icon-save"></i>
                      <span>Salva Impostazioni</span>
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Alerts */}
            {success && (
              <div className="enhanced-alert enhanced-alert-success">
                <i className="feather icon-check-circle"></i>
                <span>{success}</span>
              </div>
            )}
            
            {error && (
              <div className="enhanced-alert enhanced-alert-danger">
                <i className="feather icon-alert-circle"></i>
                <span>{error}</span>
              </div>
            )}

          </Form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
