/**
 * DB-Based Discount Interface
 * Instant discount operations using database instead of blockchain
 * No gas fees, instant confirmation
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Form, Badge, Spinner, ProgressBar } from 'react-bootstrap';
import './DBDiscountInterface.scss';

const DBDiscountInterface = ({ 
  course, 
  onDiscountApplied,
  className = ""
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [userBalance, setUserBalance] = useState(0);
  const [discountAmount, setDiscountAmount] = useState(0);
  const [discountCalculation, setDiscountCalculation] = useState(null);

  // Load user's DB balance
  const loadUserBalance = async () => {
    try {
      // Use withdrawal API for consistency
      const response = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🔍 Discount Balance API Response:', data);
        
        if (data.success && data.balance) {
          // Convert withdrawal API format
          setUserBalance(parseFloat(data.balance.available || 0));
        } else {
          console.warn('Balance API returned no data:', data);
          setUserBalance(0);
        }
      } else {
        console.error('Failed to fetch balance');
        setUserBalance(0);
      }
    } catch (error) {
      console.error('Error loading user balance:', error);
      setUserBalance(0);
    }
  };

  // Calculate discount based on available TEO and course price
  const calculateDiscount = async () => {
    if (!course?.price_eur || userBalance <= 0) {
      setDiscountCalculation(null);
      return;
    }

    try {
      const response = await fetch('/api/v1/teocoin/calculate-discount/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_price: course.price_eur,
          course_id: course.id
        })
      });

      if (response.ok) {
        const data = await response.json();
        setDiscountCalculation(data.discount);
      }
    } catch (error) {
      console.error('Error calculating discount:', error);
    }
  };

  // Apply discount using DB system
  const applyDiscount = async () => {
    if (!discountCalculation || discountCalculation.teo_required <= 0) {
      setError('Nessuno sconto disponibile');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🚀 Applying DB-based discount...');
      console.log(`💰 TEO Required: ${discountCalculation.teo_required}`);
      console.log(`💵 Discount: €${discountCalculation.discount_amount}`);
      console.log('⚡ Processing: Instant (DB operation)');

      const response = await fetch('/api/v1/teocoin/apply-discount/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_id: course.id,
          course_price: course.price_eur,
          course_title: course.title
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to apply discount');
      }

      const result = await response.json();
      
      if (result.success) {
        console.log('✅ DB discount applied successfully!');
        
        setSuccess({
          message: 'Sconto applicato istantaneamente!',
          discountApplied: result.discount_applied,
          finalPrice: result.final_price,
          teoUsed: result.teo_used,
          newBalance: userBalance - result.teo_used
        });
        
        // Update local balance
        setUserBalance(prev => prev - result.teo_used);
        
        // Notify parent component
        if (onDiscountApplied) {
          onDiscountApplied({
            success: true,
            discount_amount: result.discount_applied,
            final_price: result.final_price,
            teo_used: result.teo_used,
            processing_time: 'Instant',
            gas_cost: 'Free'
          });
        }
        
      } else {
        throw new Error(result.message || 'Failed to apply discount');
      }
      
    } catch (error) {
      console.error('❌ DB discount failed:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Load balance and calculate discount on mount
  useEffect(() => {
    loadUserBalance();
  }, []);

  useEffect(() => {
    calculateDiscount();
  }, [userBalance, course]);

  const maxDiscountPercentage = 50; // 50% max discount
  const teoToEurRate = 1; // 1 TEO = 1 EUR

  return (
    <Card className={`db-discount-interface ${className}`}>
      <Card.Header className="bg-success text-white">
        <div className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            <i className="feather icon-zap me-2"></i>
            Sconto Istantaneo DB
          </h5>
          <Badge bg="light" text="dark">Gratuito & Istantaneo</Badge>
        </div>
      </Card.Header>
      
      <Card.Body>
        {/* Course Information */}
        <div className="course-info mb-3">
          <h6 className="text-muted">Corso: {course?.title || 'Unknown Course'}</h6>
          <div className="d-flex justify-content-between">
            <span>Prezzo Originale:</span>
            <span className="fw-bold">€{course?.price_eur || 0}</span>
          </div>
        </div>

        {/* User Balance */}
        <div className="balance-info mb-3">
          <div className="d-flex justify-content-between align-items-center">
            <span className="text-muted">Saldo TEO Disponibile:</span>
            <div className="d-flex align-items-center">
              <Badge bg="primary" className="me-2">{userBalance} TEO</Badge>
              <Button 
                variant="outline-primary" 
                size="sm"
                onClick={loadUserBalance}
              >
                <i className="feather icon-refresh-cw"></i>
              </Button>
            </div>
          </div>
        </div>

        {/* Discount Calculation */}
        {discountCalculation && (
          <div className="discount-calculation mb-3">
            <div className="bg-light p-3 rounded">
              <h6 className="text-success mb-2">
                <i className="feather icon-percent me-2"></i>
                Calcolo Sconto Automatico
              </h6>
              
              <div className="row g-2">
                <div className="col-6">
                  <div className="text-center">
                    <div className="h4 text-success">{discountCalculation.discount_percentage?.toFixed(1)}%</div>
                    <small className="text-muted">Percentuale Sconto</small>
                  </div>
                </div>
                <div className="col-6">
                  <div className="text-center">
                    <div className="h4 text-primary">€{discountCalculation.discount_amount}</div>
                    <small className="text-muted">Risparmio in Euro</small>
                  </div>
                </div>
              </div>
              
              <hr className="my-2" />
              
              <div className="d-flex justify-content-between">
                <span>TEO Necessari:</span>
                <span className="fw-bold">{discountCalculation.teo_required} TEO</span>
              </div>
              <div className="d-flex justify-content-between">
                <span>Prezzo Finale:</span>
                <span className="fw-bold text-success">€{discountCalculation.final_price}</span>
              </div>
              
              {discountCalculation.discount_percentage >= maxDiscountPercentage && (
                <Alert variant="info" className="mt-2 mb-0 py-2">
                  <small>
                    <i className="feather icon-info me-1"></i>
                    Sconto massimo del {maxDiscountPercentage}% applicato
                  </small>
                </Alert>
              )}
            </div>
          </div>
        )}

        {/* No Discount Available */}
        {userBalance <= 0 && (
          <Alert variant="warning" className="mb-3">
            <i className="feather icon-alert-triangle me-2"></i>
            Nessun TEO disponibile per lo sconto. Guadagna TEO completando corsi!
          </Alert>
        )}

        {/* Insufficient Balance */}
        {userBalance > 0 && discountCalculation && discountCalculation.teo_required > userBalance && (
          <Alert variant="info" className="mb-3">
            <i className="feather icon-info me-2"></i>
            Sconto parziale disponibile con il tuo saldo attuale di {userBalance} TEO
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="danger" className="mb-3">
            <i className="feather icon-x-circle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Success Display */}
        {success && (
          <Alert variant="success" className="mb-3">
            <div className="d-flex flex-column">
              <div>
                <i className="feather icon-check-circle me-2"></i>
                {success.message}
              </div>
              <div className="mt-2 small">
                <div>💰 TEO Utilizzati: {success.teoUsed}</div>
                <div>💵 Sconto Applicato: €{success.discountApplied}</div>
                <div>🎯 Prezzo Finale: €{success.finalPrice}</div>
                <div>⚡ Tempo di Elaborazione: Istantaneo</div>
                <div>💳 Costo Gas: Gratuito</div>
              </div>
            </div>
          </Alert>
        )}

        {/* Action Button */}
        <div className="d-grid">
          <Button
            variant="success"
            size="lg"
            onClick={applyDiscount}
            disabled={
              isLoading || 
              !discountCalculation || 
              discountCalculation.teo_required <= 0 ||
              userBalance <= 0
            }
            className="db-discount-btn"
          >
            {isLoading ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Applicando Sconto...
              </>
            ) : (
              <>
                <i className="feather icon-zap me-2"></i>
                Applica Sconto Istantaneo
                {discountCalculation && (
                  <span className="ms-2">
                    (-€{discountCalculation.discount_amount})
                  </span>
                )}
              </>
            )}
          </Button>
        </div>

        {/* Process Benefits */}
        <div className="process-benefits mt-3">
          <small className="text-muted">
            <strong>Vantaggi del Sistema DB:</strong>
            <ul className="small mt-1 ps-3 mb-0">
              <li>⚡ Conferma istantanea (0 secondi)</li>
              <li>💳 Nessun costo gas (gratuito)</li>
              <li>🔄 Nessuna attesa blockchain</li>
              <li>🎯 Esperienza utente ottimale</li>
            </ul>
          </small>
        </div>

        {/* Comparison with Old System */}
        <div className="comparison mt-3">
          <div className="bg-info bg-opacity-10 p-2 rounded">
            <div className="row text-center small">
              <div className="col-6">
                <div className="text-success">
                  <strong>Sistema DB</strong>
                </div>
                <div>⚡ Istantaneo</div>
                <div>💳 Gratuito</div>
              </div>
              <div className="col-6">
                <div className="text-muted">
                  <strong>Vecchio Blockchain</strong>
                </div>
                <div>🐌 1-2 minuti</div>
                <div>💰 $0.005 gas</div>
              </div>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default DBDiscountInterface;
