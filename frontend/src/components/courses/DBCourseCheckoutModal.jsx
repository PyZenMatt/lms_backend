import React, { useState, useEffect } from 'react';
import { Modal, Button, Alert, Spinner, Nav, Tab, Card, Badge } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { loadStripe } from '@stripe/stripe-js';
import {
    Elements,
    CardElement,
    useStripe,
    useElements
} from '@stripe/react-stripe-js';

// Initialize Stripe with debugging
const STRIPE_PUBLISHABLE_KEY = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 
                                import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;

console.log('🔑 Stripe Key Debug:', {
  react_env: process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY?.substring(0, 15) + '...',
  vite_env: import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY?.substring(0, 15) + '...',
  using: STRIPE_PUBLISHABLE_KEY?.substring(0, 15) + '...',
  key_length: STRIPE_PUBLISHABLE_KEY?.length
});

if (!STRIPE_PUBLISHABLE_KEY) {
  console.error('❌ No Stripe publishable key found!');
  console.log('Available env vars:', Object.keys(import.meta.env).filter(k => k.includes('STRIPE')));
}

const stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY);

/**
 * DB-based CourseCheckoutModal - Uses database TeoCoin system
 * 
 * This component provides two payment options:
 * 1. Fiat payment via Stripe (EUR) with TeoCoin rewards
 * 2. TeoCoin payment with discount (uses DB-based system)
 */
const DBCourseCheckoutModal = ({ course, show, handleClose, onPurchaseComplete }) => {
  const { user } = useAuth();
  console.log('🔥 DBCourseCheckoutModal RENDER:', { course: course?.id, show });
  
  const [activeTab, setActiveTab] = useState('fiat'); // 'fiat' or 'teocoin'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('confirm'); // confirm, purchasing, success
  const [dbBalance, setDbBalance] = useState(0);
  const [paymentResult, setPaymentResult] = useState(null);
  const [discountApplied, setDiscountApplied] = useState(false);
  const [selectedDiscount, setSelectedDiscount] = useState(10); // 5, 10, or 15

  // Calculate pricing options - ensure all values are numbers
  const fiatPrice = parseFloat(course?.price_eur || 0);
  const teoReward = parseFloat(course?.teocoin_reward || 0);
  
  // Use selected discount percentage
  const teoDiscount = selectedDiscount;
  
  // Use 1 EUR = 1 TEO ratio
  const teoNeeded = Math.floor(fiatPrice * teoDiscount / 100);
  const discountAmount = (fiatPrice * teoDiscount / 100);
  const finalPrice = fiatPrice - discountAmount;
  
  console.log(`💰 DB Pricing: €${fiatPrice}, need ${teoNeeded} TEO for ${teoDiscount}% discount, final: €${finalPrice.toFixed(2)}`);

  // Load DB balance when modal opens
  useEffect(() => {
    const loadDbBalance = async () => {
      if (!show || !user) return;
      
      try {
        console.log('💰 Loading DB balance for user:', user.id);
        
        // Use withdrawal API for consistency
        const response = await fetch('/api/v1/teocoin/withdrawals/balance/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          },
        });
        
        const data = await response.json();
        console.log('🔍 Checkout Balance API Response:', data);
        
        if (data.success && data.balance) {
          // Convert withdrawal API format
          const availableBalance = parseFloat(data.balance.available || 0);
          setDbBalance(availableBalance);
          console.log('💰 DB Balance loaded:', availableBalance);
        } else {
          console.warn('Balance API returned no data:', data);
          setDbBalance(0);
          setError('Failed to load TeoCoin balance');
        }
        
      } catch (err) {
        console.error('Error loading DB balance:', err);
        setError('Errore di connessione durante il caricamento del saldo');
      }
    };
    
    if (show) {
      setError('');
      setStep('confirm');
      setPaymentResult(null);
      setDiscountApplied(false);
      setSelectedDiscount(10);
      loadDbBalance();
    }
  }, [show, user]);

  // Handle Stripe card payment with course enrollment
  const handleStripeCardPayment = async () => {
    // This function will be handled by the StripeCardForm component
    console.log('� Stripe payment initiated from card form');
  };

  // Handle Stripe payment success
  const handleStripeSuccess = (result) => {
    console.log('🎉 Payment success handler called!');
    console.log('💳 Payment result:', result);
    
    setPaymentResult(result);
    setStep('success');
    
    console.log('✅ Step set to success, paymentResult set');
    
    if (onPurchaseComplete) {
      console.log('🔄 Calling onPurchaseComplete...');
      onPurchaseComplete();
    } else {
      console.log('⚠️ No onPurchaseComplete callback provided');
    }
  };

  // Handle Stripe payment error  
  const handleStripeError = (error) => {
    console.error('❌ Payment error handler called:', error);
    setError(error);
    setStep('confirm');
  };

  // Handle DB TeoCoin discount application
  const handleDbTeoCoinDiscount = async () => {
    if (discountApplied) {
      setError('Sconto già applicato per questo corso');
      return;
    }

    console.log('🔥 Applying DB TeoCoin discount', {
      user: user?.id,
      course: course?.id,
      teoNeeded,
      currentBalance: dbBalance,
      selectedDiscount
    });
    
    if (dbBalance < teoNeeded) {
      setError(`Saldo insufficiente. Necessari ${teoNeeded} TEO, disponibili ${dbBalance.toFixed(2)} TEO`);
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/v1/teocoin/apply-discount/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          course_id: course.id,
          teo_amount: teoNeeded,
          discount_percentage: teoDiscount
        })
      });
      
      const data = await response.json();
      console.log('📨 DB Discount response:', data);
      
      if (data.success) {
        console.log('✅ DB TeoCoin discount applied successfully!');
        
        // Update local balance
        setDbBalance(parseFloat(data.new_balance || 0));
        
        // Store discount info and switch to Stripe payment
        const discountInfo = {
          teo_used: teoNeeded,
          discount_amount_eur: discountAmount,
          discount_percentage: selectedDiscount,
          final_price: finalPrice,
          transaction_id: data.transaction_id
        };
        
        setPaymentResult({ type: 'discount_applied', discountInfo });
        setDiscountApplied(true);
        setActiveTab('fiat');
        
      } else {
        setError(data.error || 'Errore durante l\'applicazione dello sconto TeoCoin');
      }
    } catch (error) {
      console.error('❌ DB TeoCoin discount error:', error);
      setError('Errore di connessione durante l\'applicazione dello sconto');
    } finally {
      setLoading(false);
    }
  };

  // Remove unused variables
  const canAffordDiscount = dbBalance >= teoNeeded;

  const refreshDbBalance = async () => {
    try {
      // Use withdrawal API for consistency
      const response = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });
      
      const data = await response.json();
      console.log('🔍 Checkout Refresh Balance API Response:', data);
      
      if (data.success && data.balance) {
        // Convert withdrawal API format
        setDbBalance(parseFloat(data.balance.available || 0));
      } else {
        console.warn('Balance API returned no data:', data);
        setDbBalance(0);
      }
      if (data.success) {
        setDbBalance(parseFloat(data.balance.available_balance || 0));
      }
    } catch (err) {
      console.error('Error refreshing DB balance:', err);
    }
  };

  const renderFiatPaymentTab = () => {
    if (step === 'success' && paymentResult) {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Pagamento completato!</h5>
          <p>Hai acquistato con successo il corso "{course?.title}".</p>
          <div className="mb-3">
            <strong>€{paymentResult.discountInfo ? paymentResult.discountInfo.final_price.toFixed(2) : fiatPrice}</strong> pagati
            {paymentResult.discountInfo && (
              <div>
                <span className="text-warning">-{paymentResult.discountInfo.teo_used} TEO</span> usati per sconto
              </div>
            )}
            <br />
            <span className="text-success">+{teoReward} TEO</span> guadagnati come ricompensa!
          </div>
          <Button variant="primary" onClick={handleClose}>
            Accedi al corso
          </Button>
        </div>
      );
    }

    // Ensure effectivePrice is always a number
    const effectivePrice = paymentResult?.discountInfo 
      ? parseFloat(paymentResult.discountInfo.final_price) 
      : parseFloat(fiatPrice || 0);

    return (
      <div className="p-3">
        {paymentResult?.discountInfo && (
          <Alert variant="success" className="mb-3">
            <strong>✅ Sconto TeoCoin applicato!</strong>
            <br />
            Usati {paymentResult.discountInfo.teo_used} TEO per €{parseFloat(paymentResult.discountInfo.discount_amount_eur || 0).toFixed(2)} di sconto
          </Alert>
        )}
        
        <div className="payment-option-card mb-4 p-3" style={{ border: '2px solid #007bff', borderRadius: '8px', backgroundColor: '#f8f9ff' }}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-primary">💳 Pagamento con Carta</h5>
            <span className="badge badge-primary">Consigliato</span>
          </div>
          <div className="row">
            <div className="col-6">
              <strong>Prezzo: €{effectivePrice.toFixed(2)}</strong>
              {paymentResult?.discountInfo && (
                <div><small className="text-muted">Originale: €{parseFloat(fiatPrice || 0).toFixed(2)}</small></div>
              )}
            </div>
            <div className="col-6 text-end">
              <span className="text-success">+{teoReward} TEO Reward</span>
            </div>
          </div>
          <small className="text-muted">
            Pagamento sicuro con Stripe. Ricevi {teoReward} TeoCoin come ricompensa al completamento del corso.
          </small>
        </div>

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        {/* Stripe Card Payment */}
        <div className="stripe-payment-container">
          <Elements stripe={stripePromise}>
            <StripeCardForm 
              course={course}
              finalPrice={effectivePrice}
              paymentResult={paymentResult}
              onPaymentSuccess={handleStripeSuccess}
              onPaymentError={handleStripeError}
              loading={loading}
              setLoading={setLoading}
            />
          </Elements>
        </div>
      </div>
    );
  };

  const renderTeoCoinPaymentTab = () => {
    if (step === 'purchasing') {
      return (
        <div className="text-center p-4">
          <Spinner animation="border" className="mb-3" />
          <p>Pagamento in corso...</p>
          <small className="text-muted">Non chiudere questa finestra</small>
        </div>
      );
    }

    if (step === 'success' && paymentResult?.type === 'teocoin_payment') {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Sconto TeoCoin applicato!</h5>
          <p>Procedi ora al pagamento con carta per completare l'acquisto.</p>
          <Button variant="primary" onClick={() => setActiveTab('fiat')}>
            Vai al Pagamento
          </Button>
        </div>
      );
    }

    const canAffordDiscount = dbBalance >= teoNeeded;
    const canAffordFullPrice = dbBalance >= fiatPrice;

    return (
      <div className="p-3">
        {/* Wallet Info */}
        <Card className="mb-3 bg-light">
          <Card.Body>
            <h6>💰 Il Tuo Saldo TeoCoin</h6>
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <span className="text-muted">Disponibile:</span> <strong>{dbBalance.toFixed(2)} TEO</strong>
              </div>
              <Button variant="outline-secondary" size="sm" onClick={refreshDbBalance}>
                🔄 Aggiorna
              </Button>
            </div>
          </Card.Body>
        </Card>

        {/* Discount Options */}
        <Card className="mb-3">
          <Card.Header>
            <h6 className="mb-0">🪙 Sconti TeoCoin Disponibili</h6>
          </Card.Header>
          <Card.Body>
            <div className="row">
              {[5, 10, 15].map(percentage => {
                const teoRequired = Math.floor(fiatPrice * percentage / 100);
                const discount = (fiatPrice * percentage / 100);
                const final = fiatPrice - discount;
                const canAfford = dbBalance >= teoRequired;
                
                return (
                  <div key={percentage} className="col-md-4 mb-3">
                    <div 
                      className={`discount-option p-3 text-center border rounded ${
                        selectedDiscount === percentage ? 'border-success bg-light' : 'border-secondary'
                      } ${canAfford ? 'cursor-pointer' : 'opacity-50'}`}
                      onClick={() => canAfford && !discountApplied && setSelectedDiscount(percentage)}
                      style={{ cursor: canAfford && !discountApplied ? 'pointer' : 'not-allowed' }}
                    >
                      <h5 className="text-success">{percentage}% Sconto</h5>
                      <div><strong>{teoRequired} TEO</strong></div>
                      <small className="text-muted">€{discount.toFixed(2)} risparmiati</small>
                      <div className="mt-2">
                        <Badge bg={canAfford ? 'success' : 'danger'}>
                          {canAfford ? 'Disponibile' : 'TEO insufficienti'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            
            <div className="mt-3">
              <Button
                variant="success"
                size="lg"
                className="w-100"
                onClick={handleDbTeoCoinDiscount}
                disabled={loading || dbBalance < teoNeeded || discountApplied}
              >
                {loading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Applicando sconto...
                  </>
                ) : discountApplied ? (
                  `✅ Sconto ${selectedDiscount}% Applicato`
                ) : (
                  `🪙 Applica sconto ${selectedDiscount}% (${teoNeeded} TEO)`
                )}
              </Button>
            </div>
          </Card.Body>
        </Card>

        {/* Full TeoCoin Payment Option - REMOVED */}

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}
      </div>
    );
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg" centered>
      <Modal.Header closeButton>
        <Modal.Title>
          💳 Acquista Corso: {course?.title}
        </Modal.Title>
      </Modal.Header>
      
      <Modal.Body>
        <Tab.Container activeKey={activeTab} onSelect={setActiveTab}>
          <Nav variant="pills" className="justify-content-center mb-4">
            <Nav.Item>
              <Nav.Link eventKey="fiat" className="mx-2">
                💳 Carta di Credito
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="teocoin" className="mx-2">
                🪙 TeoCoin Database
              </Nav.Link>
            </Nav.Item>
          </Nav>

          <Tab.Content>
            <Tab.Pane eventKey="fiat">
              {renderFiatPaymentTab()}
            </Tab.Pane>
            
            <Tab.Pane eventKey="teocoin">
              {renderTeoCoinPaymentTab()}
            </Tab.Pane>
          </Tab.Content>
        </Tab.Container>
      </Modal.Body>
      
      {step === 'confirm' && (
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Annulla
          </Button>
        </Modal.Footer>
      )}
    </Modal>
  );
};

// Stripe Card Payment Form Component
const StripeCardForm = ({ course, finalPrice, paymentResult, onPaymentSuccess, onPaymentError, loading, setLoading }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    console.log('💳 Stripe validation:', {
      stripe_available: !!stripe,
      elements_available: !!elements,
      stripe_key_loaded: STRIPE_PUBLISHABLE_KEY?.substring(0, 15) + '...'
    });
    
    if (!stripe || !elements) {
      console.error('❌ Stripe or Elements not available:', { stripe: !!stripe, elements: !!elements });
      onPaymentError('Stripe not loaded. Please refresh the page.');
      return;
    }

    setProcessing(true);
    setLoading(true);

    try {
      console.log('💳 Starting Stripe payment process...');
      
      const cardElement = elements.getElement(CardElement);
      
      if (!cardElement) {
        throw new Error('Card element not found');
      }
      
      console.log('💳 Card element found, validating...');
      
      // Validate card element before proceeding
      const {error: cardError} = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
      });

      if (cardError) {
        console.error('❌ Card validation error:', cardError);
        
        // Handle specific Stripe error types
        if (cardError.type === 'api_connection_error') {
          throw new Error('Connection problem with payment service. Please check your internet connection and try again.');
        } else if (cardError.type === 'api_error') {
          throw new Error('Payment service error. Please try again in a moment.');
        } else if (cardError.type === 'authentication_error') {
          throw new Error('Payment authentication failed. Please refresh the page and try again.');
        } else if (cardError.type === 'card_error') {
          throw new Error(`Card error: ${cardError.message}`);
        } else {
          throw new Error(cardError.message || 'Payment validation failed');
        }
      }

      console.log('✅ Card validation passed');

      // Create payment intent with retry mechanism
      console.log('🔄 Creating payment intent for course:', course.id);
      
      const apiUrl = `/api/v1/courses/${course.id}/create-payment-intent/`;
      console.log('📡 API URL:', apiUrl);
      
      const paymentData = {
        use_teocoin_discount: paymentResult?.discountInfo ? true : false,
        discount_percent: paymentResult?.discountInfo?.discount_percentage || 0,
        teocoin_discount: paymentResult?.discountInfo?.discount_amount_eur || 0,
        payment_method: 'stripe',
        final_amount: finalPrice,
        discount_info: paymentResult?.discountInfo
      };
      
      console.log('💳 Payment data:', paymentData);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify(paymentData)
      });
      
      console.log('📡 Payment intent response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Payment intent API error:', { status: response.status, text: errorText });
        throw new Error(`Payment API error (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      console.log('💳 Payment intent response:', data);

      if (data.success) {
        const { client_secret } = data;
        console.log('🔐 Client secret received');

        // Confirm payment with Stripe
        const result = await stripe.confirmCardPayment(client_secret, {
          payment_method: {
            card: cardElement,
          }
        });

        console.log('💳 Stripe confirmation result:', result);

        if (result.error) {
          console.error('❌ Stripe payment error:', result.error);
          throw new Error(result.error.message);
        } else {
          console.log('✅ Payment successful!', result.paymentIntent);
          
          // Now enroll the student after successful payment
          const enrollResponse = await fetch(`/api/v1/courses/${course.id}/enroll/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            },
            body: JSON.stringify({
              payment_method: 'stripe',
              amount: finalPrice,
              discount_applied: paymentResult?.discountInfo ? true : false,
              discount_info: paymentResult?.discountInfo,
              stripe_payment_intent: result.paymentIntent.id
            })
          });
          
          const enrollData = await enrollResponse.json();
          console.log('📨 Course enrollment response:', enrollData);
          
          if (enrollData.success) {
            console.log('✅ Course enrollment successful!');
            
            onPaymentSuccess({
              success: true,
              discountInfo: paymentResult?.discountInfo,
              enrollment: enrollData.enrollment,
              stripe_payment: result.paymentIntent
            });
          } else {
            throw new Error(enrollData.error || 'Errore durante l\'iscrizione al corso');
          }
        }
      } else {
        throw new Error(data.error || 'Errore durante la creazione del pagamento');
      }
    } catch (error) {
      console.error('💳 Payment process error:', error);
      onPaymentError(error.message);
    } finally {
      setProcessing(false);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="stripe-card-form">
      <div className="card-element-container mb-3" style={{
        border: '2px solid #007bff',
        borderRadius: '8px',
        padding: '15px',
        background: '#fff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <CardElement 
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                  color: '#aab7c4',
                },
                fontFamily: 'Arial, sans-serif',
                fontSmoothing: 'antialiased',
                padding: '12px',
              },
              invalid: {
                color: '#fa755a',
                iconColor: '#fa755a'
              }
            },
            hidePostalCode: false,
            disabled: false,
          }}
        />
      </div>
      
      <Alert variant="warning" className="mb-3">
        <small>
          <strong>🧪 Test Mode:</strong><br/>
          • Card: <code>4242 4242 4242 4242</code><br/>
          • Expiry: Any future date (e.g., 12/28)<br/>
          • CVC: Any 3 digits (e.g., 123)<br/>
          • ZIP: <strong>12345</strong> (must be 5 digits)
        </small>
      </Alert>
      
      <div className="d-grid">
        <Button 
          type="submit" 
          variant="primary" 
          size="lg"
          disabled={!stripe || processing || loading}
        >
          {processing || loading ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              Processing Payment...
            </>
          ) : (
            `💳 Pay €${finalPrice.toFixed(2)}`
          )}
        </Button>
      </div>
    </form>
  );
};

export default DBCourseCheckoutModal;
