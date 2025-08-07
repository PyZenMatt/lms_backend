import React, { useState, useEffect } from 'react';
import { Badge, Dropdown, Card, Button, Spinner } from 'react-bootstrap';
import { BellFill, CurrencyExchange, Clock, CheckCircle, XCircle } from 'react-bootstrap-icons';
import axiosClient from '../../services/core/axiosClient';
import { formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

const TeacherDiscountNotification = () => {
  const [pendingAbsorptions, setPendingAbsorptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState({});

  const fetchPendingAbsorptions = async () => {
    try {
      setLoading(true);
      const response = await axiosClient.get('/teocoin/teacher/absorptions/pending/');
      
      if (response.data.success) {
        setPendingAbsorptions(response.data.pending_absorptions || []);
        setError(null);
      } else {
        setError(response.data.error || 'Errore nel caricamento notifiche');
      }
    } catch (err) {
      console.error('Errore fetch pending absorptions:', err);
      setError('Errore di connessione');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingAbsorptions();
    
    // Refresh ogni 30 secondi per notifiche real-time
    const interval = setInterval(fetchPendingAbsorptions, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleChoice = async (absorptionId, choice) => {
    try {
      setProcessing(prev => ({ ...prev, [absorptionId]: true }));
      
      const response = await axiosClient.post('/teocoin/teacher/choice/', {
        absorption_id: absorptionId,
        choice: choice
      });

      if (response.data.success) {
        // Rimuovi dalla lista locale
        setPendingAbsorptions(prev => 
          prev.filter(absorption => absorption.id !== absorptionId)
        );
        
        // Mostra messaggio di successo
        if (window.showToast) {
          window.showToast(
            choice === 'absorb' 
              ? '✅ Sconto assorbito! TEO aggiunti al tuo saldo' 
              : '💰 Scelta EUR confermata',
            'success'
          );
        }
      } else {
        throw new Error(response.data.error || 'Errore nella scelta');
      }
    } catch (err) {
      console.error('Errore nella scelta:', err);
      if (window.showToast) {
        window.showToast('❌ Errore nella scelta: ' + err.message, 'error');
      }
    } finally {
      setProcessing(prev => ({ ...prev, [absorptionId]: false }));
    }
  };

  const formatTimeRemaining = (hoursRemaining) => {
    if (hoursRemaining <= 0) return 'Scaduto';
    if (hoursRemaining < 1) return `${Math.round(hoursRemaining * 60)}m rimanenti`;
    return `${Math.round(hoursRemaining)}h rimanenti`;
  };

  const notificationCount = pendingAbsorptions.length;

  return (
    <Dropdown align="end">
      <Dropdown.Toggle
        variant="link"
        className="nav-link position-relative p-2"
        style={{ border: 'none', background: 'none', boxShadow: 'none' }}
      >
        <CurrencyExchange size={20} className="text-warning" />
        {notificationCount > 0 && (
          <Badge 
            bg="danger" 
            pill 
            className="position-absolute top-0 start-100 translate-middle"
            style={{ fontSize: '0.7rem' }}
          >
            {notificationCount}
          </Badge>
        )}
      </Dropdown.Toggle>

      <Dropdown.Menu className="dropdown-menu-end" style={{ width: '400px', maxHeight: '500px', overflowY: 'auto' }}>
        <Dropdown.Header>
          <div className="d-flex justify-content-between align-items-center">
            <span>📊 Richieste Sconto TEO</span>
            {loading && <Spinner size="sm" animation="border" />}
          </div>
        </Dropdown.Header>

        {error && (
          <div className="dropdown-item-text text-danger p-3">
            <small>⚠️ {error}</small>
          </div>
        )}

        {!loading && notificationCount === 0 && (
          <div className="dropdown-item-text text-muted p-3 text-center">
            <CurrencyExchange className="mb-2" size={32} style={{ opacity: 0.5 }} />
            <br />
            <small>Nessuna richiesta di sconto pendente</small>
          </div>
        )}

        {pendingAbsorptions.map((absorption) => (
          <div key={absorption.id} className="dropdown-item-text p-0">
            <Card className="border-0 border-bottom">
              <Card.Body className="p-3">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <strong className="text-primary">{absorption.course.title}</strong>
                    <br />
                    <small className="text-muted">
                      Studente: {absorption.student.username}
                    </small>
                  </div>
                  <Badge 
                    bg={absorption.timing.hours_remaining > 2 ? "success" : "warning"}
                    className="ms-2"
                  >
                    <Clock size={12} className="me-1" />
                    {formatTimeRemaining(absorption.timing.hours_remaining)}
                  </Badge>
                </div>

                <div className="mb-3">
                  <div className="d-flex justify-content-between text-sm">
                    <span>Prezzo corso:</span>
                    <span>€{absorption.course.price}</span>
                  </div>
                  <div className="d-flex justify-content-between text-sm">
                    <span>Sconto richiesto:</span>
                    <span className="text-warning">
                      -{absorption.discount.percentage}% (€{absorption.discount.eur_amount})
                    </span>
                  </div>
                  <div className="d-flex justify-content-between text-sm">
                    <span>TEO utilizzati:</span>
                    <span className="text-info">{absorption.discount.teo_used} TEO</span>
                  </div>
                </div>

                <div className="row g-2 mb-3">
                  <div className="col-6">
                    <Card className="border-primary">
                      <Card.Body className="p-2 text-center">
                        <div className="text-primary fw-bold">Opzione A</div>
                        <div className="small text-muted">Commissione EUR</div>
                        <div className="fw-bold">€{absorption.options.option_a.teacher_eur}</div>
                        <div className="small text-success">+ 0 TEO</div>
                      </Card.Body>
                    </Card>
                  </div>
                  <div className="col-6">
                    <Card className="border-warning">
                      <Card.Body className="p-2 text-center">
                        <div className="text-warning fw-bold">Opzione B</div>
                        <div className="small text-muted">Assorbi Sconto</div>
                        <div className="fw-bold">€{absorption.options.option_b.teacher_eur}</div>
                        <div className="small text-warning">+ {absorption.options.option_b.teacher_teo} TEO</div>
                      </Card.Body>
                    </Card>
                  </div>
                </div>

                <div className="d-grid gap-2 d-md-flex justify-content-md-end">
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => handleChoice(absorption.id, 'refuse')}
                    disabled={processing[absorption.id]}
                  >
                    {processing[absorption.id] ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <>
                        <XCircle className="me-1" size={14} />
                        EUR
                      </>
                    )}
                  </Button>
                  <Button
                    variant="warning"
                    size="sm"
                    onClick={() => handleChoice(absorption.id, 'absorb')}
                    disabled={processing[absorption.id]}
                  >
                    {processing[absorption.id] ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <>
                        <CheckCircle className="me-1" size={14} />
                        TEO
                      </>
                    )}
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </div>
        ))}

        {notificationCount > 0 && (
          <Dropdown.Item 
            className="text-center text-primary"
            onClick={fetchPendingAbsorptions}
          >
            🔄 Aggiorna notifiche
          </Dropdown.Item>
        )}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default TeacherDiscountNotification;
