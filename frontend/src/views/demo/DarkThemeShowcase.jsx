/**
 * 🌙 Dark Theme Feature Showcase
 * 
 * Comprehensive demonstration of all dark theme capabilities
 */

import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Alert, Modal, Form, Table, Badge, ProgressBar } from 'react-bootstrap';
import { useTheme } from '../../contexts/ThemeContext';
import ThemeToggle from '../../components/ui/ThemeToggle';

const DarkThemeShowcase = () => {
  const { isDark, getThemeColors } = useTheme();
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('components');
  
  const themeColors = getThemeColors();

  const showcaseData = {
    components: [
      { name: 'Cards', status: '✅ Full Support', features: ['Background adaptation', 'Border colors', 'Shadow effects'] },
      { name: 'Navigation', status: '✅ Full Support', features: ['Dark navbar', 'Sidebar theming', 'Menu highlighting'] },
      { name: 'Modals', status: '✅ Full Support', features: ['Dark overlays', 'Content theming', 'Border adaptation'] },
      { name: 'Forms', status: '✅ Full Support', features: ['Input styling', 'Focus states', 'Validation colors'] },
      { name: 'Buttons', status: '✅ Full Support', features: ['Color variants', 'Hover effects', 'State indicators'] },
      { name: 'Tables', status: '✅ Full Support', features: ['Row striping', 'Hover effects', 'Border colors'] },
      { name: 'Alerts', status: '✅ Full Support', features: ['Color adaptation', 'Icon theming', 'Text contrast'] },
      { name: 'Tooltips', status: '✅ Full Support', features: ['Background colors', 'Text contrast', 'Border styling'] }
    ],
    features: [
      { name: 'System Preference Detection', description: 'Automatically detects user system preference' },
      { name: 'Manual Override', description: 'Users can manually select light or dark theme' },
      { name: 'Persistent Storage', description: 'Theme preference saved in localStorage' },
      { name: 'Real-time Switching', description: 'Instant theme changes without reload' },
      { name: 'CSS Custom Properties', description: 'Dynamic color system using CSS variables' },
      { name: 'Accessibility Support', description: 'High contrast and reduced motion support' },
      { name: 'Mobile Optimization', description: 'Theme-color meta tag for mobile browsers' },
      { name: 'Component Integration', description: 'All UI components support theme switching' }
    ]
  };

  const sampleTableData = [
    { id: 1, course: 'React Fundamentals', progress: 85, status: 'In Progress', students: 124 },
    { id: 2, course: 'JavaScript ES6+', progress: 100, status: 'Completed', students: 89 },
    { id: 3, course: 'Node.js Backend', progress: 45, status: 'In Progress', students: 67 },
    { id: 4, course: 'CSS Grid & Flexbox', progress: 90, status: 'In Progress', students: 156 }
  ];

  return (
    <Container fluid className="p-4">
      <Row>
        <Col lg={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-transparent border-0 pb-0">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h3 className="mb-1">🌙 Dark Theme Showcase</h3>
                  <p className="text-muted mb-0">
                    Complete dark theme implementation with all UI components and features
                  </p>
                </div>
                <ThemeToggle size="lg" showLabel={true} />
              </div>
            </Card.Header>

            <Card.Body>
              {/* Current Theme Status */}
              <Alert variant={isDark ? 'dark' : 'light'} className="mb-4">
                <div className="d-flex align-items-center">
                  <div className="me-3" style={{ fontSize: '2rem' }}>
                    {isDark ? '🌙' : '☀️'}
                  </div>
                  <div className="flex-grow-1">
                    <h5 className="mb-1">Current Theme: {isDark ? 'Dark Mode' : 'Light Mode'}</h5>
                    <p className="mb-0">
                      {isDark 
                        ? 'You are currently viewing the dark theme with full component support.' 
                        : 'Switch to dark mode using the toggle above to see all dark theme features.'
                      }
                    </p>
                  </div>
                  <Button 
                    variant={isDark ? 'light' : 'dark'} 
                    onClick={() => setShowModal(true)}
                  >
                    View Features
                  </Button>
                </div>
              </Alert>

              {/* Navigation Tabs */}
              <div className="mb-4">
                <div className="nav nav-pills" style={{ borderBottom: `1px solid ${themeColors.border}` }}>
                  {['components', 'features', 'demo'].map((tab) => (
                    <button
                      key={tab}
                      className={`nav-link ${activeTab === tab ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab)}
                      style={{
                        background: activeTab === tab ? themeColors.primary : 'transparent',
                        color: activeTab === tab ? 'white' : themeColors.text,
                        border: 'none',
                        padding: '0.5rem 1rem',
                        margin: '0 0.25rem',
                        borderRadius: '0.375rem'
                      }}
                    >
                      {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Components Support */}
              {activeTab === 'components' && (
                <Row>
                  <Col lg={12}>
                    <h5 className="mb-3">📦 Component Support Overview</h5>
                    <Row>
                      {showcaseData.components.map((component, index) => (
                        <Col md={6} lg={4} key={index} className="mb-3">
                          <Card className="h-100">
                            <Card.Body>
                              <div className="d-flex align-items-center mb-2">
                                <h6 className="mb-0 me-2">{component.name}</h6>
                                <Badge bg="success" className="small">
                                  {component.status}
                                </Badge>
                              </div>
                              <ul className="small mb-0">
                                {component.features.map((feature, idx) => (
                                  <li key={idx} className="text-muted">{feature}</li>
                                ))}
                              </ul>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Col>
                </Row>
              )}

              {/* Features List */}
              {activeTab === 'features' && (
                <Row>
                  <Col lg={12}>
                    <h5 className="mb-3">⚡ Theme System Features</h5>
                    <Row>
                      {showcaseData.features.map((feature, index) => (
                        <Col md={6} key={index} className="mb-3">
                          <Card className="h-100">
                            <Card.Body>
                              <h6 className="mb-2">✨ {feature.name}</h6>
                              <p className="text-muted small mb-0">{feature.description}</p>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Col>
                </Row>
              )}

              {/* Live Demo */}
              {activeTab === 'demo' && (
                <Row>
                  <Col lg={12}>
                    <h5 className="mb-3">🎨 Live Component Demo</h5>
                    
                    {/* Sample Table */}
                    <Card className="mb-4">
                      <Card.Header>
                        <h6 className="mb-0">📊 Data Table Example</h6>
                      </Card.Header>
                      <Card.Body className="p-0">
                        <Table responsive striped hover className="mb-0">
                          <thead>
                            <tr>
                              <th>Course Name</th>
                              <th>Progress</th>
                              <th>Status</th>
                              <th>Students</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sampleTableData.map((row) => (
                              <tr key={row.id}>
                                <td>{row.course}</td>
                                <td>
                                  <ProgressBar 
                                    now={row.progress} 
                                    label={`${row.progress}%`}
                                    style={{ height: '20px' }}
                                  />
                                </td>
                                <td>
                                  <Badge bg={row.status === 'Completed' ? 'success' : 'primary'}>
                                    {row.status}
                                  </Badge>
                                </td>
                                <td>{row.students}</td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </Card.Body>
                    </Card>

                    {/* Sample Alerts */}
                    <Row>
                      <Col md={6} className="mb-3">
                        <Alert variant="primary">
                          <strong>Primary Alert:</strong> This is a primary alert showing theme adaptation.
                        </Alert>
                        <Alert variant="success">
                          <strong>Success Alert:</strong> Action completed successfully.
                        </Alert>
                      </Col>
                      <Col md={6} className="mb-3">
                        <Alert variant="warning">
                          <strong>Warning Alert:</strong> Please review this information.
                        </Alert>
                        <Alert variant="danger">
                          <strong>Danger Alert:</strong> Critical issue requires attention.
                        </Alert>
                      </Col>
                    </Row>

                    {/* Sample Form */}
                    <Card>
                      <Card.Header>
                        <h6 className="mb-0">📝 Form Components Example</h6>
                      </Card.Header>
                      <Card.Body>
                        <Form>
                          <Row>
                            <Col md={6}>
                              <Form.Group className="mb-3">
                                <Form.Label>Course Name</Form.Label>
                                <Form.Control 
                                  type="text" 
                                  placeholder="Enter course name"
                                  defaultValue="React Advanced Concepts"
                                />
                              </Form.Group>
                            </Col>
                            <Col md={6}>
                              <Form.Group className="mb-3">
                                <Form.Label>Category</Form.Label>
                                <Form.Select>
                                  <option>Select category</option>
                                  <option>Frontend Development</option>
                                  <option>Backend Development</option>
                                  <option>Full Stack</option>
                                </Form.Select>
                              </Form.Group>
                            </Col>
                          </Row>
                          <Form.Group className="mb-3">
                            <Form.Label>Description</Form.Label>
                            <Form.Control 
                              as="textarea" 
                              rows={3}
                              placeholder="Course description..."
                              defaultValue="Advanced React concepts including hooks, context, and performance optimization."
                            />
                          </Form.Group>
                          <div className="d-flex gap-2">
                            <Button variant="primary">Save Course</Button>
                            <Button variant="outline-secondary">Preview</Button>
                            <Button variant="outline-danger">Reset</Button>
                          </div>
                        </Form>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Feature Details Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>🌙 Dark Theme Technical Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <h6>🎨 Color System</h6>
          <p className="small text-muted mb-3">
            The dark theme uses a comprehensive CSS custom property system that dynamically 
            updates all component colors in real-time.
          </p>

          <h6>⚙️ Implementation Features</h6>
          <ul className="small">
            <li>React Context for theme state management</li>
            <li>CSS custom properties for dynamic color updates</li>
            <li>LocalStorage persistence for user preferences</li>
            <li>System preference detection and automatic following</li>
            <li>Smooth transitions between theme modes</li>
            <li>Mobile browser theme-color meta tag updates</li>
            <li>Accessibility support for reduced motion and high contrast</li>
            <li>Print-friendly styles that revert to light mode</li>
          </ul>

          <h6>🎯 Component Coverage</h6>
          <p className="small text-muted">
            All Bootstrap components and custom UI elements are fully themed, including:
            cards, modals, forms, tables, navigation, alerts, buttons, badges, and more.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default DarkThemeShowcase;
