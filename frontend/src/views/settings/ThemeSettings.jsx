/**
 * 🌙 Theme Settings Page
 * 
 * Comprehensive theme management interface with:
 * - Theme selection (Light/Dark/Auto)
 * - Custom color schemes
 * - Accessibility options
 * - Theme preview
 */

import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Form, Badge, Alert } from 'react-bootstrap';
import { useTheme } from '../../contexts/ThemeContext';
import ThemeToggle from '../../components/ui/ThemeToggle';

const ThemeSettings = () => {
  const { 
    isDark, 
    systemPreference, 
    isManuallySet, 
    toggleTheme, 
    setTheme, 
    resetToSystemPreference,
    getThemeName,
    getThemeColors 
  } = useTheme();

  const [showPreview, setShowPreview] = useState(false);
  const themeColors = getThemeColors();

  const themeOptions = [
    {
      id: 'light',
      name: 'Light Theme',
      description: 'Clean and bright interface perfect for daytime use',
      icon: '☀️',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
      id: 'dark',
      name: 'Dark Theme', 
      description: 'Easy on the eyes for extended use and low-light environments',
      icon: '🌙',
      gradient: 'linear-gradient(135deg, #2c3e50 0%, #4a6741 100%)'
    },
    {
      id: 'auto',
      name: 'System Preference',
      description: 'Automatically matches your device settings',
      icon: '🔄',
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    }
  ];

  const handleThemeChange = (themeId) => {
    if (themeId === 'auto') {
      resetToSystemPreference();
    } else {
      setTheme(themeId);
    }
  };

  const getCurrentSelection = () => {
    if (!isManuallySet()) return 'auto';
    return getThemeName();
  };

  return (
    <Container fluid className="p-4">
      <Row>
        <Col lg={8} md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent border-0 pb-0">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h4 className="mb-1">🎨 Theme Settings</h4>
                  <p className="text-muted mb-0">
                    Customize your SchoolPlatform experience with different themes and color schemes
                  </p>
                </div>
                <ThemeToggle size="lg" showLabel={true} />
              </div>
            </Card.Header>

            <Card.Body>
              {/* Current Status */}
              <Alert variant={isDark ? 'info' : 'primary'} className="d-flex align-items-center">
                <div className="me-3" style={{ fontSize: '1.5rem' }}>
                  {isDark ? '🌙' : '☀️'}
                </div>
                <div>
                  <strong>Current Theme: {isDark ? 'Dark' : 'Light'} Mode</strong>
                  <div className="small">
                    {isManuallySet() 
                      ? 'Manually selected theme' 
                      : `Following system preference (${systemPreference})`
                    }
                  </div>
                </div>
              </Alert>

              {/* Theme Selection */}
              <div className="mb-4">
                <h5 className="mb-3">Choose Your Theme</h5>
                <Row>
                  {themeOptions.map((option) => (
                    <Col md={4} key={option.id} className="mb-3">
                      <Card 
                        className={`theme-option h-100 cursor-pointer border-2 ${
                          getCurrentSelection() === option.id 
                            ? 'border-primary shadow-sm' 
                            : 'border-light hover-shadow'
                        }`}
                        onClick={() => handleThemeChange(option.id)}
                        style={{ 
                          cursor: 'pointer',
                          transition: 'all 0.3s ease',
                          transform: getCurrentSelection() === option.id ? 'translateY(-2px)' : 'none'
                        }}
                      >
                        <Card.Body className="text-center p-4">
                          <div 
                            className="theme-preview mb-3"
                            style={{
                              width: '60px',
                              height: '60px',
                              borderRadius: '12px',
                              background: option.gradient,
                              margin: '0 auto',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '1.5rem'
                            }}
                          >
                            {option.icon}
                          </div>
                          <h6 className="mb-2">{option.name}</h6>
                          <p className="text-muted small mb-3">{option.description}</p>
                          {getCurrentSelection() === option.id && (
                            <Badge bg="primary">
                              <i className="feather icon-check me-1"></i>
                              Active
                            </Badge>
                          )}
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>

              {/* Theme Preview Toggle */}
              <div className="mb-4">
                <h5 className="mb-3">Theme Preview</h5>
                <Button
                  variant={showPreview ? 'primary' : 'outline-primary'}
                  onClick={() => setShowPreview(!showPreview)}
                  className="me-2"
                >
                  <i className={`feather icon-${showPreview ? 'eye-off' : 'eye'} me-2`}></i>
                  {showPreview ? 'Hide' : 'Show'} Color Palette
                </Button>
              </div>

              {/* Color Palette Preview */}
              {showPreview && (
                <div className="mb-4">
                  <Card className="border-0" style={{ background: themeColors.surface }}>
                    <Card.Body>
                      <h6 className="mb-3" style={{ color: themeColors.text }}>
                        Current Theme Colors
                      </h6>
                      <Row>
                        {Object.entries(themeColors).map(([name, color]) => (
                          <Col md={3} sm={6} key={name} className="mb-3">
                            <div className="d-flex align-items-center">
                              <div
                                className="color-swatch me-2"
                                style={{
                                  width: '30px',
                                  height: '30px',
                                  borderRadius: '6px',
                                  background: color,
                                  border: `2px solid ${themeColors.border}`
                                }}
                              ></div>
                              <div>
                                <div 
                                  className="small fw-medium"
                                  style={{ color: themeColors.text }}
                                >
                                  {name.charAt(0).toUpperCase() + name.slice(1)}
                                </div>
                                <div 
                                  className="small"
                                  style={{ 
                                    color: themeColors.textMuted,
                                    fontFamily: 'monospace' 
                                  }}
                                >
                                  {color}
                                </div>
                              </div>
                            </div>
                          </Col>
                        ))}
                      </Row>
                    </Card.Body>
                  </Card>
                </div>
              )}

              {/* Quick Actions */}
              <div className="mb-4">
                <h5 className="mb-3">Quick Actions</h5>
                <div className="d-flex flex-wrap gap-2">
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={toggleTheme}
                  >
                    <i className="feather icon-refresh-cw me-1"></i>
                    Toggle Theme
                  </Button>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => setTheme('light')}
                    disabled={!isDark}
                  >
                    <i className="feather icon-sun me-1"></i>
                    Switch to Light
                  </Button>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => setTheme('dark')}
                    disabled={isDark}
                  >
                    <i className="feather icon-moon me-1"></i>
                    Switch to Dark
                  </Button>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={resetToSystemPreference}
                    disabled={!isManuallySet()}
                  >
                    <i className="feather icon-smartphone me-1"></i>
                    Follow System
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={4} md={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent border-0">
              <h5 className="mb-0">💡 Theme Tips</h5>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <h6>🌙 Dark Mode Benefits</h6>
                <ul className="small text-muted mb-0">
                  <li>Reduces eye strain in low light</li>
                  <li>Saves battery on OLED screens</li>
                  <li>Better for extended study sessions</li>
                  <li>Modern, professional appearance</li>
                </ul>
              </div>

              <div className="mb-3">
                <h6>☀️ Light Mode Benefits</h6>
                <ul className="small text-muted mb-0">
                  <li>Better readability in bright environments</li>
                  <li>Classic, familiar interface</li>
                  <li>Ideal for detailed document work</li>
                  <li>Optimal for daytime use</li>
                </ul>
              </div>

              <div className="mb-3">
                <h6>🔄 Auto Mode Benefits</h6>
                <ul className="small text-muted mb-0">
                  <li>Adapts to your schedule automatically</li>
                  <li>Follows system dark mode settings</li>
                  <li>Seamless transition between modes</li>
                  <li>No manual switching needed</li>
                </ul>
              </div>

              <Alert variant="info" className="small">
                <strong>💡 Pro Tip:</strong> Your theme preference is saved automatically and will persist across browser sessions.
              </Alert>
            </Card.Body>
          </Card>

          {/* System Info */}
          <Card className="border-0 shadow-sm mt-3">
            <Card.Header className="bg-transparent border-0">
              <h6 className="mb-0">🔧 System Information</h6>
            </Card.Header>
            <Card.Body className="small">
              <div className="d-flex justify-content-between mb-2">
                <span>System Preference:</span>
                <Badge bg={systemPreference === 'dark' ? 'dark' : 'light'}>
                  {systemPreference}
                </Badge>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span>Current Theme:</span>
                <Badge bg={isDark ? 'dark' : 'light'}>
                  {getThemeName()}
                </Badge>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span>Manual Override:</span>
                <Badge bg={isManuallySet() ? 'warning' : 'success'}>
                  {isManuallySet() ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="d-flex justify-content-between">
                <span>Theme Support:</span>
                <Badge bg="success">Full</Badge>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ThemeSettings;
