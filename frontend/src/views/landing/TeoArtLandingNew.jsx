import React, { memo } from 'react';
import { Container, Row, Col, Card, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';

// Memoized components for better performance
const StatCard = memo(({ stat }) => (
  <Col lg={3} md={6} className="mb-4">
    <Card className="border-0 shadow-sm h-100">
      <Card.Body className="text-center p-4">
        <div className="avatar-circle bg-primary mb-3 mx-auto">
          <i className={`feather ${stat.icon} text-white`}></i>
        </div>
        <h3 className="counter-value">{stat.value}</h3>
        <p className="mb-0 text-muted">{stat.label}</p>
      </Card.Body>
    </Card>
  </Col>
));

const FeatureCard = memo(({ feature }) => (
  <Col lg={4} md={6} className="mb-4">
    <Card className={`border-top-${feature.colorClass} border-top-3 card-hover-shadow h-100`}>
      <Card.Body className="p-4">
        <div className="d-flex align-items-center mb-3">
          <div className={`bg-${feature.colorClass} text-white rounded p-3 me-3`}>
            <i className={`feather ${feature.icon}`}></i>
          </div>
          <h5 className="mb-0">{feature.title}</h5>
        </div>
        <p className="text-muted mb-0">{feature.description}</p>
      </Card.Body>
    </Card>
  </Col>
));

const TestimonialCard = memo(({ testimonial }) => (
  <Col lg={4} md={6} className="mb-4">
    <Card className="border-0 shadow-sm h-100">
      <Card.Body className="p-4">
        <div className="d-flex align-items-center mb-3">
          <div className="avatar-initial bg-primary text-white rounded-circle me-3">
            {testimonial.name.charAt(0)}
          </div>
          <div>
            <h6 className="mb-0">{testimonial.name}</h6>
            <small className="text-muted">{testimonial.role}</small>
          </div>
        </div>
        <p className="text-muted mb-3">"{testimonial.text}"</p>
        <div className="d-flex">
          {[...Array(testimonial.rating)].map((_, i) => (
            <i key={i} className="feather icon-star text-warning"></i>
          ))}
        </div>
      </Card.Body>
    </Card>
  </Col>
));

const LandingPage = () => {
  const features = [
    {
      icon: 'icon-palette',
      title: 'Arte Digitale Web3',
      description: 'Crea NFT e arte digitale con strumenti Web3 all\'avanguardia',
      colorClass: 'primary'
    },
    {
      icon: 'icon-shopping-bag',
      title: 'NFT Marketplace',
      description: 'Vendi le tue creazioni nel marketplace integrato',
      colorClass: 'success'
    },
    {
      icon: 'icon-award',
      title: 'Certificazioni Blockchain',
      description: 'Certificati immutabili verificati sulla blockchain',
      colorClass: 'info'
    },
    {
      icon: 'icon-users',
      title: 'Community DAO',
      description: 'Partecipa alle decisioni della scuola attraverso il sistema DAO',
      colorClass: 'warning'
    },
    {
      icon: 'icon-dollar-sign',
      title: 'Blockchain Rewards',
      description: 'Guadagna TeoCoins reali completando corsi e creando arte',
      colorClass: 'danger'
    },
    {
      icon: 'icon-copy',
      title: 'Peer Review Web3',
      description: 'Sistema di valutazione decentralizzato basato su smart contracts',
      colorClass: 'dark'
    }
  ];

  // Stats section data
  const stats = [
    { value: '2,847', label: 'Artisti Digitali', icon: 'icon-users' },
    { value: '450+', label: 'Corsi NFT', icon: 'icon-book-open' },
    { value: '247K', label: 'TeoCoins Guadagnati', icon: 'icon-dollar-sign' },
    { value: '€127K', label: 'Valore Reale Creato', icon: 'icon-trending-up' }
  ];

  // Testimonials section data
  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Digital Artist & NFT Creator',
      text: 'TeoArt ha rivoluzionato il mio percorso artistico. In 6 mesi ho guadagnato oltre 15 ETH vendendo le mie opere!',
      rating: 5
    },
    {
      name: 'Marco Rossi',
      role: 'Blockchain Developer',
      text: 'La prima scuola che unisce arte e tecnologia Web3. I corsi sono all\'avanguardia e i docenti sono esperti del settore.',
      rating: 5
    },
    {
      name: 'Elena Bianchi',
      role: 'Crypto Art Collector',
      text: 'Il marketplace integrato mi ha permesso di scoprire artisti incredibili. La qualità è eccezionale!',
      rating: 5
    }
  ];

  return (
    <div className="landing-page">
      {/* Floating Elements - Simplified for performance */}
      <div className="auth-bg-simple">
        <span className="r" />
        <span className="r s" />
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <Container>
          <Row className="align-items-center min-vh-100">
            <Col lg={6} className="position-relative" style={{ zIndex: 5 }}>
              <div className="hero-content">
                <Badge bg="primary" className="mb-3 p-2 fs-6">
                  <i className="feather icon-award me-1"></i> 
                  Prima Scuola d'Arte Web3 al Mondo
                </Badge>
                
                <h1 className="display-4 fw-bold mb-4 text-primary">
                  TeoArt<span className="text-dark">Web3</span>
                  <div className="w-50 border-bottom border-primary border-3 mt-2"></div>
                </h1>
                
                <p className="lead mb-4">
                  <strong>Rivoluzione nell'educazione artistica!</strong> La prima scuola che 
                  unisce arte tradizionale e tecnologia Web3. Crea NFT, guadagna <span className="text-primary">TeoCoins reali</span> 
                  e partecipa alla Community DAO più innovativa del settore.
                </p>

                <div className="d-flex flex-wrap gap-2 mb-4">
                  <div className="d-inline-flex align-items-center me-3 mb-2">
                    <i className="feather icon-check-circle text-success me-2"></i>
                    <span>Guadagni reali in crypto</span>
                  </div>
                  <div className="d-inline-flex align-items-center me-3 mb-2">
                    <i className="feather icon-check-circle text-success me-2"></i>
                    <span>Certificazioni NFT</span>
                  </div>
                  <div className="d-inline-flex align-items-center me-3 mb-2">
                    <i className="feather icon-check-circle text-success me-2"></i>
                    <span>Marketplace integrato</span>
                  </div>
                  <div className="d-inline-flex align-items-center me-3 mb-2">
                    <i className="feather icon-check-circle text-success me-2"></i>
                    <span>Sistema DAO avanzato</span>
                  </div>
                </div>
                
                <div className="d-flex flex-wrap gap-3">
                  <Link to="/auth/signup-1" className="btn btn-primary btn-lg shadow-lg">
                    <i className="feather icon-rocket me-2"></i>
                    Inizia l'Avventura Web3
                  </Link>
                  <Link to="/auth/signin-1" className="btn btn-light btn-lg">
                    <i className="feather icon-log-in me-2"></i>
                    Accedi alla Piattaforma
                  </Link>
                </div>
              </div>
            </Col>
            
            <Col lg={6} className="position-relative">
              <div className="hero-cards">
                {/* Floating Cards - Styled like cards in Datta Able */}
                <Card className="shadow-lg position-absolute card-nft" 
                      style={{ 
                          top: '10%', 
                          right: '15%', 
                          width: '280px',
                          transform: 'rotate(5deg)',
                          zIndex: 3
                      }}>
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <Badge bg="primary">NFT Creation</Badge>
                    <Badge bg="danger" pill>LIVE</Badge>
                  </Card.Header>
                  <Card.Body>
                    <div className="mb-3 bg-light rounded p-3 text-center" style={{height: '120px'}}>
                      <i className="feather icon-image text-primary" style={{fontSize: '3rem'}}></i>
                    </div>
                    <h5>Digital Art Masterpiece</h5>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="fw-bold text-primary">2.5 ETH</span>
                      <Badge bg="success">+125 TeoCoins</Badge>
                    </div>
                  </Card.Body>
                </Card>

                <Card className="shadow-lg position-absolute card-course" 
                      style={{ 
                          top: '35%', 
                          left: '5%', 
                          width: '280px',
                          transform: 'rotate(-3deg)',
                          zIndex: 4
                      }}>
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <Badge bg="info">Course</Badge>
                    <div className="position-relative" style={{width: '30px', height: '30px'}}>
                      <div className="rounded-circle position-absolute" 
                          style={{
                              width: '30px', 
                              height: '30px', 
                              border: '3px solid #00acc1',
                              borderTopColor: 'transparent',
                              transform: 'rotate(45deg)'
                          }}>
                      </div>
                    </div>
                  </Card.Header>
                  <Card.Body>
                    <h5>Advanced NFT Development</h5>
                    <p className="small text-muted">Smart Contracts & Marketplace Integration</p>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="small text-muted">12 settimane</span>
                      <Badge bg="warning">+25 TeoCoins</Badge>
                    </div>
                  </Card.Body>
                </Card>

                <Card className="shadow-lg position-absolute card-dao" 
                      style={{ 
                          bottom: '10%', 
                          right: '10%', 
                          width: '280px',
                          transform: 'rotate(2deg)',
                          zIndex: 2
                      }}>
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <Badge bg="warning">DAO Community</Badge>
                    <div className="text-success">
                      <i className="feather icon-circle" style={{fontSize: '10px'}}></i>
                    </div>
                  </Card.Header>
                  <Card.Body>
                    <h5>Voting Session Active</h5>
                    <p className="small text-muted">New Marketplace Features</p>
                    <div className="progress mb-2" style={{height: '10px'}}>
                      <div className="progress-bar bg-success" style={{width: '73%'}}></div>
                    </div>
                    <div className="text-end small">73% Yes</div>
                  </Card.Body>
                </Card>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Stats Section */}
      <section className="stats-section py-5 bg-light">
        <Container>
          <Row className="text-center mb-5">
            <Col lg={8} className="mx-auto">
              <h2 className="section-title mb-3">
                <i className="feather icon-bar-chart-2 text-primary me-2"></i> 
                TeoArt in Numeri
              </h2>
              <p className="text-muted">
                I risultati tangibili della rivoluzione Web3 nell'educazione artistica
              </p>
            </Col>
          </Row>
          <Row>
            {stats.map((stat, index) => (
              <StatCard key={index} stat={stat} />
            ))}
          </Row>
        </Container>
      </section>

      {/* Features Section */}
      <section className="features-section py-5">
        <Container>
          <Row className="text-center mb-5">
            <Col lg={8} className="mx-auto">
              <h2 className="section-title mb-3">
                <i className="feather icon-gift text-primary me-2"></i> 
                Funzionalità Innovative
              </h2>
              <p className="text-muted">
                Scopri tutte le caratteristiche che rendono TeoArt la scelta ideale 
                per artisti, creatori e collezionisti nell'era Web3.
              </p>
            </Col>
          </Row>
          <Row>
            {features.map((feature, index) => (
              <FeatureCard key={index} feature={feature} />
            ))}
          </Row>
        </Container>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials-section py-5 bg-light">
        <Container>
          <Row className="text-center mb-5">
            <Col lg={8} className="mx-auto">
              <h2 className="section-title mb-3">
                <i className="feather icon-message-circle text-primary me-2"></i> 
                Cosa Dicono i Nostri Artisti
              </h2>
              <p className="text-muted">
                Storie di successo dalla community più innovativa del Web3
              </p>
            </Col>
          </Row>
          <Row>
            {testimonials.map((testimonial, index) => (
              <TestimonialCard key={index} testimonial={testimonial} />
            ))}
          </Row>
        </Container>
      </section>

      {/* How it Works Section */}
      <section className="how-it-works-section py-5">
        <Container>
          <Row className="text-center mb-5">
            <Col lg={8} className="mx-auto">
              <h2 className="section-title mb-3">
                <i className="feather icon-help-circle text-primary me-2"></i> 
                Come Funziona
              </h2>
              <p className="text-muted">
                Tre semplici passi per iniziare il tuo percorso nell'arte Web3
              </p>
            </Col>
          </Row>
          <Row>
            <Col lg={4} className="mb-4">
              <Card className="border-0 shadow-sm h-100">
                <Card.Body className="p-4 text-center">
                  <div className="step-circle mb-3 mx-auto">1</div>
                  <div className="avatar-circle bg-primary mb-3 mx-auto">
                    <i className="feather icon-user-plus text-white"></i>
                  </div>
                  <h5>Registrati e Connetti Wallet</h5>
                  <p className="text-muted mb-0">
                    Crea il tuo account e connetti il tuo wallet Web3 per iniziare
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col lg={4} className="mb-4">
              <Card className="border-0 shadow-sm h-100">
                <Card.Body className="p-4 text-center">
                  <div className="step-circle mb-3 mx-auto">2</div>
                  <div className="avatar-circle bg-primary mb-3 mx-auto">
                    <i className="feather icon-book-open text-white"></i>
                  </div>
                  <h5>Scegli i Tuoi Corsi</h5>
                  <p className="text-muted mb-0">
                    Esplora i corsi NFT e Web3, acquista con TeoCoins o ETH
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col lg={4} className="mb-4">
              <Card className="border-0 shadow-sm h-100">
                <Card.Body className="p-4 text-center">
                  <div className="step-circle mb-3 mx-auto">3</div>
                  <div className="avatar-circle bg-primary mb-3 mx-auto">
                    <i className="feather icon-dollar-sign text-white"></i>
                  </div>
                  <h5>Crea, Valuta e Guadagna</h5>
                  <p className="text-muted mb-0">
                    Completa progetti, partecipa a peer review e guadagna TeoCoins reali
                  </p>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </section>

      {/* CTA Section */}
      <section className="cta-section py-5 bg-primary text-white">
        <Container>
          <Row className="justify-content-center">
            <Col lg={8} className="text-center">
              <h2 className="mb-4">Pronto a Rivoluzionare la Tua Arte?</h2>
              <p className="lead mb-4">
                Unisciti a migliaia di artisti che stanno già guadagnando nel Web3. 
                La tua creatività ha finalmente un valore reale.
              </p>
              <div className="d-flex flex-wrap justify-content-center gap-3">
                <Link to="/auth/signup-1" className="btn btn-light btn-lg">
                  <i className="feather icon-rocket me-2"></i>
                  Inizia Gratis Ora
                </Link>
                <Link to="/sample-page" className="btn btn-outline-light btn-lg">
                  <i className="feather icon-info me-2"></i>
                  Scopri di Più
                </Link>
              </div>
              <div className="mt-4">
                <Badge bg="light" text="primary" className="p-2">
                  <i className="feather icon-shield me-2"></i>
                  Registrazione gratuita • Nessun costo nascosto • Guadagni immediati
                </Badge>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Footer */}
      <footer className="footer py-5 bg-dark text-white">
        <Container>
          <Row className="text-center">
            <Col>
              <h3 className="mb-3">
                <i className="feather icon-palette me-2"></i>
                TeoArt Web3 School
              </h3>
              <p className="mb-4">
                La prima scuola d'arte Web3 al mondo. Dove creatività e tecnologia si incontrano.
              </p>
              <div className="social-links mb-4">
                <a href="#" className="btn btn-outline-light btn-icon rounded-circle mx-1">
                  <i className="feather icon-twitter"></i>
                </a>
                <a href="#" className="btn btn-outline-light btn-icon rounded-circle mx-1">
                  <i className="feather icon-instagram"></i>
                </a>
                <a href="#" className="btn btn-outline-light btn-icon rounded-circle mx-1">
                  <i className="feather icon-github"></i>
                </a>
                <a href="#" className="btn btn-outline-light btn-icon rounded-circle mx-1">
                  <i className="feather icon-globe"></i>
                </a>
              </div>
              <p className="mb-0 small">
                © 2025 TeoArt Web3 School. Powered by blockchain technology.
              </p>
            </Col>
          </Row>
        </Container>
      </footer>
    </div>
  );
};

// Export memoized component for better performance
export default memo(LandingPage);
